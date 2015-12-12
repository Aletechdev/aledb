from django.http import HttpResponse

from django.utils.safestring import mark_safe

from django.contrib.auth.decorators import login_required

from django.template import Context, loader

import seq.models

import seq.views.common


@login_required
def search_form(request):

    template = loader.get_template("search_form.html")

    return HttpResponse(template.render())


@login_required
def search(request):

    if 'q' in request.GET and request.GET['q']:

        gene_query = request.GET['q']

        # message = 'You searched for: %r' % request.GET['q']

        seq_experiment_dict, observed_mutations_with_gene = _get_seq_exp(gene_query)

        table_header = seq.views.common.get_table_header(seq_experiment_dict)

        table_body = seq.views.common.get_table_body(seq_experiment_dict, observed_mutations_with_gene, request)

        template = loader.get_template("search_results.html")

        context = Context({"table_body": mark_safe(table_body),
                           "title": "Search Results",
                           "table_header": mark_safe(table_header)})

        return HttpResponse(template.render(context))

    else:

        return HttpResponse('Please submit a search term.')


def _get_seq_exp(mutated_gene):

    mutations_with_gene = seq.models.Mutation.objects.filter(gene=mutated_gene)

    observed_mutations_with_gene = seq.models.ObservedMutation.objects.filter(mutation=mutations_with_gene)

    seq_experiment_dict = {}

    for observed_mutation in observed_mutations_with_gene:

        seq_experiment_dict[observed_mutation.sequencing_experiment.id] = observed_mutation.sequencing_experiment

    return seq_experiment_dict, observed_mutations_with_gene