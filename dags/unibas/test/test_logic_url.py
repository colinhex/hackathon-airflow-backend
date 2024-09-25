import unittest
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from pydantic import AnyUrl

from unibas.common.logic.url_logic import href_is_different_domain, get_href_netloc, get_target_scheme, \
    get_absolute_url, absolute_url_from_href, find_hrefs_in_soup, parse_absolute_urls
from unibas.common.model.parsed_model import UrlParseResult


class TestUrlLogic(unittest.TestCase):

    def test_href_is_different_domain_returns_true_for_different_domain(self):
        origin = AnyUrl('http://www.example.com')
        href_parse_result = urlparse('http://www.different.com')
        self.assertTrue(href_is_different_domain(origin, href_parse_result))

    def test_href_is_different_domain_returns_false_for_same_domain(self):
        origin = AnyUrl('http://www.example.com')
        href_parse_result = urlparse('http://www.example.com/page')
        self.assertFalse(href_is_different_domain(origin, href_parse_result))

    def test_href_is_different_domain_returns_true_for_relative_path(self):
        origin = AnyUrl('http://www.example.com')
        href_parse_result = urlparse('/page')
        self.assertFalse(href_is_different_domain(origin, href_parse_result))

    def test_get_href_netloc_returns_netloc_for_different_domain(self):
        origin = AnyUrl('http://www.example.com')
        href_parse_result = urlparse('http://www.different.com')
        self.assertEqual(get_href_netloc(origin, href_parse_result), 'www.different.com')

    def test_get_href_netloc_returns_origin_host_for_relative_path(self):
        origin = AnyUrl('http://www.example.com')
        href_parse_result = urlparse('/page')
        self.assertEqual(get_href_netloc(origin, href_parse_result), 'www.example.com')

    def test_get_target_scheme_returns_target_scheme_if_present(self):
        origin = AnyUrl('http://www.example.com')
        target = urlparse('https://www.example.com')
        self.assertEqual(get_target_scheme(origin, target), 'https')

    def test_get_target_scheme_returns_origin_scheme_if_target_scheme_not_present(self):
        origin = AnyUrl('http://www.example.com')
        target = urlparse('//www.example.com')
        self.assertEqual(get_target_scheme(origin, target), 'http')

    def test_get_target_scheme_returns_default_scheme_if_both_not_present(self):
        origin = AnyUrl('http://www.example.com')
        target = urlparse('//www.example.com')
        self.assertEqual(get_target_scheme(origin, target), 'http')

    def test_get_absolute_url_returns_correct_absolute_url_for_relative_path(self):
        origin = AnyUrl('http://www.example.com')
        href_parse_result = urlparse('/page')
        self.assertEqual(get_absolute_url(origin, href_parse_result), 'http://www.example.com/page')

    def test_get_absolute_url_returns_correct_absolute_url_for_no_scheme(self):
        origin = AnyUrl('http://www.example.com')
        href_parse_result = urlparse('//www.example.com/page')
        self.assertEqual(get_absolute_url(origin, href_parse_result), 'http://www.example.com/page')

    def test_absolute_url_from_href_returns_correct_absolute_url_for_relative_path(self):
        origin_url = AnyUrl('http://www.example.com')
        href = '/page'
        self.assertEqual(absolute_url_from_href(origin_url, href), 'http://www.example.com/page')

    def test_absolute_url_from_href_returns_correct_absolute_url_for_no_scheme(self):
        origin_url = AnyUrl('http://www.example.com')
        href = '//www.example.com/page'
        self.assertEqual(absolute_url_from_href(origin_url, href), 'http://www.example.com/page')

    def test_find_hrefs_in_soup_returns_list_of_hrefs(self):
        soup = BeautifulSoup('<body><a href="/page1">Link1</a><a href="http://www.example.com/page2">Link2</a></body>', 'html.parser')
        self.assertEqual(find_hrefs_in_soup(soup), ['/page1', 'http://www.example.com/page2'])

    def test_parse_absolute_urls_returns_correct_url_parse_result_for_relative_paths(self):
        origin = AnyUrl('http://www.example.com')
        soup = BeautifulSoup('<body><a href="/page1">Link1</a><a href="/page2">Link2</a></body>', 'html.parser')
        result = parse_absolute_urls(origin, soup)
        expected = UrlParseResult(
            origin=origin,
            urls=[(AnyUrl('http://www.example.com/page1'), 1), (AnyUrl('http://www.example.com/page2'), 1)]
        )
        self.assertEqual(result.model_dump(exclude='id'), expected.model_dump(exclude='id'))

    def test_parse_absolute_urls_returns_correct_url_parse_result_for_mixed_paths(self):
        origin = AnyUrl('http://www.example.com')
        soup = BeautifulSoup('<body><a href="/page1">Link1</a><a href="http://www.example.com/page2">Link2</a><a href="//www.different.com/page3">Link3</a></body>', 'html.parser')
        result = parse_absolute_urls(origin, soup)
        expected = UrlParseResult(
            origin=origin,
            urls=[(AnyUrl('http://www.example.com/page1'), 1), (AnyUrl('http://www.example.com/page2'), 1), (AnyUrl('http://www.different.com/page3'), 1)]
        )
        self.assertEqual(result.model_dump(exclude='id'), expected.model_dump(exclude='id'))


if __name__ == '__main__':
    unittest.main()
