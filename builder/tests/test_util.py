import unittest

from builder.util import sanitize_path
from builder.util import AleName
from builder.util import parse_ale_name
from builder.util import get_ale_name

__author__ = 'Patrick Phaneuf'


class TestUtil(unittest.TestCase):

    def test_santize_path_not_previously_sanitized(self):

        path = "asdf/qwer"

        sanitized_path = sanitize_path(path)

        expected = "asdf/qwer/"

        self.assertEquals(sanitized_path, expected)

    def test_santize_path_already_sanitized(self):

        path = "asdf/qwer/"

        sanitized_path = sanitize_path(path)

        expected = "asdf/qwer/"

        self.assertEquals(sanitized_path, expected)

    def test_parse_ale_name_ale(self):

        ale_name = "1-2"

        returned_ale_value = parse_ale_name(ale_name, AleName.Ale)

        expected_ale_value = 1

        self.assertEqual(returned_ale_value, expected_ale_value)

    def test_parse_ale_name_flask(self):

        ale_name = "1-2"

        returned_ale_value = parse_ale_name(ale_name, AleName.Flask)

        expected_ale_value = 2

        self.assertEqual(returned_ale_value, expected_ale_value)

    def test_get_ale_name(self):

        returned_ale_name = get_ale_name(1, 2)

        expected_ale_name = "A1-F2"

        self.assertEqual(returned_ale_name, expected_ale_name)