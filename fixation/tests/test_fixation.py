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
    def setUp(self):
        self.media = Media.objects.create()
        self.instr = Instrument.objects.create()
        self.ale_exp = AleExperiment.objects.create(instrument=self.instr)
        self.freezer_box = FreezerBox.objects.create()
        self.ale = AleId.objects.create(ale_experiment=self.ale_exp, ale_id=99)

    def test_no_fixation(self):
        flask_1 = Flask.objects.create(ale_id=self.ale,
                                       media=self.media,
                                       flask_number=1)
        isolate_1 = Isolate.objects.create(flask=flask_1,
                                           isolate_number=1,
                                           is_population=False,
                                           freezer_box=self.freezer_box)
        tech_rep_1 = TechnicalReplicate.objects.create(isolate=isolate_1)
        reseq_1 = ResequencingExperiment.objects.create(tech_rep=tech_rep_1)

        flask_2 = Flask.objects.create(ale_id=self.ale,
                                       media=self.media,
                                       flask_number=2)
        isolate_2 = Isolate.objects.create(flask=flask_2,
                                           isolate_number=1,
                                           is_population=False,
                                           freezer_box=self.freezer_box)
        tech_rep_2 = TechnicalReplicate.objects.create(isolate=isolate_2)
        reseq_2 = ResequencingExperiment.objects.create(tech_rep=tech_rep_2)

        mut1 = Mutation.objects.create(mutation_type="qwe",
                                       position=1,
                                       sequence_change="asdf",
                                       gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=reseq_1,
                                        frequency=1,
                                        mutation=mut1)
        mut2 = Mutation.objects.create(mutation_type="qwe",
                                       position=2,
                                       sequence_change="asdf",
                                       gene="geneB")
        ObservedMutation.objects.create(sequencing_experiment=reseq_2,
                                        frequency=1,
                                        mutation=mut2)
        mut3 = Mutation.objects.create(mutation_type="qwe",
                                       position=2,
                                       sequence_change="hhjk",
                                       gene="geneB")
        ObservedMutation.objects.create(sequencing_experiment=reseq_2,
                                        frequency=1,
                                        mutation=mut3)

        reseq_ordered_dict = collections.OrderedDict()
        reseq_ordered_dict.update({1: reseq_1})
        reseq_ordered_dict.update({2: reseq_2})
        fixation = Fixation(reseq_ordered_dict)
        self.assertEquals(0, len(fixation.fixating_mutation_list))

    def test_fixation_single_mutation(self):
        flask_1 = Flask.objects.create(ale_id=self.ale,
                                       media=self.media,
                                       flask_number=1)
        isolate_1 = Isolate.objects.create(flask=flask_1,
                                           isolate_number=1,
                                           is_population=False,
                                           freezer_box=self.freezer_box)
        tech_rep_1 = TechnicalReplicate.objects.create(isolate=isolate_1)
        reseq_1 = ResequencingExperiment.objects.create(tech_rep=tech_rep_1)

        flask_2 = Flask.objects.create(ale_id=self.ale,
                                       media=self.media,
                                       flask_number=2)
        isolate_2 = Isolate.objects.create(flask=flask_2,
                                           isolate_number=1,
                                           is_population=False,
                                           freezer_box=self.freezer_box)
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

    def test_lost_fixation(self):
        """
        Mutation fixates, but then disappears.
        This could happen with replacement mutations that provide more fitness on same gene; we should handle
        this as a fixation in future implementations.
        """
        flask_1 = Flask.objects.create(ale_id=self.ale,
                                       media=self.media,
                                       flask_number=1)
        isolate_1 = Isolate.objects.create(flask=flask_1,
                                           isolate_number=1,
                                           is_population=False,
                                           freezer_box=self.freezer_box)
        tech_rep_1 = TechnicalReplicate.objects.create(isolate=isolate_1)
        reseq_1 = ResequencingExperiment.objects.create(tech_rep=tech_rep_1)

        flask_2 = Flask.objects.create(ale_id=self.ale,
                                       media=self.media,
                                       flask_number=2)
        isolate_2 = Isolate.objects.create(flask=flask_2,
                                           isolate_number=1,
                                           is_population=False,
                                           freezer_box=self.freezer_box)
        tech_rep_2 = TechnicalReplicate.objects.create(isolate=isolate_2)
        reseq_2 = ResequencingExperiment.objects.create(tech_rep=tech_rep_2)

        flask_3 = Flask.objects.create(ale_id=self.ale,
                                       media=self.media,
                                       flask_number=3)
        isolate_3 = Isolate.objects.create(flask=flask_3,
                                           isolate_number=1,
                                           is_population=False,
                                           freezer_box=self.freezer_box)
        tech_rep_3 = TechnicalReplicate.objects.create(isolate=isolate_3)
        reseq_3 = ResequencingExperiment.objects.create(tech_rep=tech_rep_3)

        mut1 = Mutation.objects.create(mutation_type="qwe",
                                       position=1,
                                       sequence_change="asdf",
                                       gene="geneA")
        ObservedMutation.objects.create(sequencing_experiment=reseq_1,
                                        frequency=1,
                                        mutation=mut1)

        # mut1 fixates up to reseq_2, but disappears in reseq_3
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

        mut3 = Mutation.objects.create(mutation_type="uio",
                                       position=2,
                                       sequence_change="wqer",
                                       gene="geneC")
        ObservedMutation.objects.create(sequencing_experiment=reseq_3,
                                        frequency=1,
                                        mutation=mut3)

        reseq_ordered_dict = collections.OrderedDict()
        reseq_ordered_dict.update({1: reseq_1})
        reseq_ordered_dict.update({2: reseq_2})
        reseq_ordered_dict.update({3: reseq_3})
        fixation = Fixation(reseq_ordered_dict)
        self.assertEquals(0, len(fixation.fixating_mutation_list))

    # Test for core internal Fixation logic
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