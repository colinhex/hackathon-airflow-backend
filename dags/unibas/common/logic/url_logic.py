from typing import Callable, Dict, List
from urllib.parse import ParseResult, urlparse

from bs4 import BeautifulSoup
from pydantic import AnyUrl
from toolz import pipe, frequencies

from unibas.common.model.parsed_model import UrlParseResult

__DEFAULT_URI_SCHEME = 'https'


def href_is_different_domain(origin: AnyUrl, href_parse_result: ParseResult):
    return href_parse_result.netloc is not None \
        and href_parse_result.netloc != '' \
        and href_parse_result.netloc != origin.host


def get_href_netloc(origin: AnyUrl, href_parse_result: ParseResult) -> str:
    if href_is_different_domain(origin, href_parse_result):
        print('href_is_different_domain_netloc', href_parse_result.netloc)
        return href_parse_result.netloc
    else:
        return origin.host


def get_target_scheme(origin: AnyUrl, target: ParseResult) -> str:
    return target.scheme or origin.scheme or __DEFAULT_URI_SCHEME


def get_absolute_url(origin: AnyUrl, href_parse_result: ParseResult) -> str:
    return ''.join([
        get_target_scheme(origin, href_parse_result), '://',
        get_href_netloc(origin, href_parse_result),
        href_parse_result.path
    ]).strip('/')


def absolute_url_from_href(origin_url: AnyUrl, href: str) -> str:
    return get_absolute_url(origin_url, urlparse(href))


def absolute_url_mapping(origin: AnyUrl) -> Callable[[List[str]], Dict[str, int]]:
    return lambda hrefs: pipe(
        hrefs,
        lambda _hrefs: list(map(
            lambda href: absolute_url_from_href(origin, href), _hrefs
        )),
        AnyUrl,
        frequencies,
        lambda freq: [{'loc': k, 'freq': v} for k, v in freq.items() ]
    )


def find_hrefs_in_soup(soup: BeautifulSoup) -> List[str]:
    return [a.get('href') for a in soup.find('body').find_all('a', href=True)]


def parse_absolute_urls(origin: AnyUrl, soup: BeautifulSoup) -> UrlParseResult:
    urls_with_frequencies: Dict[AnyUrl, int] = pipe(
        soup,
        find_hrefs_in_soup,
        absolute_url_mapping(origin)
    )
    return UrlParseResult(
        origin=origin,
        urls=[(link, freq) for link, freq in urls_with_frequencies.items()],
    )
