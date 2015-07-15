__author__ = 'pphaneuf'

import unittest

from seq.upload import is_sample_clonal_or_popuation
from seq.upload import Breseq_sample_type

class TestUpload(unittest.TestCase):

    def test_is_sample_clonal_or_popuation_clonal(self):

        log_file_path = "log_sample_is_clonal.txt"

        sample_type = is_sample_clonal_or_popuation(log_file_path)

        self.assertEquals(Breseq_sample_type.clonal, sample_type)

    def test_is_sample_clonal_or_popuation_population(self):

        log_file_path = "log_sample_is_population.txt"

        sample_type = is_sample_clonal_or_popuation(log_file_path)

        self.assertEquals(Breseq_sample_type.population, sample_type)