from builder.gdparse.gdparse import gdparse
import unittest


__author__ = 'Patrick Phaneuf'


class TestGDParser(unittest.TestCase):

    def test_del_position_522526_gene_name_is_clr(self):
        expected_mutation_name = "[crl]"
        mutation_id = 1
        gd_file_name = "annotated.gd"
        with open(gd_file_name, 'rb') as genomic_diff_file:
            gd_parser = gdparse.GDParser(genomic_diff_file)
            experiment_mutation_dict = gd_parser.data['mutation']
        returned_mutation_name = experiment_mutation_dict[mutation_id]["gene_name"]
        self.assertEqual(expected_mutation_name, returned_mutation_name)

    def test_parsing_breseq_version(self):
        expected = "0.27.0b"
        with open("has_AUTHOR.gd") as annotated_gd_file:
            gd_parser = gdparse.GDParser(annotated_gd_file)
        returned_version = gd_parser.meta_data.get(gdparse.BRESEQ_VERSION_KEY)
        self.assertEqual(expected, returned_version)
        with open("has_PROGRAM.gd") as annotated_gd_file:
            gd_parser = gdparse.GDParser(annotated_gd_file)
        returned_version = gd_parser.meta_data.get(gdparse.BRESEQ_VERSION_KEY)
        self.assertEqual(expected, returned_version)
        expected = None
        with open("no_PROGRAM_or_AUTHOR.gd") as annotated_gd_file:
            gd_parser = gdparse.GDParser(annotated_gd_file)
        returned_version = gd_parser.meta_data.get(gdparse.BRESEQ_VERSION_KEY)
        self.assertEqual(expected, returned_version)
        with open("AUTHOR_name.gd") as annotated_gd_file:
            gd_parser = gdparse.GDParser(annotated_gd_file)
        returned_version = gd_parser.meta_data.get(gdparse.BRESEQ_VERSION_KEY)
        self.assertEqual(expected, returned_version)
