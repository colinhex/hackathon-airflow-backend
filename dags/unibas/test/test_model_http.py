import unittest
from unibas.common.model.model_http import HttpCode


class TestHttpCode(unittest.TestCase):

    def test_from_status_code_valid_code(self):
        self.assertEqual(HttpCode.from_status_code(200), HttpCode.OK)

    def test_from_status_code_invalid_code(self):
        with self.assertRaises(ValueError):
            HttpCode.from_status_code(999)

    def test_from_name_valid_name(self):
        self.assertEqual(HttpCode.from_name('ok'), HttpCode.OK)

    def test_from_name_invalid_name(self):
        with self.assertRaises(KeyError):
            HttpCode.from_name('invalid_name')

    def test_get_name_lowercase(self):
        self.assertEqual(HttpCode.OK.get_name(), 'ok')

    def test_is_code_group_1xx(self):
        self.assertTrue(HttpCode.CONTINUE.protocol())

    def test_is_code_group_2xx(self):
        self.assertTrue(HttpCode.OK.success())

    def test_is_code_group_3xx(self):
        self.assertTrue(HttpCode.MOVED_PERMANENTLY.redirect())

    def test_is_code_group_4xx(self):
        self.assertTrue(HttpCode.BAD_REQUEST.client_error())

    def test_is_code_group_5xx(self):
        self.assertTrue(HttpCode.INTERNAL_SERVER_ERROR.server_error())


if __name__ == '__main__':
    unittest.main()