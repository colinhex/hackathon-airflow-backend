import asyncio
import ssl
from asyncio import gather as asyncio_gather
from typing import Iterable, AsyncGenerator, List, Tuple

import certifi
from aiohttp import ClientSession, ClientError

from unibas.common.logic.logic_utility import async_partition
from unibas.common.model.model_http import HttpCode
from unibas.common.model.model_resource import WebResource, WebContent, WebContentHeader

__SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
__HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


async def async_fetch_resource(session: ClientSession, resource: WebResource) -> WebContent:
    """
    Fetch a web resource asynchronously.

    Args:
        session (ClientSession): The aiohttp client session to use for the request.
        resource (WebResource): The web resource to fetch.

    Returns:
        WebContent: The fetched web content.

    Raises:
        ValueError: If there is an error fetching the content.
    """
    print(f'Outgoing Request: GET {resource.model_dump_json()}')

    try:
        async with session.get(str(resource.loc), ssl=__SSL_CONTEXT) as response:
            content: WebContent = await WebContent.result(resource, response)

            print(f'Incoming Response: {content.model_dump_json(exclude={"content"})}')
            return content

    except ClientError as client_error:
        raise ValueError(f'Error fetching content from {resource.model_dump_json()}:\n {client_error}')


async def async_fetch_resource_head(session: ClientSession, resource: WebResource) -> WebContentHeader:
    """
    Fetch a web resource asynchronously.

    Args:
        session (ClientSession): The aiohttp client session to use for the request.
        resource (WebResource): The web resource to fetch.

    Returns:
        WebContentHeader: The fetched web content header.

    Raises:
        ValueError: If there is an error fetching the content.
    """
    print(f'Outgoing Request: HEAD {resource.model_dump_json()}')

    try:
        async with session.head(str(resource.loc), ssl=__SSL_CONTEXT, headers=__HEADERS) as response:
            content: WebContentHeader = await WebContentHeader.result(resource, response)

            print(f'Incoming Response: {content.model_dump_json(exclude={"content"})}')
            return content

    except ClientError as client_error:
        raise ValueError(f'Error fetching content from {resource.model_dump_json()}:\n {client_error}')


async def async_fetch_resources(resources: Iterable[WebResource], batch_size=25) -> AsyncGenerator[List[WebContent], None]:
    """
    Fetch multiple web resources asynchronously in batches.

    Args:
        resources (Iterable[WebResource]): The web resources to fetch.
        batch_size (int, optional): The number of resources to fetch in each batch. Defaults to 25.

    Yields:
        List[WebContent]: A list of fetched web content for each batch.
    """
    async with ClientSession() as _session:
        async for batch in async_partition(resources, batch_size):
            yield await asyncio_gather(*[async_fetch_resource(_session, url) for url in batch])


async def async_fetch_resource_heads(resources: Iterable[WebResource], batch_size=25) -> AsyncGenerator[List[WebContentHeader], None]:
    """
    Fetch multiple web resources asynchronously in batches.

    Args:
        resources (Iterable[WebResource]): The web resources to fetch.
        batch_size (int, optional): The number of resources to fetch in each batch. Defaults to 25.

    Yields:
        List[WebContentHeader]: A list of fetched web content for each batch.
    """
    async with ClientSession() as _session:
        async for batch in async_partition(resources, batch_size):
            yield await asyncio_gather(*[async_fetch_resource_head(_session, url) for url in batch])


def fetch_resource(resource: WebResource) -> WebContent:
    """
    Fetch a single web resource.

    Args:
        resource (WebResource): The web resource to fetch.

    Returns:
        WebContent: The fetched web content.
    """
    if isinstance(resource, WebContent):
        return resource

    async def get_data():
        async with ClientSession() as session:
            return await async_fetch_resource(session, resource)
    return asyncio.run(get_data())


def fetch_resource_head(resource: WebResource) -> WebContentHeader:
    """
    Fetch a single web resource.

    Args:
        resource (WebResource): The web resource to fetch.

    Returns:
        WebContentHeader: The fetched web content.
    """
    async def get_data():
        async with ClientSession() as session:
            return await async_fetch_resource_head(session, resource)
    return asyncio.run(get_data())


def is_downloaded_content(resource: WebResource | WebContent) -> bool:
    return isinstance(resource, WebContent) and HttpCode.success(resource.code)


def is_downloaded_header(resource: WebResource | WebContentHeader) -> bool:
    return isinstance(resource, WebContentHeader) and HttpCode.success(resource.code)


def filter_already_fetched_content(resources: Iterable[WebResource]) -> Tuple[List[WebResource], List[WebContent]]:
    un_fetched: List[WebResource] = [rsrc for rsrc in resources if not is_downloaded_content(rsrc)]
    fetched: List[WebContent] = [rsrc for rsrc in resources if is_downloaded_content(rsrc)]
    return un_fetched, fetched


def filter_already_fetched_headers(resources: Iterable[WebResource]) -> Tuple[List[WebResource], List[WebContentHeader]]:
    un_fetched: List[WebResource] = [rsrc for rsrc in resources if not is_downloaded_header(rsrc)]
    fetched: List[WebContentHeader] = [rsrc for rsrc in resources if is_downloaded_header(rsrc)]
    return un_fetched, fetched


def fetch_resource_batch(resources: Iterable[WebResource], batch_size=25) -> List[WebContent]:
    """
    Fetch multiple web resources and handles asynchronous execution.

    Args:
        resources (Iterable[WebResource]): The web resources to fetch.
        batch_size (int, optional): The number of resources to fetch in each batch. Defaults to 25.

    Returns:
        List[WebContent]: A list of fetched web content.
    """
    async def get_resources():
        un_fetched, fetched = filter_already_fetched_content(resources)
        print(f'Already fetched: {len(fetched)}')
        for fetched_resources in fetched:
            print(f'\t- {fetched_resources.loc}')
        print(f'Fetching: {len(un_fetched)} in batches of {batch_size}')
        for idx, un_fetched_resource in enumerate(un_fetched):
            if idx % batch_size == 0:
                print(f'Batch {idx}: {"".join(["-"]*100)}')
            print(f'\t- {un_fetched_resource.loc}')
        async for resource in async_fetch_resources(un_fetched, batch_size):
            fetched.extend(resource)
        return fetched
    return asyncio.run(get_resources())


def fetch_resource_headers(resources: Iterable[WebResource], batch_size=25) -> List[WebContentHeader]:
    """
    Fetch multiple web resources and handles asynchronous execution.

    Args:
        resources (Iterable[WebResource]): The web resources to fetch.
        batch_size (int, optional): The number of resources to fetch in each batch. Defaults to 25.

    Returns:
        List[WebContentHeader]: A list of fetched web content.
    """
    async def get_resources():
        un_fetched, fetched = filter_already_fetched_headers(resources)
        print(f'Already fetched: {len(fetched)}')
        for fetched_resources in fetched:
            print(f'\t- {fetched_resources.loc}')
        print(f'Fetching: {len(un_fetched)} in batches of {batch_size}')
        for idx, un_fetched_resource in enumerate(un_fetched):
            if idx % batch_size == 0:
                print(f'Batch {idx}: {"".join(["-"]*100)}')
            print(f'\t- {un_fetched_resource.loc}')
        async for resource in async_fetch_resource_heads(un_fetched, batch_size):
            fetched.extend(resource)
        return fetched
    return asyncio.run(get_resources())