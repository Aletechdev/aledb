from django.http import HttpResponse

from django.utils.safestring import mark_safe

from django.contrib.auth.decorators import login_required

from django.template import Context, loader

import seq.models

import seq.views.common

from seq.views import mutation_table_builder

import urllib.request

import json


@login_required
def gene(request):
    gene_query = request.GET['g']

    reseq_dict, observed_mutations_with_gene_queryset = _get_seq_exp(request, gene_query)

    table_header = mutation_table_builder.get_table_header(reseq_dict)

    table_body = mutation_table_builder.get_table_body(reseq_dict,
                                                       observed_mutations_with_gene_queryset,
                                                       table_type=mutation_table_builder.TableType.gene_table)

    template = loader.get_template("gene.html")

    pdb_url = _get_pdb_url(gene_query)

    context = Context({"gene_name": gene_query,
                       "table_body": mark_safe(table_body),
                       "title": gene_query + " gene",
                       "table_header": mark_safe(table_header),
                       "pdb_file_path": pdb_url})

    return HttpResponse(template.render(context))


# TODO: This is the same implementation as found within seq.views.search.py; need to consolidate.
def _get_seq_exp(request, mutated_gene):

    isolates_to_remove_id_list = []
    isolates_to_remove_string = request.GET.get(mutation_table_builder.EXPERIMENT_MAPPING_FILTERING_REMOVE_FLAG)
    if isolates_to_remove_string is not None:
        isolates_to_remove_ids = isolates_to_remove_string.encode('latin_1').replace("{", "").replace("}", "")
        isolates_to_remove_id_list = [int(i) for i in isolates_to_remove_ids.split(",") if i != ""]

    isolates_to_show_id_list = []
    isolates_to_show_string = request.GET.get(mutation_table_builder.EXPERIMENT_MAPPING_FILTERING_SHOW_FLAG)
    if isolates_to_show_string is not None:
        isolates_to_show_ids = isolates_to_show_string.encode('latin_1').replace("{", "").replace("}", "")
        isolates_to_show_id_list = [int(i) for i in isolates_to_show_ids.split(",") if i != ""]

    mutations_with_gene = seq.models.Mutation.objects.filter(gene=mutated_gene)

    observed_mutations_with_gene = seq.models.ObservedMutation.objects.filter(mutation__in=mutations_with_gene)

    seq_experiment_dict = {}

    for observed_mutation in observed_mutations_with_gene:

        if observed_mutation.sequencing_experiment.id not in isolates_to_remove_id_list\
            or observed_mutation.sequencing_experiment.id in isolates_to_remove_id_list\
                and observed_mutation.sequencing_experiment.id in isolates_to_show_id_list:

            seq_experiment_dict[observed_mutation.sequencing_experiment.id] = observed_mutation.sequencing_experiment

    return seq_experiment_dict, observed_mutations_with_gene


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

                pdb_url = 'https://files.rcsb.org/download/' + pdb_code + '.pdb'

                return pdb_url
    except:
        return ''

