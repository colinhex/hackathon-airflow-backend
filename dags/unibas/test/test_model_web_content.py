import unittest
from datetime import datetime, timezone
from aiohttp import ClientResponse
from unittest.mock import AsyncMock, MagicMock
from unibas.common.model.model_resource import WebContent, WebResource, HttpCode, MimeType, Charset


class TestWebContent(unittest.IsolatedAsyncioTestCase):

    def test_web_content_initialization(self):
        resource = WebContent(
            loc='https://example.com',
            lastmod=datetime(2023, 1, 1, 0, 0),
            code=HttpCode.OK,
            mime_type=MimeType.JSON,
            charset=Charset.UTF_8,
            content='{"key": "value"}'
        )
        self.assertEqual(str(resource.loc), 'https://example.com/')
        self.assertEqual(resource.lastmod, datetime(2023, 1, 1, 0, 0))
        self.assertEqual(resource.code, HttpCode.OK)
        self.assertEqual(resource.mime_type, MimeType.JSON)
        self.assertEqual(resource.charset, Charset.UTF_8)
        self.assertEqual(resource.content, '{"key": "value"}')

    async def test_web_content_result(self):
        web_resource = WebResource(loc='https://example.com', lastmod=datetime(2023, 1, 1, 0, 0))
        client_response = MagicMock(spec=ClientResponse)
        client_response.status = 200
        client_response.headers = {'Content-Type': 'application/json', 'Last-Modified': 'Sun, 01 Jan 2023 00:00:00 GMT'}
        client_response.json = AsyncMock(return_value="{\"key\": \"value\"}")

        result = await WebContent.result(web_resource, client_response)
        self.assertEqual(str(result.loc), 'https://example.com/')
        self.assertEqual(result.lastmod, datetime(2023, 1, 1, 0, 0))
        self.assertEqual(result.code, HttpCode.OK)
        self.assertEqual(result.mime_type, MimeType.JSON)
        self.assertEqual(result.charset, Charset.UTF_8)
        self.assertEqual(result.content, "{\"key\": \"value\"}")

    async def test_web_content_result_text(self):
        web_resource = WebResource(loc='https://example.com', lastmod=datetime(2023, 1, 1, 0, 0))
        client_response = MagicMock(spec=ClientResponse)
        client_response.status = 200
        client_response.headers = {'Content-Type': 'text/plain', 'Last-Modified': 'Sun, 01 Jan 2023 00:00:00 GMT'}
        client_response.text = AsyncMock(return_value="plain text content")

        result = await WebContent.result(web_resource, client_response)
        self.assertEqual(str(result.loc), 'https://example.com/')
        self.assertEqual(result.lastmod, datetime(2023, 1, 1, 0, 0))
        self.assertEqual(result.code, HttpCode.OK)
        self.assertEqual(result.mime_type, MimeType.TEXT_PLAIN)
        self.assertEqual(result.charset, Charset.UTF_8)
        self.assertEqual(result.content, "plain text content")

    async def test_web_content_result_binary(self):
        web_resource = WebResource(loc='https://example.com', lastmod=datetime(2023, 1, 1, 0, 0))
        client_response = MagicMock(spec=ClientResponse)
        client_response.status = 200
        client_response.headers = {'Content-Type': 'application/pdf', 'Last-Modified': 'Sun, 01 Jan 2023 00:00:00 GMT'}
        client_response.read = AsyncMock(return_value=b'binary content')

        result = await WebContent.result(web_resource, client_response)
        self.assertEqual(str(result.loc), 'https://example.com/')
        self.assertEqual(result.lastmod, datetime(2023, 1, 1, 0, 0))
        self.assertEqual(result.code, HttpCode.OK)
        self.assertEqual(result.mime_type, MimeType.APPLICATION_PDF)
        self.assertEqual(result.charset, Charset.UTF_8)
        self.assertEqual(result.content, b'binary content')


if __name__ == '__main__':
    unittest.main()