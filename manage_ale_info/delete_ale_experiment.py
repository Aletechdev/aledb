__author__ = 'pphaneuf'


from ale.models import AleExperiment

from seq.models import Mutation


def delete_ale_experiment(ale_experiment_primary_key):

    ale_experiment_to_delete = AleExperiment.objects.get(pk=ale_experiment_primary_key)

    ale_experiment_to_delete.delete()

    _delete_all_orphaned_mutations()


def _delete_all_orphaned_mutations():

    all_mutations = Mutation.objects.all()

    for mutation in all_mutations:

        if len(mutation.observedmutation_set.all()) == 0:

            mutation.delete()
