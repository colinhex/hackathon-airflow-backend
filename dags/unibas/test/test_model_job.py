import unittest
from datetime import datetime
from pydantic import AnyUrl

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
from unibas.common.model.model_job import Job


class TestParsedWebContent(unittest.TestCase):

    def setUp(self):
        self.web_resource = WebResource(
            loc=AnyUrl('http://example.com'),
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

    def test_job_initialization_with_default_values(self):
        job = Job(resources=[])
        self.assertIsInstance(job, Job)
        self.assertFalse(job.processing)
        self.assertEqual(job.tries, 0)
        self.assertIsInstance(job.created_at, datetime)
        self.assertEqual(job.resources, [])

    def test_job_initialization_with_custom_values(self):
        resources = [WebResource(loc=AnyUrl('http://example.com'), lastmod=datetime.now())]
        job = Job(processing=True, tries=3, resources=resources)
        self.assertTrue(job.processing)
        self.assertEqual(job.tries, 3)
        self.assertEqual(job.resources, resources)

    def test_job_model_dump_with_default_values(self):
        job = Job(resources=[])
        dump = job.model_dump()
        self.assertIn('created_at', dump)
        self.assertIn('processing', dump)
        self.assertIn('tries', dump)
        self.assertIn('resources', dump)

    def test_job_model_dump_with_stringify_datetime(self):
        job = Job(resources=[])
        dump = job.model_dump(stringify_datetime=True)
        self.assertIsInstance(dump['created_at'], str)
        self.assertIn('T', dump['created_at'])  # Check if ISO format

    def test_job_model_dump_with_resources(self):
        resources = [WebResource(loc=AnyUrl('http://example.com'), lastmod=datetime.now())]
        job = Job(resources=resources)
        dump = job.model_dump()
        self.assertIn('resources', dump)
        self.assertEqual(len(dump['resources']), 1)
        self.assertIn('loc', dump['resources'][0])


if __name__ == '__main__':
    unittest.main()