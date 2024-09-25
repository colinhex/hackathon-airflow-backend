import asyncio
import ssl
from asyncio import gather as asyncio_gather
from typing import Iterable, AsyncGenerator, List

import certifi
from aiohttp import ClientSession, ClientError

from unibas.common.model.model_resource import WebResource, WebContent
from unibas.common.logic.logic_utility import async_partition

__SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


async def async_fetch_resource(session: ClientSession, resource: WebResource) -> WebContent:
    print(f'Outgoing Request: GET {resource.model_dump_json()}')

    try:
        async with session.get(str(resource.loc), ssl=__SSL_CONTEXT) as response:
            content: WebContent = await WebContent.result(resource, response)

            print(f'Incoming Response: {content.model_dump_json(exclude="content")}')
            return content

    except ClientError as client_error:
        raise ValueError(f'Error fetching content from {resource.model_dump_json()}:\n {client_error}')


async def async_fetch_resources(resources: Iterable[WebResource], batch_size=25) -> AsyncGenerator[List[WebContent], None]:
    async with ClientSession() as _session:
        async for batch in async_partition(resources, batch_size):
            yield await asyncio_gather(*[async_fetch_resource(_session, url) for url in batch])


def fetch_resource(resource: WebResource) -> WebContent:
    async def get_data():
        async with ClientSession() as session:
            return await async_fetch_resource(session, resource)
    return asyncio.run(get_data())


def fetch_resource_batch(resources: Iterable[WebResource], batch_size=25) -> List[WebContent]:
    async def get_resources():
        responses = []
        async for resource in async_fetch_resources(resources, batch_size):
            responses.extend(resource)
        return responses
    return asyncio.run(get_resources())
