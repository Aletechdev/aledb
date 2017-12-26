import unittest

from common.util import filter_for_ale
from common.util import filter_for_ale_exp

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