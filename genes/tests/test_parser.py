import unittest

from genes.parser import get_ordered_gene_list


class TestParser(unittest.TestCase):

    def test_get_ordered_gene_list(self):
        ref_file_path = "test.gb"
        returned = get_ordered_gene_list(ref_file_path)
        expected = ["geneA", "geneB", "geneC", "geneD"]
        self.assertEquals(returned, expected)