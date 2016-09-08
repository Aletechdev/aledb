import unittest
import os

from duplications.util import Duplications

__author__ = 'Patrick Phaneuf'

class TestUtil(unittest.TestCase):

    def test_duplications_parsing(self):
        current_location = os.path.dirname(os.path.realpath(__file__))
        test_breseq_output_dir_path = str(current_location) + "/1-1-1/output/"
        duplications = Duplications(test_breseq_output_dir_path)
        expected_gene_str = "[insF1], insE1, ymdE, [ycdU]"
        duplication_found = False
        for dup_dict in duplications.dup_list:
            if dup_dict[Duplications.START_POSITION_KEY] == "1094256":
                returned_gene_str = dup_dict[Duplications.GENES_KEY]
                self.assertEquals(returned_gene_str, expected_gene_str)
                duplication_found = True
        self.assertTrue(duplication_found)