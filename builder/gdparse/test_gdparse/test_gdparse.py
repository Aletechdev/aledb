from builder.gdparse.gdparse.gdparse import GDParser
import unittest


__author__ = 'Patrick Phaneuf'


class TestGDParser(unittest.TestCase):

    def test_del_position_522526_gene_name_is_clr(self):

        expected_mutation_name = "[crl]"
        mutation_id = 1
        gd_file_name = "annotated.gd"

        with open(gd_file_name, 'rb') as genomic_diff_file:
            gd_parser = GDParser(genomic_diff_file)
            experiment_mutation_dict = gd_parser.data['mutation']

        returned_mutation_name = experiment_mutation_dict[mutation_id]["gene_name"]

        self.assertEquals(expected_mutation_name, returned_mutation_name)


    def test_CON_mutations(self):
        with open("3-30000-1-1.gd") as gd_file:
            gd_parser = GDParser(gd_file)
        # pass if doesn't crash.