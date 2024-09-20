from typing import Callable, Dict, List
from urllib.parse import ParseResult, urlparse

from bs4 import BeautifulSoup
from toolz import pipe, frequencies

# If no scheme is present, absolute links will be resolved with this scheme.
__DEFAULT_URI_SCHEME = 'https'


def href_is_different_domain(origin_url_parse_result: ParseResult, href_parse_result: ParseResult):
    # href has a netloc and this netloc differs from the origin
    return href_parse_result.netloc is not None \
        and href_parse_result.netloc != '' \
        and href_parse_result.netloc != origin_url_parse_result.netloc


def get_href_netloc(origin_url_parse_result: ParseResult, href_parse_result: ParseResult) -> str:
    if href_is_different_domain(origin_url_parse_result, href_parse_result):
        print('href_is_different_domain_netloc', href_parse_result.netloc)
        return href_parse_result.netloc
    else:
        return origin_url_parse_result.netloc


def get_target_scheme(origin: ParseResult, target: ParseResult) -> str:
    return target.scheme or origin.scheme or __DEFAULT_URI_SCHEME


def get_absolute_url(origin: ParseResult, href_parse_result: ParseResult) -> str:
    return ''.join([
        get_target_scheme(origin, href_parse_result), '://',
        get_href_netloc(origin, href_parse_result),
        href_parse_result.path
    ]).strip('/')


def absolute_url_from_href(origin_url: str, href: str) -> str:
    return get_absolute_url(urlparse(origin_url), urlparse(href))


def absolute_url_mapping(url: str) -> Callable[[List[str]], Dict[str, int]]:
    return lambda hrefs: pipe(
        hrefs,
        lambda _hrefs: list(map(
            lambda href: absolute_url_from_href(url, href), _hrefs
        )),
        frequencies,
        lambda freq: [{'loc': k, 'freq': v} for k, v in freq.items() ]
    )


def find_hrefs_in_soup(soup: BeautifulSoup) -> List[str]:
    return [a.get('href') for a in soup.find('body').find_all('a', href=True)]


def parse_absolute_urls(url: str, soup: BeautifulSoup) -> Dict[str, int]:
    return pipe(
        soup,
        find_hrefs_in_soup,
        absolute_url_mapping(url)
    )