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
    experiment_mapping = dict((o.id, i) for i, o in enumerate(experiments))
    # cache the urls of the experiment location
    experiment_urls = dict((i.id, sequencing_url + i.location) for i in experiments)
    mutations = Mutation.objects.all()
    mutation_mapping = dict((mutation.id, i) for i, mutation in enumerate(mutations))
    table_header = """<tr><td>Experiment</td>"""
    for mutation in mutations:
        table_header += """<td>%d %s</td>""" % (mutation.position, mutation.sequence_change)
    table_header += "</tr>"
    table_entries = [[None] * len(mutations) for i in range(len(experiments))]
    for observed in ObservedMutation.objects.all():
        table_entries[experiment_mapping[observed.sequencing_experiment_id]][mutation_mapping[observed.mutation_id]] = \
            """<td class="true">%s</td>""" % observed.evidence.replace("evidence/", experiment_urls[observed.sequencing_experiment_id] + "/evidence/")
    table_body = ""
    for experiment in experiments:
        table_body += """<tr><td><a href="%s">%s</a></td>""" % (sequencing_url + experiment.location, experiment.get_isolate_name())
        for column in table_entries[experiment_mapping[experiment.id]]:
            if column is None:
                table_body += """<td class="false"></td>"""
            else:
                table_body += column
    template = loader.get_template("table_template.html")
    context = Context({"table_body": mark_safe(table_body), "title": "Experiment table", "table_header": mark_safe(table_header)})
    return HttpResponse(template.render(context))

def mutation_table(request):
    experiments = ResequencingExperiment.objects.all()
    experiment_mapping = dict((o.id, i) for i, o in enumerate(experiments))
    # cache the urls of the experiment location
    experiment_urls = dict((i.id, sequencing_url + i.location) for i in experiments)
    mutations = Mutation.objects.all()
    mutation_mapping = dict((mutation.id, i) for i, mutation in enumerate(mutations))
    table_header = """<tr><td>Mutation</td><td>Gene</td><td>Protein change</td>"""
    for experiment in experiments:
        table_header += """<td>%s</td>""" % (experiment.get_isolate_name().replace("_", " "))
    table_header += "</tr>"
    table_entries = [["""<td class="false"></td>"""] * len(experiments) for i in range(len(mutations))]
    
    observed_query = ObservedMutation.objects
    
    for observed in observed_query.all():
        table_entries[mutation_mapping[observed.mutation_id]][experiment_mapping[observed.sequencing_experiment_id]] = \
            """<td class="true">%s</td>""" % observed.evidence.replace("evidence/", experiment_urls[observed.sequencing_experiment_id] + "/evidence/")
    table_body = ""
    for mutation in mutations:
        table_body += "<tr><td>%d %s</td><td>%s</td><td>%s</td>%s</tr>\n" % \
            (mutation.position, mutation.sequence_change, mutation.gene, mutation.protein_change, "".join(table_entries[mutation_mapping[mutation.id]]))
    template = loader.get_template("table_template.html")
    context = Context({"table_body": mark_safe(table_body), "title": "Mutation table", "table_header": mark_safe(table_header)})
    return HttpResponse(template.render(context))
