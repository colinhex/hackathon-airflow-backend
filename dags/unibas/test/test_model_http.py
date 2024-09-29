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
        self.assertTrue(HttpCode.protocol(HttpCode.CONTINUE.value))


    def test_is_code_group_2xx(self):
        self.assertTrue(HttpCode.success(HttpCode.OK.value))


    def test_is_code_group_3xx(self):
        self.assertTrue(HttpCode.redirect(HttpCode.MOVED_PERMANENTLY.value))


    def test_is_code_group_4xx(self):
        self.assertTrue(HttpCode.client_error(HttpCode.BAD_REQUEST.value))


    def test_is_code_group_5xx(self):
        self.assertTrue(HttpCode.server_error(HttpCode.INTERNAL_SERVER_ERROR.value))


if __name__ == '__main__':
    unittest.main()