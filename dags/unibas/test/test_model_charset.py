import unittest
from unibas.common.model.model_charset import Charset


class TestCharset(unittest.TestCase):

    def test_from_name_valid_charset(self):
        self.assertEqual(Charset.from_name('utf-8'), Charset.UTF_8)

    def test_from_name_invalid_charset(self):
        with self.assertRaises(KeyError):
            Charset.from_name('invalid-charset')

    def test_default_to_charset_utf8(self):
        self.assertEqual(Charset.default_to_charset(True), Charset.UTF_8)

    def test_default_to_charset_unknown(self):
        self.assertEqual(Charset.default_to_charset(False), Charset.UNKNOWN)

    def test_from_content_type_with_charset(self):
        self.assertEqual(Charset.from_content_type('text/html; charset=utf-8'), Charset.UTF_8)

    def test_from_content_type_without_charset(self):
        self.assertEqual(Charset.from_content_type('text/html'), Charset.UNKNOWN)

    def test_from_content_type_none(self):
        self.assertEqual(Charset.from_content_type(None), Charset.UNKNOWN)

    def test_from_content_type_default_to_utf8(self):
        self.assertEqual(Charset.from_content_type(None, default_to_utf8=True), Charset.UTF_8)

    def test_get_all_charsets(self):
        expected_charsets = [
            'unknown', 'utf-8', 'utf-16', 'utf-32', 'iso-8859-1', 'iso-8859-2', 'iso-8859-3', 'iso-8859-4',
            'iso-8859-5', 'iso-8859-6', 'iso-8859-7', 'iso-8859-8', 'iso-8859-9', 'windows-1250', 'windows-1251',
            'windows-1252', 'windows-1253', 'windows-1254', 'windows-1255', 'windows-1256', 'windows-1257', 'windows-1258'
        ]
        self.assertEqual(Charset.get_all(), expected_charsets)


if __name__ == '__main__':
    unittest.main()