import time
from django.http import HttpResponse
from django.utils.safestring import mark_safe
from django.template import loader
import seq.models
import seq.views.common
from seq.views import mutation_table_builder
import urllib.request
from xml.dom import minidom
import gzip
import csv
import json
import requests
from ale.utils import get_all_user_exps
from common.util import check_hidden_columns_and_filters
from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings
from logs.aledb_logger import user_extra, join_extras
import logging

logger = logging.getLogger(__name__)

if hasattr(settings, seq.views.common.SETTINGS_SEQUENCING_URL):
    aledata_url = settings.SEQUENCING_URL
    username = settings.OTHER_USERNAME
    password = settings.OTHER_PASSWORD
else:
    aledata_url = ""
    username = ""
    password = ""


def gene(request):
    logger.info("gene usage", extra = user_extra(request))

    try:
        start_time = time.clock()
        gene_query = request.GET['g']
        reseq_dict, observed_mutations_with_gene_queryset = _get_seq_exp(request, gene_query)
        table_header = mutation_table_builder.get_table_header(request.user, reseq_dict)
        table_body, protein_changes = mutation_table_builder.get_table_body(request.user, reseq_dict,
                                                                            observed_mutations_with_gene_queryset,
                                                                            table_type=mutation_table_builder.TableType.GENE_TABLE)

        pdb_url, residue_mappings, has_pdb_file = _get_pdb_info(gene_query)
        homology_data, has_homology_data = _get_homology_data(gene_query)
        hidden_columns = check_hidden_columns_and_filters(request, None)
        template = loader.get_template("gene.html")

        experiments = get_all_user_exps(request.user)
        context = {"experiments": experiments}
        context.update({"gene_name": gene_query,
                   "table_body": mark_safe(json.dumps(table_body, cls=DjangoJSONEncoder)),
                   "title": gene_query + " gene",
                   "table_header": mark_safe(table_header),
                   "pdb_url": pdb_url,
                   "residue_mappings": mark_safe(residue_mappings),
                   "protein_changes": protein_changes,
                   "pdb_id": _get_pdb_url(gene_query)[0],
                   "has_pdb_file": has_pdb_file,
                   "homology_data": mark_safe(json.dumps(homology_data)),
                   "has_homology_data": has_homology_data,
                   "hidden_columns": hidden_columns})
        logger.info("genes performance", extra=join_extras(user_extra(request), {"time taken": time.clock() - start_time}))
        return HttpResponse(template.render(context, request), content_type="text/html")
    except Exception as e:
        logger.exception("genes broke", extra = user_extra(request))
        template = loader.get_template("500.html")
        context = {'err_message': str(e)}
        return HttpResponse(template.render(context, request), content_type="text/html")


# TODO: This is the same implementation as found within seq.views.search.py; need to consolidate.
def _get_seq_exp(request, mutated_gene):

    isolates_to_remove_id_list = []
    isolates_to_remove_string = request.GET.get(mutation_table_builder.EXPERIMENT_MAPPING_FILTERING_REMOVE_FLAG)
    if isolates_to_remove_string is not None:
        isolates_to_remove_ids = isolates_to_remove_string.replace("{", "").replace("}", "")
        isolates_to_remove_id_list = [int(i) for i in isolates_to_remove_ids.split(",") if i != ""]

    isolates_to_show_id_list = []
    isolates_to_show_string = request.GET.get(mutation_table_builder.EXPERIMENT_MAPPING_FILTERING_SHOW_FLAG)
    if isolates_to_show_string is not None:
        isolates_to_show_ids = isolates_to_show_string.replace("{", "").replace("}", "")
        isolates_to_show_id_list = [int(i) for i in isolates_to_show_ids.split(",") if i != ""]

    mutations_with_gene_queryset = seq.models.Mutation.objects.filter(gene__contains=mutated_gene)

    observed_mutations_with_gene = seq.models.ObservedMutation.objects.filter(mutation__in=mutations_with_gene_queryset)

    seq_experiment_dict = {}

    for observed_mutation in observed_mutations_with_gene:

        if observed_mutation.sequencing_experiment.id not in isolates_to_remove_id_list\
            or observed_mutation.sequencing_experiment.id in isolates_to_remove_id_list\
                and observed_mutation.sequencing_experiment.id in isolates_to_show_id_list:

            seq_experiment_dict[observed_mutation.sequencing_experiment.id] = observed_mutation.sequencing_experiment

    return seq_experiment_dict, observed_mutations_with_gene


def _get_pdb_info(gene_query):
    pdb_code, has_pdb_file = _get_pdb_url(gene_query)
    pdb_url = 'https://files.rcsb.org/download/' + pdb_code + '.pdb'
    residue_mappings = _get_xml_for_pdb(pdb_code)
    return pdb_url, residue_mappings, has_pdb_file


def _get_xml_for_pdb(pdb_code):

    try:
        with urllib.request.urlopen(
                                "ftp://ftp.ebi.ac.uk/pub/databases/msd/sifts/xml/" + pdb_code + ".xml.gz") as xmlfile:
            with gzip.open(xmlfile, 'rt') as f:
                content = f.read()
                mappings = {}
                dom = minidom.parseString(content)
                for entity in dom.getElementsByTagName('entity'):
                    for segment in entity.getElementsByTagName('segment'):
                        for residue in segment.getElementsByTagName('residue'):
                            residue_number = residue.attributes['dbResNum'].value
                            cross_ref_db = residue.getElementsByTagName('crossRefDb')[0]
                            cross_ref_num = cross_ref_db.attributes['dbResNum'].value
                            cross_ref_chain = cross_ref_db.attributes['dbChainId'].value
                            key = cross_ref_num + "_" + cross_ref_chain
                            mappings[key] = residue_number

                return mappings
    except:
        return {}


def _get_pdb_url(gene_query):

    try:
        with urllib.request.urlopen("http://www.uniprot.org/uniprot/?query=gene:" + gene_query +
                                    "+AND+organism:83333+AND+reviewed:yes&sort=score&format=list") as uniprot_response:
            uniprot_id = uniprot_response.read().decode("utf-8").replace("\n", "")
            with urllib.request.urlopen("https://www.ebi.ac.uk/pdbe/api/mappings/best_structures/" + str(uniprot_id)) \
                    as pdb_id_response:
                matches = json.loads(pdb_id_response.read().decode("utf-8"))[uniprot_id]
                best = matches[0]
                pdb_code = best['pdb_id']

                return pdb_code, True
    except:
        return '', False


def _get_homology_data(gene_query):
    mapping_url = aledata_url + 'homology_models/160804-genes_to_homology_models.csv'
    response = requests.get(mapping_url, auth=(username, password))
    reader = csv.reader(response.text.splitlines())
    for row in reader:
        if row[1] == gene_query:
            homology_url = aledata_url + 'homology_models/' + row[3]
            return requests.get(homology_url, auth=(username, password)).text, True
    return '', False
