__author__ = 'pphaneuf'


from gdparse import gdparse

import unittest


class TestGDParser(unittest.TestCase):

    def test_del_position_522526_gene_name_is_clr(self):

        expected_mutation_name = "[crl]"
        mutation_id = 1
        attribute = "gene_name"
        gd_file_name = "annotated.gd"

        with open(gd_file_name, 'rb') as genomic_diff_file:
            gd_parser = gdparse.GDParser(genomic_diff_file)
            experiment_mutation_dict = gd_parser.data['mutation']

        returned_mutation_name = experiment_mutation_dict[mutation_id][attribute]

        self.assertEquals(expected_mutation_name, returned_mutation_name)