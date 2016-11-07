import unittest

from genes.util import get_annotated_gene_list
from genes.util import get_gene_list

__author__ = 'Patrick Phaneuf'


class TestUtil(unittest.TestCase):

    def test_get_gene_list_intergenic(self):
        mutation_gene_str = "asdf/qwer"
        gene_product_annotation = ""
        returned = get_annotated_gene_list(mutation_gene_str, gene_product_annotation)
        expected = ['asdf','qwer']
        self.assertEquals(returned, expected)

    def test_get_gene_list_byte_string(self):
        mutation_gene_str = b'asdf/qwer'
        gene_product_annotation = ""
        returned = get_annotated_gene_list(mutation_gene_str, gene_product_annotation)
        expected = ['asdf', 'qwer']
        self.assertEquals(returned, expected)

    def test_get_gene_list_gene_range_breseq_string(self):
        mutation_gene_annotation = "[geneA]–geneC" # Breseq gene string
        gene_product_annotation = "[geneA], geneB, geneC"
        returned = get_annotated_gene_list(mutation_gene_annotation, gene_product_annotation)
        expected = ['[geneA]', 'geneB', 'geneC']
        self.assertEquals(returned, expected)

    def test_get_annotated_gene_list_mutation_gene_annotation_is_None(self):
        mutation_gene_annotation = None
        returned = get_annotated_gene_list(mutation_gene_annotation)
        expected = []
        self.assertEquals(returned, expected)

    def test_get_gene_list_intragenic(self):
        annotated_gene_list_str = "[geneA], geneB, geneC"
        returned = get_gene_list(annotated_gene_list_str)
        expected = ["geneA", "geneB", "geneC"]
        self.assertEquals(returned, expected)