import unittest

from common.util import get_git_hash

__author__ = 'Patrick Phaneuf'


class TestUtil(unittest.TestCase):

    def test_get_hash(self):
        expected_hash_length = 40
        returned = len(get_git_hash())
        self.assertEquals(returned, expected_hash_length)
