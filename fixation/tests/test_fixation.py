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
from fixation import fixation
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
        fixating_mutation_list = fixation.get_ale_exp_fixated_mutation_list(reseq_ordered_dict)
        self.assertEquals(0, len(fixating_mutation_list))

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
        fixating_mutation_list = fixation.get_ale_exp_fixated_mutation_list(reseq_ordered_dict)
        self.assertEquals(1, len(fixating_mutation_list))
        expected_fixation_gene = "geneA"
        for mutation in fixating_mutation_list:
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
        fixating_mutation_list = fixation.get_ale_exp_fixated_mutation_list(reseq_ordered_dict)
        self.assertEquals(0, len(fixating_mutation_list))

    def test_multiple_fixations_same_ale(self):
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

        # mut1 starts fixating
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

        # mut1 and mut2 have fixated
        ObservedMutation.objects.create(sequencing_experiment=reseq_3,
                                        frequency=1,
                                        mutation=mut1)
        ObservedMutation.objects.create(sequencing_experiment=reseq_3,
                                        frequency=1,
                                        mutation=mut2)

        reseq_ordered_dict = collections.OrderedDict()
        reseq_ordered_dict.update({1: reseq_1})
        reseq_ordered_dict.update({2: reseq_2})
        reseq_ordered_dict.update({3: reseq_3})
        fixating_mutation_list = fixation.get_ale_exp_fixated_mutation_list(reseq_ordered_dict)
        self.assertEquals(2, len(fixating_mutation_list))
        mut1_count = 0
        mut2_count = 0
        for mutation in fixating_mutation_list:
            if mutation.gene == "geneA":
                mut1_count += 1
            if mutation.gene == "geneB":
                mut2_count += 1
        self.assertEquals(mut1_count, 1)
        self.assertEquals(mut2_count, 1)

    def test_fixation_ale_exp_filter(self):
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

        filter_settings = AleExperimentFilter.objects.create(ale_experiment=self.ale_exp, ignored_genes="geneA")

        reseq_ordered_dict = collections.OrderedDict()
        reseq_ordered_dict.update({1: reseq_1})
        reseq_ordered_dict.update({2: reseq_2})
        fixating_mutation_list = fixation.get_ale_exp_fixated_mutation_list(reseq_ordered_dict, filter_settings)
        self.assertEquals(0, len(fixating_mutation_list))


    def test_fixation_ale_exp_filter(self):
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

        GlobalFilter.objects.create(ignored_genes="geneA")

        reseq_ordered_dict = collections.OrderedDict()
        reseq_ordered_dict.update({1: reseq_1})
        reseq_ordered_dict.update({2: reseq_2})
        fixating_mutation_list = fixation.get_ale_exp_fixated_mutation_list(reseq_ordered_dict)
        self.assertEquals(0, len(fixating_mutation_list))
