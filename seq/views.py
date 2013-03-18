from django.http import HttpResponse
from django.template import Context, loader
from django.utils.safestring import mark_safe

from seq.models import *
import aleinfo.settings as settings

if hasattr(settings, "sequencing_url"):
    sequencing_url = settings.sequencing_url
else:
    sequencing_url = "http://localhost/sequencing/"

def index(request):
    # return a list of resequencing experiments
    experiments = ResequencingExperiment.objects.all()
    template = loader.get_template("experiment_view.html")
    context = Context({"experiments": experiments})
    return HttpResponse(template.render(context))


def experiment_table(request):
    experiments = ResequencingExperiment.objects.all()
    mutations = Mutation.objects.all()
    mutation_mapping = dict((mutation.id, i) for i, mutation in enumerate(mutations))
    table_header = """<tr><td>Experiment</td>"""
    for mutation in mutations:
        table_header += """<td>%d %s</td>""" % (mutation.position, mutation.sequence_change)
    table_header += "</tr>"
    columns_base = ["""<td class="false"></td>"""] * len(mutations)
    table_body = ""
    for experiment in experiments:
        columns = columns_base[:]  # copy
        for observed_mutation in experiment.observedmutation_set.all():
            mutation = observed_mutation.mutation
            columns[mutation_mapping[mutation.id]] = """<td class="true">%s</td>""" % observed_mutation.evidence.replace("evidence/", sequencing_url + experiment.location + "/evidence/")
            #from IPython import embed; embed()
        table_body += """<tr><td><a href="%s">%s</a></td>%s</tr>\n""" % (sequencing_url + experiment.location, experiment.get_isolate_name(), "".join(columns))
    template = loader.get_template("table_template.html")
    context = Context({"table_body": mark_safe(table_body), "title": "Experiment table", "table_header": mark_safe(table_header)})
    return HttpResponse(template.render(context))

def mutation_table(request):
    experiments = ResequencingExperiment.objects.all()
    experiment_mapping = dict((experiment, i) for i, experiment in enumerate(experiments))
    mutations = Mutation.objects.all()
    table_header = """<tr><td>Mutation</td><td>Gene</td><td>Protein change</td>"""
    for experiment in experiments:
        table_header += """<td>%s</td>""" % (experiment.get_isolate_name().replace("_", " "))
    table_header += "</tr>"
    columns_base = ["""<td class="false"></td>"""] * len(experiments)
    table_body = ""
    for mutation in mutations:
        columns = columns_base[:]  # copy
        for experiment in mutation.resequencingexperiment_set.all():
            columns[experiment_mapping[experiment]] = """<td class="true">true</td>"""
        table_body += "<tr><td>%d %s</td><td>%s</td><td>%s</td>%s</tr>\n" % \
            (mutation.position, mutation.sequence_change, mutation.gene, mutation.protein_change, "".join(columns))
    template = loader.get_template("table_template.html")
    context = Context({"table_body": mark_safe(table_body), "title": "Mutation table", "table_header": mark_safe(table_header)})
    return HttpResponse(template.render(context))
