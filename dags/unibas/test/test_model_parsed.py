import unittest
from datetime import datetime

from unibas.common.model.model_charset import Charset
from unibas.common.model.model_http import HttpCode
from unibas.common.model.model_mime_type import MimeType
from unibas.common.model.model_parsed import (
    ParsedContent,
    WebContent,
    WebResource
)


class TestParsedWebContent(unittest.TestCase):

    def setUp(self):
        self.web_resource = WebResource(
            loc='http://example.com',
            lastmod=datetime.now()
        )
        self.web_content = WebContent(
            loc=self.web_resource.loc,
            lastmod=self.web_resource.lastmod,
            code=HttpCode.OK,
            mime_type=MimeType.TEXT_HTML,
            charset=Charset.UTF_8,
            content='Test content'
        )

    def test_parsed_web_content_text_chunks_initialization(self):
        parsed_content_text_chunks = ParsedContent(
            loc=self.web_content.loc,
            lastmod=self.web_content.lastmod,
            code=self.web_content.code,
            mime_type=self.web_content.mime_type,
            charset=self.web_content.charset,
            content=['chunk1', 'chunk2']
        )
        self.assertIsInstance(parsed_content_text_chunks, ParsedContent)
        self.assertEqual(parsed_content_text_chunks.content, ['chunk1', 'chunk2'])


if __name__ == '__main__':
    unittest.main()