import unittest

from genes.util import get_gene_list

__author__ = 'Patrick Phaneuf'


class TestUtil(unittest.TestCase):

    def test_get_gene_list_intergenic(self):
        mutation_gene_str = "asdf/qwer"
        returned = get_gene_list(mutation_gene_str)
        expected = ['asdf','qwer']
        self.assertEquals(returned, expected)

    def test_get_gene_list_intragenic(self):
        mutation_gene_str = "[asdf]"
        returned = get_gene_list(mutation_gene_str)
        expected = ['asdf']
        self.assertEquals(returned, expected)