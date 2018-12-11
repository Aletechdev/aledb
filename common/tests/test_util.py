import unittest

from seq.util import filter_for_ale, filter_for_ale_exp
from common.util import get_git_hash

__author__ = 'Patrick Phaneuf'


class TestUtil(unittest.TestCase):

    def test_get_ale_number_selector_None(self):
        ale_id = None
        expected = ""
        returned = filter_for_ale(ale_id)
        self.assertEquals(returned, expected)

    def test_get_ale_experiment_selector(self):
        ale_experiment_id = None
        expected = ""
        returned = filter_for_ale_exp(ale_experiment_id)
        self.assertEquals(returned, expected)

    def test_get_hash(self):
        expected_hash_length = 40
        returned = len(get_git_hash())
        self.assertEquals(returned,expected_hash_length)