import unittest
from datetime import datetime

from unibas.common.model.model_charset import Charset
from unibas.common.model.model_http import HttpCode
from unibas.common.model.model_parsed import ParsedWebContentXmlSitemapResult, ParsedWebContentHtml, ParsedWebContentPdf
from unibas.common.model.model_resource import WebContent
from unibas.common.model.model_mime_type import MimeType
from unibas.common.logic.logic_parse import parse


class TestSitemapParsing(unittest.TestCase):
    def test_sitemap_parsing(self):
        content = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url>
                <loc>https://example.com/</loc>
                <lastmod>2023-01-01</lastmod>
            </url>
        </urlset>"""
        web_content = WebContent(
            loc="https://example.com/sitemap.xml",
            lastmod=datetime.now(),
            code=HttpCode.OK,
            mime_type=MimeType.TEXT_XML,
            charset=Charset.UTF_8,
            extracted_at=datetime.now(),
            content=content
        )
        parsed_content = parse(web_content)
        self.assertEqual(parsed_content.resource_type, "parsed_web_content_xml_sitemap")
        parsed_sitemap_content: ParsedWebContentXmlSitemapResult = parsed_content
        self.assertEqual(len(parsed_sitemap_content.content), 1)
        self.assertEqual(str(parsed_sitemap_content.content[0].loc), "https://example.com/")
        self.assertEqual(str(parsed_sitemap_content.content[0].lastmod), "2023-01-01 00:00:00")


class TestHtmlParsing(unittest.TestCase):
    def test_html_parsing(self):
        content = "<html><head><title>Test</title></head><body>Example HTML content</body></html>"
        web_content = WebContent(
            loc="https://example.com/sample.html",
            lastmod=datetime.now(),
            code=HttpCode.OK,
            mime_type=MimeType.TEXT_HTML,
            charset=Charset.UTF_8,
            extracted_at=datetime.now(),
            content=content
        )
        parsed_content = parse(web_content)
        self.assertEqual(parsed_content.resource_type, "parsed_web_content_html")
        parsed_html_content: ParsedWebContentHtml = parsed_content
        self.assertEqual(parsed_html_content.attributes.title, "Test")
        self.assertIn(0, parsed_html_content.content)
        self.assertEqual(parsed_html_content.content[0], "Example HTML content")


MOCK_PDF = '''%PDF-1.4
%âãÏÓ
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page
   /Parent 2 0 R
   /MediaBox [0 0 612 792]
   /Contents 4 0 R
   /Resources << /Font << /F1 5 0 R >> >>
>>
endobj
4 0 obj
<< /Length 55 >>
stream
BT /F1 24 Tf 100 700 Td (Hello, World!) Tj ET
endstream
endobj
5 0 obj
<< /Type /Font
   /Subtype /Type1
   /BaseFont /Helvetica
>>
endobj
trailer
<< /Root 1 0 R >>
%%EOF'''


class TestPdfParsing(unittest.TestCase):
    def test_pdf_parsing(self):
        content = MOCK_PDF.encode('utf-8')
        web_content = WebContent(
            loc="https://example.com/sample.pdf",
            lastmod=datetime.now(),
            code=HttpCode.OK,
            mime_type=MimeType.APPLICATION_PDF,
            charset=Charset.UTF_8,
            extracted_at=datetime.now(),
            content=content
        )
        parsed_content = parse(web_content)
        self.assertEqual(parsed_content.resource_type, "parsed_web_content_pdf")
        parsed_pdf_content: ParsedWebContentPdf = parsed_content
        self.assertIn(0, parsed_pdf_content.content)
        self.assertIn("Hello, World!", parsed_pdf_content.content[0])


if __name__ == "__main__":
    unittest.main()
