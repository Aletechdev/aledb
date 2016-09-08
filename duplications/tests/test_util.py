import unittest
import os

from duplications.util import Duplications

__author__ = 'Patrick Phaneuf'

class TestUtil(unittest.TestCase):

    def test(self):
        current_location = os.path.dirname(os.path.realpath(__file__))
        test_breseq_output_dir_path = str(current_location) + "/1-1-1/output/"
        duplications = Duplications(test_breseq_output_dir_path)
        print("")