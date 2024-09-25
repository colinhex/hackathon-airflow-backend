from typing import Callable, Dict, List, Tuple
from urllib.parse import ParseResult, urlparse

from bs4 import BeautifulSoup
from pydantic import AnyUrl
from toolz import pipe, frequencies

from unibas.common.model.model_parsed import UrlParseResult

__DEFAULT_URI_SCHEME = 'https'


def href_is_different_domain(origin: AnyUrl, href_parse_result: ParseResult):
    """
    Check if the href belongs to a different domain than the origin.

    Args:
        origin (AnyUrl): The origin URL.
        href_parse_result (ParseResult): The parsed result of the href.

    Returns:
        bool: True if the href belongs to a different domain, False otherwise.
    """
    return href_parse_result.netloc is not None \
        and href_parse_result.netloc != '' \
        and href_parse_result.netloc != origin.host


def get_href_netloc(origin: AnyUrl, href_parse_result: ParseResult) -> str:
    """
    Get the network location (netloc) of the href.

    Args:
        origin (AnyUrl): The origin URL.
        href_parse_result (ParseResult): The parsed result of the href.

    Returns:
        str: The netloc of the href.
    """
    if href_is_different_domain(origin, href_parse_result):
        return href_parse_result.netloc
    else:
        return origin.host


def get_target_scheme(origin: AnyUrl, target: ParseResult) -> str:
    """
    Get the scheme of the target URL.

    Args:
        origin (AnyUrl): The origin URL.
        target (ParseResult): The parsed result of the target URL.

    Returns:
        str: The scheme of the target URL.
    """
    return target.scheme or origin.scheme or __DEFAULT_URI_SCHEME


def get_absolute_url(origin: AnyUrl, href_parse_result: ParseResult) -> str:
    """
    Construct the absolute URL from the origin and href.

    Args:
        origin (AnyUrl): The origin URL.
        href_parse_result (ParseResult): The parsed result of the href.

    Returns:
        str: The absolute URL.
    """
    return ''.join([
        get_target_scheme(origin, href_parse_result), '://',
        get_href_netloc(origin, href_parse_result),
        href_parse_result.path
    ]).strip('/')


def absolute_url_from_href(origin_url: AnyUrl, href: str) -> str:
    """
    Convert a relative href to an absolute URL based on the origin URL.

    Args:
        origin_url (AnyUrl): The origin URL.
        href (str): The relative href.

    Returns:
        str: The absolute URL.
    """
    return get_absolute_url(origin_url, urlparse(href))


def absolute_url_mapping(origin: AnyUrl) -> Callable[[List[str]], List[Tuple[AnyUrl, int]]]:
    """
    Create a mapping function to convert a list of hrefs to absolute URLs and count their frequencies.

    Args:
        origin (AnyUrl): The origin URL.

    Returns:
        Callable[[List[str]], List[Tuple[AnyUrl, int]]]: A function that takes a list of hrefs and returns a list of tuples with absolute URLs and their frequencies.
    """
    return lambda hrefs: pipe(
        hrefs,
        lambda _hrefs: list(map(
            lambda href: absolute_url_from_href(origin, href), _hrefs
        )),
        lambda _hrefs: [AnyUrl(href) for href in _hrefs],
        frequencies,
        lambda freq: [(k, v) for k, v in freq.items()]
    )


def find_hrefs_in_soup(soup: BeautifulSoup) -> List[str]:
    """
    Find all hrefs in the body of a BeautifulSoup object.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object to search.

    Returns:
        List[str]: A list of hrefs found in the body.
    """
    return [a.get('href') for a in soup.find('body').find_all('a', href=True)]


def parse_absolute_urls(origin: AnyUrl, soup: BeautifulSoup) -> UrlParseResult:
    """
    Parse absolute URLs from a BeautifulSoup object.

    Args:
        origin (AnyUrl): The origin URL.
        soup (BeautifulSoup): The BeautifulSoup object to parse.

    Returns:
        UrlParseResult: The result containing the origin and the list of absolute URLs with their frequencies.
    """
    return UrlParseResult(
        origin=origin,
        urls=pipe(
            soup,
            find_hrefs_in_soup,
            absolute_url_mapping(origin)
        )
    )