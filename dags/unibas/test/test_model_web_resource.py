import unittest
from datetime import datetime, timezone
from pydantic import AnyHttpUrl

from unibas.common.environment.variables import ModelDumpVariables
from unibas.common.model.model_resource import WebResource


class TestWebResource(unittest.TestCase):

    def test_from_iso_string_valid(self):
        resource = WebResource.from_iso_string('http://example.com', '2023-01-01T00:00:00')
        self.assertEqual(resource.loc, AnyHttpUrl('http://example.com'))
        self.assertEqual(resource.lastmod, datetime(2023, 1, 1, 0, 0))

    def test_was_modified_after_true(self):
        resource = WebResource(loc='http://example.com', lastmod=datetime(2023, 1, 1, 0, 0))
        self.assertTrue(resource.was_modified_after('2022-12-31T23:59:59'))

    def test_was_modified_after_false(self):
        resource = WebResource(loc='http://example.com', lastmod=datetime(2023, 1, 1, 0, 0))
        self.assertFalse(resource.was_modified_after('2023-01-01T00:00:01'))

    def test_was_modified_before_true(self):
        resource = WebResource(loc='http://example.com', lastmod=datetime(2023, 1, 1, 0, 0, tzinfo=timezone.utc))
        self.assertTrue(resource.was_modified_before('2023-01-01T00:00:01Z'))

    def test_was_modified_before_false(self):
        resource = WebResource(loc='https://example.com', lastmod=datetime(2023, 1, 1, 0, 0, tzinfo=timezone.utc))
        self.assertFalse(resource.was_modified_before('2022-12-31T23:59:59Z'))

    def test_is_same_host_true(self):
        resource = WebResource(loc='https://example.com', lastmod=None)
        self.assertTrue(resource.is_same_host('http://example.com/path'))

    def test_is_same_host_false(self):
        resource = WebResource(loc='https://example.com', lastmod=None)
        self.assertFalse(resource.is_same_host('http://another.com'))

    def test_is_sub_path_from_true(self):
        resource = WebResource(loc='https://example.com/path/to/resource', lastmod=None)
        self.assertTrue(resource.is_sub_path_from('/path/to'))

    def test_is_sub_path_from_false(self):
        resource = WebResource(loc='http://example.com/path/to/resource', lastmod=None)
        self.assertFalse(resource.is_sub_path_from('/another/path'))

    def test_is_sub_path_from_any_true(self):
        resource = WebResource(loc='https://example.com/path/to/resource', lastmod=None)
        self.assertTrue(resource.is_sub_path_from_any(['/path', '/another']))

    def test_is_sub_path_from_any_false(self):
        resource = WebResource(loc='https://example.com/path/to/resource', lastmod=None)
        self.assertFalse(resource.is_sub_path_from_any(['/another', '/different']))

    def test_model_dump_default(self):
        resource = WebResource(loc='https://example.com', lastmod=datetime(2023, 1, 1, 0, 0))
        dump = resource.model_dump()
        self.assertEqual(dump['loc'], 'https://example.com/')
        self.assertEqual(dump['lastmod'], datetime(2023, 1, 1, 0, 0))

    def test_model_dump_stringify_url(self):
        resource = WebResource(loc='https://example.com', lastmod=datetime(2023, 1, 1, 0, 0))
        dump = resource.model_dump(**{ModelDumpVariables.STRINGIFY_URL: True})
        self.assertEqual(dump['loc'], 'https://example.com/')

    def test_model_dump_stringify_datetime(self):
        resource = WebResource(loc='https://example.com', lastmod=datetime(2023, 1, 1, 0, 0, tzinfo=timezone.utc))
        dump = resource.model_dump(**{ModelDumpVariables.STRINGIFY_DATETIME: True})
        self.assertEqual(dump['lastmod'], '2023-01-01T00:00:00+00:00')

    def test_model_dump_no_stringify(self):
        resource = WebResource(loc='https://example.com', lastmod=datetime(2023, 1, 1, 0, 0))
        dump = resource.model_dump(
            **{ModelDumpVariables.STRINGIFY_URL: False, ModelDumpVariables.STRINGIFY_DATETIME: False})
        self.assertEqual(dump['loc'], AnyHttpUrl('https://example.com/'))
        self.assertEqual(dump['lastmod'], datetime(2023, 1, 1, 0, 0))

    def test_filter_no_filters(self):
        resources = [
            WebResource(loc='https://example.com/path1', lastmod=datetime(2023, 1, 1, 0, 0)),
            WebResource(loc='https://example.com/path2', lastmod=datetime(2023, 1, 2, 0, 0))
        ]
        filtered = WebResource.filter(resources)
        self.assertEqual(len(filtered), 2)

    def test_filter_with_path(self):
        resources = [
            WebResource(loc='https://example.com/path1', lastmod=datetime(2023, 1, 1, 0, 0)),
            WebResource(loc='https://example.com/path2', lastmod=datetime(2023, 1, 2, 0, 0))
        ]
        filtered = WebResource.filter(resources, filter_paths=['https://example.com/path1'])
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].loc, AnyHttpUrl('https://example.com/path1'))

    def test_filter_with_modified_after(self):
        resources = [
            WebResource(loc='https://example.com/path1', lastmod=datetime(2023, 1, 1, 0, 0)),
            WebResource(loc='https://example.com/path2', lastmod=datetime(2023, 1, 2, 0, 0))
        ]
        filtered = WebResource.filter(resources, modified_after=datetime(2023, 1, 1, 12, 0))
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].loc, AnyHttpUrl('https://example.com/path2'))

    def test_filter_with_path_and_modified_after(self):
        resources = [
            WebResource(loc='https://example.com/path1', lastmod=datetime(2023, 1, 1, 0, 0)),
            WebResource(loc='https://example.com/path2', lastmod=datetime(2023, 1, 2, 0, 0))
        ]
        filtered = WebResource.filter(resources, filter_paths=['/path2'], modified_after=datetime(2023, 1, 1, 12, 0))
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].loc, AnyHttpUrl('https://example.com/path2'))


if __name__ == '__main__':
    unittest.main()
