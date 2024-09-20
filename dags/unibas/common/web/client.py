import asyncio
import json
import ssl
from asyncio import gather as asyncio_gather
from datetime import datetime
from typing import Any, Iterable, AsyncGenerator, List

import certifi
from aiohttp import ClientSession, ClientResponse, ClientError

from unibas.common.typing import WebClientResponse, WebResource, IsoTime
from unibas.common.util.misc import async_partition
from unibas.common.web.mime_types import get_content_type_format, parse_content_type

__SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
__HEADER_DATE_FORMAT = "%a, %d %b %Y %H:%M:%S %Z"


async def format_web_client_response_content(response: ClientResponse, content_type: str) -> Any:
    match get_content_type_format(content_type):
        case 'text':
            return await response.text()
        case 'json':
            return await response.json()
        case 'binary':
            return await response.read()
        case 'unknown':
            return None


async def format_web_client_response(resource: WebResource, response: ClientResponse) -> WebClientResponse:
    content_type, charset = parse_content_type(response.headers.get('Content-Type', None))
    lastmod = response.headers.get('Last-Modified', None)
    if lastmod is None:
        lastmod = resource.lastmod
    else:
        lastmod = datetime.strptime(lastmod, __HEADER_DATE_FORMAT).isoformat()

    return WebClientResponse(**{
        'loc': resource.loc,
        'code': response.status,
        'content_type': content_type,
        'charset': charset,
        'extracted_at': IsoTime(time=datetime.now().isoformat()),
        'lastmod': IsoTime(time=lastmod),
        'content_encoding': response.headers.get('Content-Encoding', None),
        'content': await format_web_client_response_content(response, content_type),
    })


async def async_fetch_resource(session: ClientSession, resource: WebResource) -> WebClientResponse:
    print('Outgoing Request: GET', resource.loc)

    try:
        async with session.get(resource.loc, ssl=__SSL_CONTEXT) as response:
            web_client_response: WebClientResponse = await format_web_client_response(resource, response)

            print(f'Incoming Response: Code {json.dumps({"code": response.status, "reason": response.reason}) }')
            return web_client_response

    except ClientError as client_error:
        raise ValueError(f'Error fetching content from {resource.loc}: {client_error}')


async def async_fetch_resources(resources: Iterable[WebResource], batch_size=25) -> AsyncGenerator[List[WebClientResponse], None]:
    async with ClientSession() as _session:
        async for batch in async_partition(resources, batch_size):
            yield await asyncio_gather(*[async_fetch_resource(_session, url) for url in batch])


def fetch_resource(resource: WebResource) -> WebClientResponse:
    async def get_data():
        async with ClientSession() as session:
            return await async_fetch_resource(session, resource)
    return asyncio.run(get_data())


def fetch_resource_batch(resources: Iterable[WebResource], batch_size=25) -> List[WebClientResponse]:
    async def get_resources():
        responses = []
        async for resource in async_fetch_resources(resources, batch_size):
            responses.extend(resource)
        return responses
    return asyncio.run(get_resources())
