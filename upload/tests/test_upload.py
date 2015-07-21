__author__ = 'pphaneuf'

import unittest

from upload.upload import is_sample_clonal_or_popuation
from upload.upload import Breseq_sample_type
from upload.upload import is_missing_coverage_type

class TestUpload(unittest.TestCase):

    def test_is_sample_clonal_or_popuation_clonal(self):

        log_file_path = "log_sample_is_clonal.txt"

        sample_type = is_sample_clonal_or_popuation(log_file_path)

        self.assertEquals(Breseq_sample_type.clonal, sample_type)

    def test_is_sample_clonal_or_popuation_population(self):

        log_file_path = "log_sample_is_population.txt"

        sample_type = is_sample_clonal_or_popuation(log_file_path)

        self.assertEquals(Breseq_sample_type.population, sample_type)

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

        is_missing_coverage = is_missing_coverage_type(evidence)

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

        is_missing_coverage = is_missing_coverage_type(evidence)

        self.assertFalse(is_missing_coverage)