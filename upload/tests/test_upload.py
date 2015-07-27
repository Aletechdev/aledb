__author__ = 'pphaneuf'

import unittest

from upload.upload import is_sample_clonal_or_popuation
from upload.upload import SAMPLE_TYPE
from upload.upload import is_missing_coverage_type

# Use access to protected members till can wrap acceptance testing
# around workflow using these functions.
from upload.upload import _parse_average_read_length
from upload.upload import _parse_read_count

class TestUpload(unittest.TestCase):

    def test_is_sample_clonal_or_popuation_clonal(self):

        log_file_path = "log_sample_is_clonal.txt"

        sample_type = is_sample_clonal_or_popuation(log_file_path)

        self.assertEquals(SAMPLE_TYPE.clonal, sample_type)

    def test_is_sample_clonal_or_popuation_population(self):

        log_file_path = "log_sample_is_population.txt"

        sample_type = is_sample_clonal_or_popuation(log_file_path)

        self.assertEquals(SAMPLE_TYPE.population, sample_type)

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