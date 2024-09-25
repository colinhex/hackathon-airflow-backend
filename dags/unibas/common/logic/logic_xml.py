from datetime import datetime

from bs4 import BeautifulSoup
from pydantic import AnyUrl
from toolz import concatv
from typing_extensions import Dict, List

from unibas.common.logic.logic_text import get_as_string
from unibas.common.model.model_charset import Charset
from unibas.common.model.model_resource import WebResource, WebContent
from unibas.common.logic.logic_web_client import fetch_resource_batch


def get_xml_soup(xml: str, charset: Charset = Charset.UTF_8) -> BeautifulSoup:
    """
    Convert an XML string into a BeautifulSoup object.

    Args:
        xml (str): The XML string to be parsed.
        charset (Charset, optional): The character set to use for decoding the XML string. Defaults to Charset.UTF_8.

    Returns:
        BeautifulSoup: A BeautifulSoup object representing the parsed XML.
    """
    xml_string = get_as_string(xml, charset=charset)
    return BeautifulSoup(xml_string, 'lxml-xml')


def is_sitemap(soup: BeautifulSoup) -> bool:
    """
    Check if the given BeautifulSoup object represents a sitemap.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object to check.

    Returns:
        bool: True if the object is a sitemap, False otherwise.
    """
    return bool(soup.find('urlset') or soup.find('sitemapindex'))


def is_nested_sitemap(soup: BeautifulSoup) -> bool:
    """
    Check if the given BeautifulSoup object represents a nested sitemap.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object to check.

    Returns:
        bool: True if the object is a nested sitemap, False otherwise.
    """
    return bool(soup.find_all('sitemap'))


def _get_sitemap_resources_from_tag(soup: BeautifulSoup, resource_tag: str) -> List[Dict[str, str]]:
    """
    Extract resources from a sitemap based on the given tag.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object representing the sitemap.
        resource_tag (str): The tag to search for in the sitemap (e.g., 'url' or 'sitemap').

    Returns:
        List[Dict[str, str]]: A list of dictionaries containing the 'loc' and 'lastmod' of each resource.
    """
    return [
        {
            'loc': url.find_next('loc').text,
            'lastmod': url.find_next('lastmod').text if url.find_next('lastmod') else None
        } for url in soup.find_all(resource_tag)
    ]


def get_web_resources_from_sitemap(soup: BeautifulSoup, filter_paths: List[AnyUrl] | None = None, modified_after: datetime | None = None) -> List[WebResource]:
    """
    Extract web resources from a sitemap.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object representing the sitemap.
        filter_paths (List[AnyUrl], optional): A list of URLs to filter the resources. Defaults to None.
        modified_after (datetime, optional): A datetime to filter resources modified after this date. Defaults to None.

    Returns:
        List[WebResource]: A list of WebResource objects extracted from the sitemap.
    """
    resources: List[WebResource] = [WebResource(**data) for data in _get_sitemap_resources_from_tag(soup, 'url')]
    return WebResource.filter(resources, filter_paths, modified_after)


def get_sitemap_resources_from_sitemap(soup: BeautifulSoup, filter_paths: List[AnyUrl] | None = None, modified_after: datetime | None = None) -> List[WebResource]:
    """
    Extract sitemap resources from a nested sitemap.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object representing the nested sitemap.
        filter_paths (List[AnyUrl], optional): A list of URLs to filter the resources. Defaults to None.
        modified_after (datetime, optional): A datetime to filter resources modified after this date. Defaults to None.

    Returns:
        List[WebResource]: A list of WebResource objects extracted from the nested sitemap.
    """
    resources = [WebResource(**data) for data in _get_sitemap_resources_from_tag(soup, 'sitemap')]
    return WebResource.filter(resources, filter_paths, modified_after)


def parse_web_resources_from_sitemap(
        soup: BeautifulSoup,
        filter_paths: List[AnyUrl] | None = None,
        modified_after: datetime | None = None
) -> List[WebResource]:
    """
    Parse web resources from a sitemap, including nested sitemaps.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object representing the sitemap.
        filter_paths (List[AnyUrl], optional): A list of URLs to filter the resources. Defaults to None.
        modified_after (datetime, optional): A datetime to filter resources modified after this date. Defaults to None.

    Returns:
        List[WebResource]: A list of WebResource objects extracted from the sitemap.
    """
    if is_nested_sitemap(soup):
        sitemaps: List[WebResource] = get_sitemap_resources_from_sitemap(soup, filter_paths, modified_after)
        resource_batch: List[WebContent] = fetch_resource_batch(sitemaps)
        return concatv(*[parse_web_resources_from_sitemap(get_xml_soup(content.content)) for content in resource_batch])
    return get_web_resources_from_sitemap(soup, filter_paths, modified_after)