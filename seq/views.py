from django.http import HttpResponse
from django.template import Context, loader
from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import login_required

from seq.models import *
from ale.models import *
import aleinfo.settings as settings

if hasattr(settings, "sequencing_url"):
    sequencing_url = settings.sequencing_url
else:
    sequencing_url = "http://localhost/sequencing/"

def get_seq_experiments(request):
    """return a list of seq experiments for a given ALE"""
    ale_experiment_id = request.GET.get("ale_experiment_id")
    if ale_experiment_id is None or ale_experiment_id == "all":
        ale_experiment_selector = ""
    else:
        ale_experiment_selector = "AND experiment_id = %d" % int(ale_experiment_id)
    ale_no = request.GET.get("ale_no")
    if ale_no is None or ale_no == "all":
        ale_no_selector = ""
    else:
        ale_no_selector = "AND ale_no = %d" % int(ale_no)
    experiments =  ResequencingExperiment.objects.raw(
        """SELECT reseq_id AS id FROM id_mapping WHERE 
        reseq_id IS NOT NULL %s %s
        ORDER BY ale_no, flask_no, isolate_no ASC;""" % (ale_experiment_selector, ale_no_selector))
    return experiments

@login_required
def index(request):
    """display a list of ales with links to the resequencing"""
    experiments = AleExperiment.objects.all()
    template = loader.get_template("index.html")
    context = Context({"experiments": experiments, "seq_url": sequencing_url})
    return HttpResponse(template.render(context))

@login_required
def lists(request):
    """return a list of resequencing experiments"""
    experiments = get_seq_experiments(request)
    template = loader.get_template("experiment_view.html")
    context = Context({"experiments": experiments, "seq_url": sequencing_url})
    return HttpResponse(template.render(context))

def make_table_entry(observed, experiment_urls):
    if observed.breseq_present:
        return """<td class="true">%s</td>""" % observed.evidence.replace("evidence/", experiment_urls[observed.sequencing_experiment_id] + "/evidence/")
    elif observed.present is False:
        return """<td class="false">%d/%d</td>""" % (observed.mutated_reads, observed.wt_reads)

@login_required
def experiment_table(request):
    experiments = get_seq_experiments(request)
    extra_validation = False if request.GET.get("novalid") else True
    experiment_mapping = dict((o.id, i) for i, o in enumerate(experiments))
    # cache the urls of the experiment location
    experiment_urls = dict((i.id, sequencing_url + i.location) for i in experiments)
    observed_mutations = ObservedMutation.objects.filter(sequencing_experiment_id__in=experiment_mapping.keys())
    mutations = Mutation.objects.filter(pk__in=observed_mutations.values_list("mutation", flat=True))
    mutation_mapping = dict((id, i) for i, id in enumerate(mutations.values_list("id", flat=True)))
    table_entries = [[None] * len(mutation_mapping) for i in experiment_mapping]
    for observed in observed_mutations:
        # sometimes we do not want the extra validation
        if not extra_validation and not observed.breseq_present:
            continue
        table_entries[experiment_mapping[observed.sequencing_experiment_id]][mutation_mapping[observed.mutation_id]] = \
            make_table_entry(observed, experiment_urls)
    table_header = """<tr><td>Experiment</td>"""
    for mutation in mutations:
        if mutation.reference_error:
            table_header += """<td class="reference_error">%d %s</td>""" % (mutation.position, mutation.sequence_change)
        else:
            table_header += """<td>%d %s</td>""" % (mutation.position, mutation.sequence_change)
    table_header += "</tr>"
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

@login_required
def mutation_table(request):
    experiments = get_seq_experiments(request)
    
    # Get the full list of ale experiments for the lineage chosen, as well as
    # the ale number of interest

    experiment_id = request.GET.get("ale_experiment_id")
    experiment_id = None if experiment_id is None or experiment_id == "all" else int(experiment_id)
    ale_no = request.GET.get("ale_no")
    ale_no = None if ale_no is None or ale_no == "all" else int(ale_no)
    if experiment_id is not None:
        experiment = AleExperiment.objects.get(ale_id=experiment_id)
        list_of_experiments = experiment.aleid_set.only("ale_id")
    else:
        list_of_experiments = ResequencingExperiment.objects.all()

    extra_validation = False if request.GET.get("novalid") else True
    experiment_mapping = dict((o.id, i) for i, o in enumerate(experiments))
    # cache the urls of the experiment location
    experiment_urls = dict((i.id, sequencing_url + i.location) for i in experiments)
    observed_mutations = ObservedMutation.objects.filter(sequencing_experiment_id__in=experiment_mapping.keys())
    mutations = Mutation.objects.filter(pk__in=observed_mutations.values_list("mutation", flat=True))
    mutation_mapping = dict((id, i) for i, id in enumerate(mutations.values_list("id", flat=True)))
    table_header = """<tr><td>Mutation</td><td>Gene</td><td>Protein change</td>"""
    for experiment in experiments:
        table_header += """<td>%s</td>""" % (experiment.get_isolate_name().replace("_", " "))
    table_header += "</tr>"
    table_entries = [["""<td class="false"></td>"""] * len(experiment_mapping) for i in range(len(mutations))]
    
    for observed in observed_mutations:
        # sometimes we do not want the extra validation
        if not extra_validation and not observed.breseq_present:
            continue
        new_entry = make_table_entry(observed, experiment_urls)
        if new_entry is not None:
            table_entries[mutation_mapping[observed.mutation_id]][experiment_mapping[observed.sequencing_experiment_id]] = new_entry
    table_body = ""
    for mutation in mutations:
        table_row = "<tr>"
        if mutation.reference_error:
            table_row += """<td class="reference_error">%d %s</td>""" % (mutation.position, mutation.sequence_change)
        else:
            table_row += "<td>%d %s</td>" % (mutation.position, mutation.sequence_change)
        table_row += "<td>%s</td>" % (mutation.gene)
        table_row += "<td>%s</td>" % (mutation.protein_change)
        table_row += "".join(table_entries[mutation_mapping[mutation.id]])
        table_row += "</tr>"
        table_body += table_row + "\n"
    template = loader.get_template("table_template.html")
    # list_of_experiments and curr_id are added for use of the drop down list
    context = Context({"experiments": list_of_experiments,
                       "ale_no": ale_no,
                       "experiment_id": experiment_id,
                       "table_body": mark_safe(table_body),
                       "title": "Mutation table",
                       "table_header": mark_safe(table_header)})
    return HttpResponse(template.render(context))

@login_required
def isolate_list(request):
    ale_experiment_id = request.GET.get("ale_experiment_id")
    if ale_experiment_id is None:
        isolates = Isolate.objects.all()
    else:
        ale_experiment_id = int(ale_experiment_id)
        isolates =  Isolate.objects.raw(
            """SELECT isolate_id AS id FROM id_mapping WHERE 
            experiment_id=%d;""" % ale_experiment_id)
        """return a list of resequencing experiments"""
    template = loader.get_template("isolate_view.html")
    context = Context({"isolates": isolates, "seq_url": sequencing_url})
    return HttpResponse(template.render(context))
    
# Provide a table showing frequencies of each observed mutation in the lineage
def lineage_overview(request):
    experiments = get_seq_experiments(request)
    experiment_mapping = dict((o.id,i) for i,o in enumerate(experiments))
    experiment_urls = dict((i.id, sequencing_url + i.location) for i in experiments)
    observed_mutations = ObservedMutation.objects.filter(sequencing_experiment_id__in=experiment_mapping.keys())
    mutations = Mutation.objects.filter(pk__in=observed_mutations.values_list("mutation", flat=True))
    mutations_sorted = sorted(mutations, key=lambda Mutation: Mutation.observedmutation_set.count(), reverse=True)
    mutation_mapping = dict((id,i)for i,id in enumerate(mutations.values_list("id", flat=True)))
    table_header = "<tr><td>Mutation</td><td>Gene</td><td>Protein change</td><td>Observation</td>"
    #for experiment in experiments:
        #table_header += """<td>%s</td>""" % (experiment.get_isolate_name().replace("_", " "))
    table_header += "</tr>"
    table_entries = [["""<td class="false"></td>"""] * len(experiment_mapping) for i in range(len(mutations))]
    
    for observed in observed_mutations:
        new_entry = make_table_entry(observed, experiment_urls)
        if new_entry is not None:
            table_entries[mutation_mapping[observed.mutation_id]][experiment_mapping[observed.sequencing_experiment_id]] = new_entry
    table_body = ""
    for mutation in mutations_sorted:
        table_row = "<tr>"
        if mutation.reference_error:
            table_row += """<td class="reference_error">%d %s</td>""" % (mutation.position, mutation.sequence_change)
        else:
            table_row += "<td>%d %s</td>" % (mutation.position, mutation.sequence_change)
        table_row += "<td>%s</td>" % (mutation.gene)
        table_row += "<td>%s</td>" % (mutation.protein_change)
        table_row += "<td>%d/%d</td>" % (mutation.observedmutation_set.count(),len(experiment_mapping))
        #table_row += "<td>%s</td>" % 
        #table_row += "".join(table_entries[mutation_mapping[mutation.id]])
        table_row += "</tr>"
        table_body += table_row + "\n"
    template = loader.get_template("lineage.html")
    context = Context({"table_body": mark_safe(table_body), "title": "Mutation table", "table_header": mark_safe(table_header)})
    return HttpResponse(template.render(context))
