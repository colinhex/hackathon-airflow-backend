import unittest

from bs4 import BeautifulSoup

from unibas.common.logic.logic_html import (
    get_soup, parse_html_title, parse_html_author, parse_html_date,
    parse_html_description, parse_html_keywords, get_all_text_from_html_body
)


class TestHtmlLogic(unittest.TestCase):

    def html_sample(self):
        return """
        <html>
            <head>
                <title>Sample Title</title>
                <meta name="author" content="Sample Author">
                <meta name="date" content="2023-10-01">
                <meta name="description" content="Sample Description">
                <meta name="keywords" content="sample, test">
            </head>
            <body>
                <h1>Sample H1</h1>
                <p>Sample paragraph.</p>
                <a href="http://example.com">Example Link</a>
            </body>
        </html>
        """

    def html_no_meta(self):
        return """
        <html>
            <head>
                <title>Sample Title</title>
            </head>
            <body>
                <h1>Sample H1</h1>
                <p>Sample paragraph.</p>
            </body>
        </html>
        """

    def html_empty(self):
        return "<html></html>"

    def soup_sample(self):
        return get_soup(self.html_sample())

    def soup_no_meta(self):
        return get_soup(self.html_no_meta())

    def soup_empty(self):
        return get_soup(self.html_empty())

    def test_get_soup(self):
        self.assertIsInstance(self.soup_sample(), BeautifulSoup)

    def test_parse_html_title_returns_title(self):
        self.assertEqual(parse_html_title(self.soup_sample()), "Sample Title")

    def test_parse_html_title_returns_h1_if_no_title(self):
        soup_without_title = self.soup_no_meta().find('body')
        self.assertEqual(parse_html_title(soup_without_title), "Sample H1")

    def test_parse_html_title_returns_none_if_no_title_or_h1(self):
        self.assertIsNone(parse_html_title(self.soup_empty()))

    def test_parse_html_author_returns_author(self):
        self.assertEqual(parse_html_author(self.soup_sample()), "Sample Author")

    def test_parse_html_author_returns_none_if_no_author(self):
        self.assertIsNone(parse_html_author(self.soup_no_meta()))

    def test_parse_html_date_returns_date(self):
        self.assertEqual(parse_html_date(self.soup_sample()), "2023-10-01")

    def test_parse_html_date_returns_default_if_no_date(self):
        self.assertEqual(parse_html_date(self.soup_no_meta(), "default-date"), "default-date")

    def test_parse_html_description_returns_description(self):
        self.assertEqual(parse_html_description(self.soup_sample()), "Sample Description")

    def test_parse_html_description_returns_none_if_no_description(self):
        self.assertIsNone(parse_html_description(self.soup_no_meta()))

    def test_parse_html_keywords_returns_keywords(self):
        self.assertEqual(parse_html_keywords(self.soup_sample()), "sample, test")

    def test_parse_html_keywords_returns_none_if_no_keywords(self):
        self.assertIsNone(parse_html_keywords(self.soup_no_meta()))

    def test_parse_html_links_returns_links(self):
        print('Links tested in separate test module.')
        self.assertTrue(True)

    def test_get_all_text_from_html_body_returns_text(self):
        self.assertEqual(get_all_text_from_html_body(self.soup_sample()), "Sample H1\nSample paragraph.\nExample Link")

    def test_get_all_text_from_html_body_returns_empty_if_no_body(self):
        self.assertEqual(get_all_text_from_html_body(self.soup_empty()), "")