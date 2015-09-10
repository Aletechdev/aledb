import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aleinfo.settings")

from ale.models import AleExperiment


__author__ = 'pphaneuf'


ale_experiment_id = 19

print(ale_experiment_id)

# experiment = AleExperiment.objects.get(ale_id=ale_experiment_id)
#
# experiment_list = experiment.aleid_set.only("ale_id")
#
# print(experiment_list)