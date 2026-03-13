import collections
import json
import logging
import operator
import re
from functools import reduce

from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_POST

from ale.permissions import can_view_project
from ale.models import AleExperiment, AleId
from ale.utils import get_user_projects
from filter.util import filter_observed_mutations
from logs.aledb_logger import user_extra
from seq.models import ObservedMutation
from metadata.views import get_ordered_reseq_queryset, get_reseq_info_list
logger = logging.getLogger(__name__)

_HTML_TAG_RE = re.compile(r'<[^>]+>')
_GENE_SEP_RE = re.compile(r'[,|;]')
_BASE_SEARCH_URL = "https://aledb.org/search/"


def _strip_html(text):
    """Extract gene name from potentially HTML-wrapped text.

    e.g. '<i><b>168 genes</b><BR>yjgN' -> 'yjgN'
    """
    if '<BR>' in text:
        text = text.rsplit('<BR>', 1)[-1]
    return _HTML_TAG_RE.sub('', text).strip()


@csrf_exempt
@require_http_methods(["GET"])
def genes(request):
    """
    Returns a list of all unique genes from mutations in the user's projects.
    """
    try:
        user_projects = get_user_projects(request.user)
        project_ids = [proj.id for proj in user_projects]
        
        # Build the query for user's projects
        include_argument_list = [
            Q(sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__project_id__in=project_ids)
        ]
        
        # Get the filtered queryset
        mut_qryset = ObservedMutation.objects.filter(
            reduce(operator.and_, include_argument_list)
        )
        
        # Extract unique genes
        genes_list = mut_qryset.values_list(
            'mutation__gene', flat=True
        ).distinct().order_by('mutation__gene')
        
        # Split comma-separated genes, strip HTML tags, and flatten
        individual_genes = set()
        for gene_entry in genes_list:
            if gene_entry:
                clean = _strip_html(gene_entry)
                for g in _GENE_SEP_RE.split(clean):
                    g = g.strip()
                    if g:
                        individual_genes.add(g)
        
        # Convert to sorted list of dicts with URL

        genes_list = sorted(list(individual_genes))
        genes_with_urls = [
            {
                "gene": gene,
                "url": f"{_BASE_SEARCH_URL}?hidden_columns=&gene={gene}&min_freq=&max_freq=&ref_seq=&min_pos=&max_pos=&mut_type=&project=&strain="
            }
            for gene in genes_list
        ]

        return JsonResponse({"genes": genes_with_urls})

    except Exception as e:
        logger.exception("genes endpoint error", extra=user_extra(request))
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def strains(request):
    """return list of strains"""
    logger.info("list strains", extra=user_extra(request))
    try:
        ale_ids = AleId.objects.all()
        strain_sets = {obj.strain for obj in ale_ids}
        strains = sorted([strain for strain in strain_sets if strain and strain != " N/A"])

        strains_with_urls = [
            {
                "strain": strain,
                "url": f"{_BASE_SEARCH_URL}?hidden_columns=&gene=&min_freq=&max_freq=&ref_seq=&min_pos=&max_pos=&mut_type=&project=&strain={strain}"
            }
            for strain in strains
        ]
        return JsonResponse({"strains": strains_with_urls})
    except Exception as e:
        logger.exception("strains endpoint error", extra=user_extra(request))
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def gene_strain_pairs(request):
    """Returns all unique gene/strain pairs with search URLs."""
    logger.info("list gene-strain pairs", extra=user_extra(request))
    try:
        user_projects = get_user_projects(request.user)
        project_ids = [proj.id for proj in user_projects]

        pairs_qs = ObservedMutation.objects.filter(
            sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__project_id__in=project_ids
        ).values_list(
            'mutation__gene',
            'sequencing_experiment__tech_rep__isolate__flask__ale_id__strain',
        ).distinct()

        # Expand comma-separated genes, strip HTML tags, into individual pairs
        unique_pairs = set()
        for gene_entry, strain in pairs_qs:
            if not gene_entry or not strain:
                continue
            clean = _strip_html(gene_entry)
            for gene in _GENE_SEP_RE.split(clean):
                gene = gene.strip()
                if gene:
                    unique_pairs.add((gene, strain))


        pairs_with_urls = [
            {
                "gene": gene,
                "strain": strain,
                "url": f"{_BASE_SEARCH_URL}?hidden_columns=&gene={gene}&min_freq=&max_freq=&ref_seq=&min_pos=&max_pos=&mut_type=&project=&strain={strain}"
            }
            for gene, strain in sorted(unique_pairs)
        ]

        return JsonResponse({"pairs": pairs_with_urls, "count": len(pairs_with_urls)})

    except Exception as e:
        logger.exception("gene-strain-pairs endpoint error", extra=user_extra(request))
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def query_by_pair(request):
    logger.info("query by pair", extra=user_extra(request))
    try:
        data = json.loads(request.body)
        pairs = data.get("pairs", [])
        if isinstance(pairs, dict):  # allow a single object
            pairs = [pairs]

        if not pairs:
            return JsonResponse({
                "mutations": [],
                "count": 0,
                "message": "No gene/strain pairs provided"
            })

        return _run_query(
            request,
            pairs,
            q_builder=lambda p: (
                Q(sequencing_experiment__tech_rep__isolate__flask__ale_id__strain=p.get("strain", "").strip()) &
                Q(mutation__gene__icontains=p.get("gene", "").strip())
            ) if p.get("gene") and p.get("strain") else None,
            empty_msg="No gene/strain pairs provided",
            invalid_msg="No valid gene/strain pairs provided"
        )

    except json.JSONDecodeError:
        return JsonResponse({
            "mutations": [],
            "count": 0,
            "message": "Invalid JSON"
        }, status=400)
    except Exception as e:
        logger.exception("search error", extra=user_extra(request))
        return JsonResponse({
            "mutations": [],
            "count": 0,
            "message": f"Error: {e}"
        }, status=500)


@csrf_exempt
@require_POST
def query_by_strain(request):
    logger.info("query by strain", extra=user_extra(request))
    try:
        ids = _parse_ids(request, 'ids')
        return _run_query(
            request,
            ids,
            q_builder=lambda strain: Q(sequencing_experiment__tech_rep__isolate__flask__ale_id__strain=strain),
            empty_msg='No strains provided',
            invalid_msg='No valid strains provided'
        )
    except json.JSONDecodeError:
        return JsonResponse({'mutations': [], 'count': 0, 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.exception("search broke", extra=user_extra(request))
        return JsonResponse({'mutations': [], 'count': 0, 'message': f'Error: {e}'}, status=500)


@csrf_exempt
@require_POST
def query_by_gene(request):
    logger.info("query by gene", extra=user_extra(request))
    try:
        ids = _parse_ids(request, 'ids')
        return _run_query(
            request,
            ids,
            q_builder=lambda gene: Q(mutation__gene__icontains=gene),
            empty_msg='No genes provided',
            invalid_msg='No valid genes provided'
        )
    except json.JSONDecodeError:
        return JsonResponse({'mutations': [], 'count': 0, 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.exception("search broke", extra=user_extra(request))
        return JsonResponse({'mutations': [], 'count': 0, 'message': f'Error: {e}'}, status=500)


def _parse_ids(request, key):
    """Return list of IDs from request JSON body under `key`."""
    data = json.loads(request.body)
    ids = data.get('ids', [])
    return [ids] if isinstance(ids, str) else ids


def _serialize_metadata(metadata_list):
    out = []
    for m in metadata_list:
        item = {
            'ale_experiment_id':   m['ale_experiment_id'],
            'ale_experiment_name': m['ale_experiment_name'],
            'ale_project_id':      m['ale_project_id'],
            'ale_project_name':    m['ale_project_name'],
            'multiple':            m['multiple'],
        }

        flat = []
        for tup in m.get('reseq_info_list', []):
            exp = tup[0]
            flat.append({
                'location':                exp.location,
                'ale_flask_isolate_str':   exp.ale_flask_isolate_str,
                'clonal_or_population':    tup[1],
                'tech_rep_description':    tup[2],
                'media_description':       tup[3],
                'carbon_source':           tup[4],
                'nitrogen_source':         tup[5],
                'phosphorous_source':      tup[6],
                'sulfur_source':           tup[7],
                'calcium_source':          tup[8],
                'supplement':              tup[9],
                'temperature':             tup[10],
                'strain':                  tup[11],
                'knockouts':               tup[12],
                'taxonomy_id':             tup[13],
                'reseq_reference':         tup[14],
            })
        item['reseq_info_list'] = flat
        out.append(item)
    return out

def _serialize_mutations(mutations):
    out = []
    for m in mutations:
        gene = m.mutation.gene
        strain = m.sequencing_experiment.tech_rep.isolate.flask.ale_id.strain
        item = {
            'observed_mutation_id': m.id,
            'mutation_id': m.mutation_id,
            'gene': gene,
            'position': m.mutation.position,
            'mutation_type': m.mutation.mutation_type,
            'sequence_change': m.mutation.sequence_change,
            'details': m.mutation.protein_change,
            'frequency': m.frequency,
            'ref_seq': m.mutation.reseq_reference,
            'strain': strain,
            'project_id': m.sequencing_experiment.tech_rep.isolate.flask.ale_id.ale_experiment.project_id,
            'url': f"{_BASE_SEARCH_URL}?hidden_columns=&gene={gene}&min_freq=&max_freq=&ref_seq=&min_pos=&max_pos=&mut_type=&project=&strain={strain}",
        }

        exp = getattr(m, 'experiment', None)
        if isinstance(exp, dict):
            item['experiment'] = {
                'ale_experiment_id': exp.get('ale_experiment_id', m.sequencing_experiment.ale_experiment.ale_id),
                'sequencing_experiment_id': exp.get('sequencing_experiment_id', m.sequencing_experiment.id),
                'sample_name': exp.get('name'),
                'genotype': exp.get('type'),
            }
        else:
            pass

        out.append(item)
    return out


def _run_query(request, ids, q_builder, empty_msg, invalid_msg):
    """
    Generic executor for the endpoints.
    `q_builder(item:str) -> Q` builds a Q object for a single id.
    """
    if not ids:
        return JsonResponse({'mutations': [], 'count': 0, 'message': empty_msg})

    observed_mutations = []
    for item in ids:
        if not item or not item:
            continue
        q = q_builder(item)
        if q is None:
            continue

        include_argument_list = []
        _add_projects_to_query(request, include_argument_list)
        include_argument_list.append(q)

        mutations = _get_observed_mutations(include_argument_list, [])
        logger.info("Found %d mutations for %s", len(mutations), item, extra=user_extra(request))
        observed_mutations.extend(mutations)

    if not observed_mutations:
        return JsonResponse({'mutations': [], 'count': 0, 'message': invalid_msg})

    reseq_dict = collections.OrderedDict({obs_mut.sequencing_experiment.id: obs_mut.sequencing_experiment
                                            for obs_mut in observed_mutations})
    
    ale_experiment_ids = set()

    for observed_mutation in observed_mutations:
        ale_experiment_id = observed_mutation.sequencing_experiment.ale_experiment.ale_id
        logging.info("Processing mutation with ID: %s", ale_experiment_id, extra=user_extra(request))
        ale_experiment_ids.add(ale_experiment_id)
        if observed_mutation.sequencing_experiment_id in reseq_dict.keys():
            sample_name = reseq_dict[observed_mutation.sequencing_experiment_id].exp_ale_flask_isolate_str
            if observed_mutation.breseq_present or observed_mutation.gatk_present:
                sample_type = "%2f/%2f" % (float(observed_mutation.frequency), float(observed_mutation.frequency_gatk))
            observed_mutation.experiment = {
                'ale_experiment_id': observed_mutation.sequencing_experiment.ale_experiment.ale_id,
                'sequencing_experiment_id': observed_mutation.sequencing_experiment.id,
                'name': sample_name,
                'type': sample_type
            }

    metadata = []

    for ale_experiment_id in ale_experiment_ids:
        logging.info("Processing reseq experiment with ID: %s", ale_experiment_id, extra=user_extra(request))
        experiment = AleExperiment.objects.get(ale_id=ale_experiment_id)
        if experiment:
            if not can_view_project(request.user, experiment.project):
                pass
            reseq_queryset = get_ordered_reseq_queryset(ale_experiment_id, None)
            reseq_info_list = get_reseq_info_list(reseq_queryset)
            experiment_info = {
                "reseq_info_list": reseq_info_list,
                "ale_experiment_name": experiment.name,
                "ale_project_name": experiment.project.name,
                "ale_project_id": experiment.project.id,
                "multiple": False,
                "ale_experiment_id": ale_experiment_id
            }
            metadata.append(experiment_info)
    
    mutations_data = _serialize_mutations(observed_mutations)
    experiment_metadata = _serialize_metadata(metadata)

    return JsonResponse({'mutations': mutations_data, 'experiment_metadata': experiment_metadata, 'count': len(mutations_data), 'message': 'Success'})


def _add_projects_to_query(request, include_argument_list):
    project_ids = [proj.id for proj in get_user_projects(request.user)]
    include_argument_list.append(
        Q(sequencing_experiment__tech_rep__isolate__flask__ale_id__ale_experiment__project_id__in=project_ids))
    

def _get_observed_mutations(search_include_param_list, search_exclude_param_list):
    """
    :param request:
    :return: mutation_queryset and observed_mutation_queryset based on user request and user permission
    """
    obs_mut_qryset = _get_mut_qryset(search_include_param_list, search_exclude_param_list)
    observed_mutations = filter_observed_mutations(obs_mut_qryset)
    return observed_mutations

def _get_mut_qryset(include_argument_list, exclude_argument_list):
    include_argument_list = reduce(operator.and_, include_argument_list)
    if len(exclude_argument_list) > 0:
        exclude_argument_list = reduce(operator.or_, exclude_argument_list)
        mut_qryset = ObservedMutation.objects.filter(include_argument_list).exclude(exclude_argument_list)
    else:
        mut_qryset = ObservedMutation.objects.filter(include_argument_list)

    return mut_qryset

