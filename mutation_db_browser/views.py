from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from seq.models import *

from mutation_db_browser.CsvUnicodeWriter import CsvUnicodeWriter


@login_required
def mutations_db_browser(request):

    content_disposition_type_str = 'attachment'
    content_disposition_separator = ";"
    content_disposition_file_name_attribute = 'filename="ale_mutations_db.csv"'
    content_disposition_str = content_disposition_type_str\
                              + content_disposition_separator\
                              + content_disposition_file_name_attribute

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = content_disposition_str
    writer = CsvUnicodeWriter(response)

    reseq_experiments = ResequencingExperiment.objects.all()

    experiment_mapping = dict((o.id, o) for o in reseq_experiments)

    observed_mutations = ObservedMutation.objects.filter(sequencing_experiment_id__in=experiment_mapping.keys())

    for observed_mutation in observed_mutations:

        writer.writerow(_build_mutation_output_str(observed_mutation))

    return response


def _build_mutation_output_str(observed_mutation):

    ale_experiment_str = observed_mutation.sequencing_experiment.isolate.flask.ale_id.ale_experiment.name

    seq_experiment_str = observed_mutation.sequencing_experiment.get_isolate_name()

    observed_mutation_str_list = [observed_mutation.mutation.mutation_type,
                                  str(observed_mutation.mutation.position),
                                  observed_mutation.mutation.sequence_change,
                                  observed_mutation.mutation.gene]

    return [ale_experiment_str, seq_experiment_str] + observed_mutation_str_list
