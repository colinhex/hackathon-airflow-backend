import unittest
from datetime import datetime

from unibas.common.model.model_charset import Charset
from unibas.common.model.model_http import HttpCode
from unibas.common.model.model_mime_type import MimeType
from unibas.common.model.model_parsed import (
    ParsedWebContent,
    ParsedWebContentSuccess,
    ParsedWebContentTextChunks,
    ParsedWebContentFailure,
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

    def test_parsed_web_content_initialization(self):
        parsed_content = ParsedWebContent(
            loc=self.web_content.loc,
            lastmod=self.web_content.lastmod,
            code=self.web_content.code,
            mime_type=self.web_content.mime_type,
            charset=self.web_content.charset,
            content=self.web_content.content,
            success=True
        )
        self.assertIsInstance(parsed_content, ParsedWebContent)
        self.assertEqual(parsed_content.success, True)

    def test_parsed_web_content_success_initialization(self):
        parsed_content_success = ParsedWebContentSuccess(
            loc=self.web_content.loc,
            lastmod=self.web_content.lastmod,
            code=self.web_content.code,
            mime_type=self.web_content.mime_type,
            charset=self.web_content.charset,
            content=self.web_content.content
        )
        self.assertIsInstance(parsed_content_success, ParsedWebContentSuccess)
        self.assertEqual(parsed_content_success.success, True)

    def test_parsed_web_content_text_chunks_initialization(self):
        parsed_content_text_chunks = ParsedWebContentTextChunks(
            loc=self.web_content.loc,
            lastmod=self.web_content.lastmod,
            code=self.web_content.code,
            mime_type=self.web_content.mime_type,
            charset=self.web_content.charset,
            content=self.web_content.content,
            text_chunks={1: 'chunk1', 2: 'chunk2'}
        )
        self.assertIsInstance(parsed_content_text_chunks, ParsedWebContentTextChunks)
        self.assertEqual(parsed_content_text_chunks.text_chunks, {1: 'chunk1', 2: 'chunk2'})

    def test_parsed_web_content_failure_initialization(self):
        parsed_content_failure = ParsedWebContentFailure.create(
            content=self.web_content,
            reason='Test failure'
        )
        self.assertIsInstance(parsed_content_failure, ParsedWebContentFailure)
        self.assertEqual(parsed_content_failure.success, False)
        self.assertEqual(parsed_content_failure.reason, 'Test failure')

    def test_model_dump(self):
        parsed_content = ParsedWebContent(
            loc=self.web_content.loc,
            lastmod=self.web_content.lastmod,
            code=self.web_content.code,
            mime_type=self.web_content.mime_type,
            charset=self.web_content.charset,
            content=self.web_content.content,
            success=True
        )
        dump = parsed_content.model_dump()
        self.assertIn('loc', dump)
        self.assertIn('lastmod', dump)
        self.assertIn('code', dump)
        self.assertIn('mime_type', dump)
        self.assertIn('charset', dump)
        self.assertIn('content', dump)
        self.assertIn('success', dump)


if __name__ == '__main__':
    unittest.main()