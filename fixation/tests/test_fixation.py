from django.test import TestCase
from seq.models import Mutation
from seq.models import ObservedMutation
from seq.models import ResequencingExperiment
from ale.models import AleId
from filter.models import AleExperimentFilter
from filter.models import GlobalFilter
from ale.models import AleExperiment
from ale.models import Instrument
from ale.models import Isolate
from ale.models import TechnicalReplicate
from ale.models import Flask
from ale.models import Media
from ale.models import FreezerBox
from fixation.util import Fixation
import collections


__author__ = 'Patrick Phaneuf'

class TestFixation(TestCase):

    def test_Fixation(self):
        # Need to build an ordered_reseq_dict
        # only considering one ALE
        media = Media.objects.create()
        instr = Instrument.objects.create()
        ale_exp = AleExperiment.objects.create(instrument=instr)
        freezer_box = FreezerBox.objects.create()
        ale = AleId.objects.create(ale_experiment=ale_exp, ale_id=99)

        # make a separate tech_rep, isolate and flask for each reseq.
        flask_1 = Flask.objects.create(ale_id=ale,
                                       media=media,
                                       flask_number=1)
        isolate_1 = Isolate.objects.create(flask=flask_1,
                                           isolate_number=1,
                                           is_population=False,
                                           freezer_box=freezer_box)
        tech_rep_1 = TechnicalReplicate.objects.create(isolate=isolate_1)
        reseq_1 = ResequencingExperiment.objects.create(tech_rep=tech_rep_1)

        flask_2 = Flask.objects.create(ale_id=ale,
                                       media=media,
                                       flask_number=2)
        isolate_2 = Isolate.objects.create(flask=flask_2,
                                           isolate_number=1,
                                           is_population=False,
                                           freezer_box=freezer_box)
        tech_rep_2 = TechnicalReplicate.objects.create(isolate=isolate_2)
        reseq_2 = ResequencingExperiment.objects.create(tech_rep=tech_rep_2)

        mut1 = Mutation.objects.create(mutation_type="qwe",
                                       position=1,
                                       sequence_change="asdf",
                                       gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=reseq_1,
                                        frequency=1,
                                        mutation=mut1)

        ObservedMutation.objects.create(sequencing_experiment=reseq_2,
                                        frequency=1,
                                        mutation=mut1)
        mut2 = Mutation.objects.create(mutation_type="qwe",
                                       position=2,
                                       sequence_change="asdf",
                                       gene="geneB")
        ObservedMutation.objects.create(sequencing_experiment=reseq_2,
                                        frequency=1,
                                        mutation=mut2)

        reseq_ordered_dict = collections.OrderedDict()
        reseq_ordered_dict.update({1: reseq_1})
        reseq_ordered_dict.update({2: reseq_2})
        fixation = Fixation(reseq_ordered_dict)
        self.assertEquals(1, len(fixation.fixating_mutation_list))
        expected_fixation_gene = "geneA"
        for mutation in fixation.fixating_mutation_list:
            self.assertEquals(expected_fixation_gene, mutation.gene)



    def test_get_ale_fixated_mutation_queryset(self):

        # flask_mutation_dict: {flask_id: mutation_query_set}
        mut1 = Mutation.objects.create(mutation_type="qwe",
                                      position=1,
                                      sequence_change="asdf",
                                      gene="geneA")

        mut2 = Mutation.objects.create(mutation_type="qwe",
                                      position=2,
                                      sequence_change="asdf",
                                      gene="geneB")

        flask_mutation_dict = {1:{mut1}, 2:{mut1, mut1}}

        fixated_mutation_queryset = Fixation._get_ale_fixated_mutation_queryset(flask_mutation_dict)
        expected_fixation_gene = "geneA"
        self.assertEquals(len(fixated_mutation_queryset), 1)
        for mutation in fixated_mutation_queryset:
            self.assertEquals(expected_fixation_gene, mutation.gene)