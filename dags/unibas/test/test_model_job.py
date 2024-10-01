import unittest
from datetime import datetime
from pydantic import AnyUrl

from unibas.common.model.model_charset import Charset
from unibas.common.model.model_http import HttpCode
from unibas.common.model.model_mime_type import MimeType
from unibas.common.model.model_parsed import (
    ParsedContent,
    ParsedHtml,
    ParsedPdf,
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

    def test_job_initialization_with_default_values(self):
        job = Job(created_by="test", resources=[])
        self.assertIsInstance(job, Job)
        self.assertFalse(job.processing)
        self.assertEqual(job.tries, 0)
        self.assertIsInstance(job.created_at, datetime)
        self.assertEqual(job.resources, [])

    def test_job_initialization_with_custom_values(self):
        resources = [WebResource(loc=AnyUrl('http://example.com'), lastmod=datetime.now())]
        job = Job(created_by="test", processing=True, tries=3, resources=resources)
        self.assertTrue(job.processing)
        self.assertEqual(job.tries, 3)
        self.assertEqual(job.resources, resources)

    def test_job_model_dump_with_default_values(self):
        job = Job(created_by="test", resources=[])
        dump = job.model_dump()
        self.assertIn('created_at', dump)
        self.assertIn('processing', dump)
        self.assertIn('tries', dump)
        self.assertIn('resources', dump)

    def test_job_model_dump_with_resources(self):
        resources = [WebResource(loc=AnyUrl('http://example.com'), lastmod=datetime.now())]
        job = Job(created_by="test", resources=resources)
        dump = job.model_dump()
        self.assertIn('resources', dump)
        self.assertEqual(len(dump['resources']), 1)
        self.assertIn('loc', dump['resources'][0])


if __name__ == '__main__':
    unittest.main()