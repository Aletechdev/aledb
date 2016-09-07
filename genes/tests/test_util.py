import unittest

from genes.util import get_gene_list
from genes.util import get_clean_gene_list

__author__ = 'Patrick Phaneuf'


class TestUtil(unittest.TestCase):

    def test_get_gene_list_intergenic(self):
        mutation_gene_str = "asdf/qwer"
        ref_gene_list = []
        returned = get_gene_list(mutation_gene_str, ref_gene_list)
        expected = ['asdf','qwer']
        self.assertEquals(returned, expected)

    def test_get_gene_list_byte_string(self):
        mutation_gene_str = b'asdf/qwer'
        ref_gene_list = []
        returned = get_gene_list(mutation_gene_str, ref_gene_list)
        expected = ['asdf', 'qwer']
        self.assertEquals(returned, expected)

    # def test_get_gene_list_gene_list(self):
    #     gene_list = ["asdf", "qwer"]
    #     ref_gene_list = ['geneA', 'geneB', 'geneC']
    #     returned = get_gene_list(gene_list, ref_gene_list)
    #     expected = ["asdf", "qwer"]
    #     self.assertEquals(returned, expected)

    def test_get_gene_list_intragenic(self):
        gene_list = ["[asdf]", "qwer"]
        returned = get_clean_gene_list(gene_list)
        expected = ["asdf", "qwer"]
        self.assertEquals(returned, expected)

    def test_get_gene_list_gene_range(self):
        mutation_gene_str = "[geneA]–geneC"
        ref_gene_list = ['geneA', 'geneB', 'geneC']
        returned = get_gene_list(mutation_gene_str, ref_gene_list)
        expected = ['[geneA]', 'geneB', 'geneC']
        self.assertEquals(returned, expected)