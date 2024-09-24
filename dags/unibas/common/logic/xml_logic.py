from datetime import datetime

from bs4 import BeautifulSoup
from pydantic import AnyUrl
from toolz import concatv
from typing_extensions import Dict, List

from unibas.common.logic.text_logic import get_as_string
from unibas.common.model.charset_model import Charset
from unibas.common.model.resource_model import WebResource, WebContent
from unibas.common.logic.web_client import fetch_resource_batch


def get_xml_soup(xml: str, charset: Charset = Charset.UTF_8) -> BeautifulSoup:
    xml_string = get_as_string(xml, charset=charset)
    return BeautifulSoup(xml_string, 'lxml-xml')


def is_sitemap(soup: BeautifulSoup):
    return bool(soup.find('urlset') or soup.find('sitemapindex'))


def is_nested_sitemap(soup: BeautifulSoup) -> bool:
    return bool(soup.find_all('sitemap'))


def _get_sitemap_resources_from_tag(soup: BeautifulSoup, resource_tag: str) -> List[Dict[str, str]]:
    return [
        {
            'loc': url.find_next('loc').text,
            'lastmod': url.find_next('lastmod').text if url.find_next('lastmod') else None
        } for url in soup.find_all(resource_tag)
    ]


def get_web_resources_from_sitemap(soup: BeautifulSoup, filter_paths: List[AnyUrl] | None = None, modified_after: datetime | None = None) -> List[WebResource]:
    resources: List[WebResource] = [WebResource(**data) for data in _get_sitemap_resources_from_tag(soup, 'url')]
    return WebResource.filter(resources, filter_paths, modified_after)


def get_sitemap_resources_from_sitemap(soup: BeautifulSoup, filter_paths: List[AnyUrl] | None = None, modified_after: datetime | None = None) -> List[WebResource]:
    resources = [WebResource(**data) for data in _get_sitemap_resources_from_tag(soup, 'sitemap')]
    return WebResource.filter(resources, filter_paths, modified_after)


def parse_web_resources_from_sitemap(
        soup: BeautifulSoup,
        filter_paths: List[AnyUrl] | None = None,
        modified_after: datetime | None = None
) -> List[WebResource]:
    if is_nested_sitemap(soup):
        sitemaps: List[WebResource] = get_sitemap_resources_from_sitemap(soup, filter_paths, modified_after)
        resource_batch: List[WebContent] = fetch_resource_batch(sitemaps)
        return concatv(*[parse_web_resources_from_sitemap(get_xml_soup(content.content)) for content in resource_batch])
    return get_web_resources_from_sitemap(soup, filter_paths, modified_after)
