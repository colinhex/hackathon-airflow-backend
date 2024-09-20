import asyncio
from datetime import datetime
from typing import List, Dict

from bs4 import BeautifulSoup
from toolz import concatv

from unibas.common.typing import SitemapQuery, WebResource, SitemapResource, HtmlResource
from unibas.common.web.client import fetch_resource, async_fetch_resources


def __get_resources_from_tag(root: BeautifulSoup, resource_tag: str) -> List[Dict[str, str]]:
    return [
        {
            'loc': url.find_next('loc').text,
            'lastmod': url.find_next('lastmod').text if url.find_next('lastmod') else None
        } for url in root.find_all(resource_tag)
    ]


def __get_sitemaps_from_xml_root(root: BeautifulSoup) -> List[WebResource]:
    return [SitemapResource(**data) for data in __get_resources_from_tag(root, 'sitemap')]


def __get_urls_from_xml_root(root: BeautifulSoup) -> List[WebResource]:
    return [HtmlResource(**data) for data in __get_resources_from_tag(root, 'url')]


def __get_urls_from_sitemap(root: BeautifulSoup) -> List[WebResource]:
    if __is_nested_sitemap(root):
        return __get_sitemaps_from_xml_root(root)
    else:
        return __get_urls_from_xml_root(root)


async def __get_nested_sitemaps(root: BeautifulSoup) -> List[BeautifulSoup]:
    sitemaps = []
    async for batch in async_fetch_resources(__get_urls_from_sitemap(root)):
        for xml in batch:
            sitemaps.append(BeautifulSoup(xml.content, 'lxml-xml'))
    return sitemaps


def __is_nested_sitemap(root: BeautifulSoup) -> bool:
    return bool(root.find_all('sitemap'))


def __get_sitemap(link: str) -> BeautifulSoup:
    xml = fetch_resource(SitemapResource(**{'loc': link}))
    return BeautifulSoup(xml.content, 'lxml-xml')


def __parse_sitemap(link: str) -> List[WebResource]:
    sitemap: BeautifulSoup = __get_sitemap(link)
    if __is_nested_sitemap(sitemap):
        return list(concatv(*map(__get_urls_from_sitemap, asyncio.run(__get_nested_sitemaps(sitemap)))))
    else:
        return __get_urls_from_sitemap(sitemap)


def __resource_is_downstream_from_paths(resource: WebResource, paths: List[str]) -> bool:
    return len(paths) == 0 or any(resource.loc.startswith(path) for path in paths)


def __resource_was_modified_after(resource: WebResource, mod_after: datetime | None) -> bool:
    return mod_after is None or resource.lastmod and datetime.fromisoformat(resource.lastmod) > mod_after


def __filter_for_loc_and_lastmod(resources: List[WebResource], query: SitemapQuery) -> List[WebResource]:
    filtered_resources = []

    for resource in resources:
        if not __resource_was_modified_after(resource, query.mod_after.to_datetime()):
            continue
        if not __resource_is_downstream_from_paths(resource, query.start_paths):
            continue
        filtered_resources.append(resource)

    return filtered_resources


def query_sitemap(query: SitemapQuery) -> List[WebResource]:
    urls = __parse_sitemap(query.sitemap_url)
    return __filter_for_loc_and_lastmod(urls, query)
