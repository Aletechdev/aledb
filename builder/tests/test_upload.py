import os
from django.test import TestCase
from seq.models import Mutation
from builder.upload import _is_missing_coverage_type
from builder.upload import _parse_average_read_length
from builder.upload import _parse_read_count
from builder.upload import _get_mutation_freq
from builder.upload import add_breseq_results
from builder.gdparse.gdparse.gdparse import GDParser


__author__ = 'Patrick Phaneuf'


class TestUpload(TestCase):

    def setUp(self):
        self.current_location = os.path.dirname(os.path.realpath(__file__))

    def test_add_breseq_results_render_html_protein_change_to_text(self):
        breseq_output_dir_path = self.current_location + "/0-0-1-1/output/"
        with open(breseq_output_dir_path + "annotated.gd") as output_genomic_diff_file:
            mutation_gd_parser = GDParser(file_handle=output_genomic_diff_file)
        add_breseq_results(1,
                           "Patrick",
                           breseq_output_dir_path,
                           mutation_gd_parser,
                           None,
                           "NC_000913_3")
        mut = Mutation.objects.get(position = 2173363)
        expected_annotation = "intergenic (‑1/+1)"
        self.assertEqual(expected_annotation, mut.protein_change)

    def test_add_breseq_results_no_mut_annotation_dict(self):
        breseq_output_dir_path = self.current_location+"/0-0-1-1/output/"
        with open(breseq_output_dir_path+"annotated.gd") as output_genomic_diff_file:
            mutation_gd_parser = GDParser(file_handle=output_genomic_diff_file)
        add_breseq_results(1,
                           "Patrick",
                           breseq_output_dir_path,
                           mutation_gd_parser,
                           None,
                           "NC_000913_3")
        mut_qryset = Mutation.objects.all()
        mut_pos_list = [mut.position for mut in mut_qryset]
        self.assertEqual(len(mut_qryset), 4)
        self.assertTrue(257908 in mut_pos_list)
        self.assertTrue(2173363 in mut_pos_list)
        self.assertTrue(3560455 in mut_pos_list)
        self.assertTrue(4296381 in mut_pos_list)

    # TODO: change unit test to get use annotated.gd rather than output.gd.
    def test_add_breseq_results_gd_file_only(self):
        breseq_output_dir_path = self.current_location + "/1-0-1-1/output/"
        with open(breseq_output_dir_path + "output.gd") as output_genomic_diff_file:
            mutation_gd_parser = GDParser(file_handle=output_genomic_diff_file)

        add_breseq_results(1,
                           "Patrick",
                           breseq_output_dir_path,
                           mutation_gd_parser,
                           None,
                           "NC_000913_3")
        mut_qryset = Mutation.objects.all()
        mut_pos_list = [mut.position for mut in mut_qryset]
        self.assertEqual(len(mut_qryset), 4)
        self.assertTrue(257908 in mut_pos_list)
        self.assertTrue(2173363 in mut_pos_list)
        self.assertTrue(3560455 in mut_pos_list)
        self.assertTrue(4296381 in mut_pos_list)

    # TODO: change unit test to get use annotated.gd rather than output.gd.
    def test_add_breseq_results_ltee_gd_file(self):
        breseq_output_dir_path = self.current_location + "/2-0-1-1/output/"
        with open(breseq_output_dir_path + "output.gd") as output_genomic_diff_file:
            mutation_gd_parser = GDParser(file_handle=output_genomic_diff_file)

        add_breseq_results(1,
                           "Patrick",
                           breseq_output_dir_path,
                           mutation_gd_parser,
                           None,
                           "NC_000913_3")

        mut_qryset = Mutation.objects.all()
        mut_pos_list = [mut.position for mut in mut_qryset]
        self.assertEqual(len(mut_qryset), 4)
        self.assertTrue(880542 in mut_pos_list)
        self.assertTrue(1733559 in mut_pos_list)
        self.assertTrue(2103918 in mut_pos_list)
        self.assertTrue(4141016 in mut_pos_list)

    def test_get_mutation_freq_89(self):

        mutation_dict = {'seq_id': 'NC_000913',
                         'parent_ids': [71],
                         'frequency': 0.89,
                         'position': 231861,
                         'new_seq': 'T',
                         'type': 'SNP'}
        
        expected_freq = 0.89

        output_freq = _get_mutation_freq(mutation_dict)

        self.assertEquals(expected_freq, output_freq)

    def test_get_mutation_freq_missing(self):

        mutation_dict = {'seq_id': 'NC_000913',
                         'parent_ids': [71],
                         'position': 231861,
                         'new_seq': 'T',
                         'type': 'SNP'}

        expected_freq = 1

        output_freq = _get_mutation_freq(mutation_dict)

        self.assertEquals(expected_freq, output_freq)

    def test_is_missing_coverage_type_True(self):

        evidence = {'end_range': 330,
                    'left_inside_cov': 184,
                    'end': 3422590,
                    'left_outside_cov': 193,
                    'seq_id': 'NC_000913',
                    'right_inside_cov': 188,
                    'right_outside_cov': 192,
                    'start': 3421757,
                    'start_range': 499,
                    'type': 'MC'}

        is_missing_coverage = _is_missing_coverage_type(evidence)

        self.assertTrue(is_missing_coverage)

    def test_is_missing_coverage_type_False(self):

        evidence = {'end_range': 330,
                    'left_inside_cov': 184,
                    'end': 3422590,
                    'left_outside_cov': 193,
                    'seq_id': 'NC_000913',
                    'right_inside_cov': 188,
                    'right_outside_cov': 192,
                    'start': 3421757,
                    'start_range': 499,
                    'type': 'RA'}

        is_missing_coverage = _is_missing_coverage_type(evidence)

        self.assertFalse(is_missing_coverage)

    def test_parse_average_read_length(self):

        input = u'164.0 bases'

        expected = u'164.0'

        output = _parse_average_read_length(input)

        self.assertEquals(output, expected)

    def test_parse_read_count(self):

        input = u'11,956,043'

        expected = 11956043

        output = _parse_read_count(input)

        self.assertEquals(output, expected)
