import unittest
import unittest.mock

from unibas.common.logic.logic_xml import (
    get_xml_soup, is_sitemap, is_nested_sitemap,
    get_web_resources_from_sitemap, parse_web_resources_from_sitemap
)


class TestXmlLogic(unittest.TestCase):

    def valid_sitemap_xml(self):
        return '''<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url>
                <loc>http://www.example.com/</loc>
                <lastmod>2023-01-01</lastmod>
            </url>
        </urlset>'''

    def nested_sitemap_xml(self):
        return '''<?xml version="1.0" encoding="UTF-8"?>
        <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <sitemap>
                <loc>http://www.example.com/sitemap1.xml</loc>
            </sitemap>
        </sitemapindex>'''

    def empty_sitemap_xml(self):
        return '''<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>'''

    def invalid_sitemap_xml(self):
        return '''<html><body>This is not a sitemap</body></html>'''

    def valid_sitemap_soup(self):
        return get_xml_soup(self.valid_sitemap_xml())

    def nested_sitemap_soup(self):
        return get_xml_soup(self.nested_sitemap_xml())

    def empty_sitemap_soup(self):
        return get_xml_soup(self.empty_sitemap_xml())

    def invalid_sitemap_soup(self):
        return get_xml_soup(self.invalid_sitemap_xml())

    def test_is_sitemap_returns_true_for_valid_sitemap(self):
        self.assertTrue(is_sitemap(self.valid_sitemap_soup()))

    def test_is_sitemap_returns_false_for_invalid_sitemap(self):
        self.assertFalse(is_sitemap(self.invalid_sitemap_soup()))

    def test_is_nested_sitemap_returns_true_for_nested_sitemap(self):
        self.assertTrue(is_nested_sitemap(self.nested_sitemap_soup()))

    def test_is_nested_sitemap_returns_false_for_non_nested_sitemap(self):
        self.assertFalse(is_nested_sitemap(self.valid_sitemap_soup()))

    def test_get_web_resources_from_sitemap_returns_resources(self):
        resources = get_web_resources_from_sitemap(self.valid_sitemap_soup())
        self.assertEqual(len(resources), 1)
        self.assertEqual(str(resources[0].loc), 'http://www.example.com/')

    def test_get_web_resources_from_sitemap_returns_empty_for_empty_sitemap(self):
        resources = get_web_resources_from_sitemap(self.empty_sitemap_soup())
        self.assertEqual(len(resources), 0)

    def parse_web_resources_from_sitemap_returns_empty_for_invalid_sitemap(self):
        with unittest.mock.patch('unibas.common.logic.web_client.fetch_resource_batch', return_value=[]):
            resources = parse_web_resources_from_sitemap(self.invalid_sitemap_soup())
            self.assertEqual(len(resources), 0)


if __name__ == '__main__':
    unittest.main()