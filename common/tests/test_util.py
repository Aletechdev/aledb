import unittest

from common.util import get_ale_number_selector
from common.util import get_ale_experiment_selector

__author__ = 'Patrick Phaneuf'


class TestUtil(unittest.TestCase):

    def test_get_ale_number_selector_None(self):
        ale_id = None
        expected = ""
        returned = get_ale_number_selector(ale_id)
        self.assertEquals(returned, expected)

    def test_get_ale_experiment_selector(self):
        ale_experiment_id = None
        expected = ""
        returned = get_ale_experiment_selector(ale_experiment_id)
        self.assertEquals(returned, expected)