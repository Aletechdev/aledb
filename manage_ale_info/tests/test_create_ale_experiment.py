__author__ = 'pphaneuf'


import unittest

from manage_ale_info.ale_experiment import _sanitize_path


class TestUpload(unittest.TestCase):

    def test_santize_path_not_previously_sanitized(self):

        path = "asdf/qwer"

        sanitized_path = _sanitize_path(path)

        expected = "asdf/qwer/"

        self.assertEquals(sanitized_path, expected)

    def test_santize_path_already_sanitized(self):

        path = "asdf/qwer/"

        sanitized_path = _sanitize_path(path)

        expected = "asdf/qwer/"

        self.assertEquals(sanitized_path, expected)
