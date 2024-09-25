from bs4 import BeautifulSoup
from pydantic import AnyUrl

from unibas.common.logic.url_logic import UrlParseResult, parse_absolute_urls


def get_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def parse_html_title(soup: BeautifulSoup) -> str | None:
    title = soup.title.string if soup.title else soup.find('h1').text if soup.find('h1') else None
    if title is None:
        h1 = soup.find('h1')
        if h1 is not None:
            title = h1.text
    return title


def parse_html_author(soup: BeautifulSoup) -> str | None:
    return (soup.find('meta', attrs={"name": "author"}) or {}).get('content', None)


def parse_html_date(soup: BeautifulSoup, or_else_date: str = None) -> str | None:
    return (soup.find('meta', attrs={"name": "date"}) or {}).get('content', or_else_date)


def parse_html_description(soup: BeautifulSoup) -> str | None:
    return (soup.find('meta', attrs={"name": "description"}) or {}).get('content', None)


def parse_html_keywords(soup: BeautifulSoup) -> str | None:
    return (soup.find('meta', attrs={"name": "keywords"}) or {}).get('content', None)


def parse_html_links(url: AnyUrl, soup: BeautifulSoup) -> UrlParseResult:
    return parse_absolute_urls(url, soup)


def get_all_text_from_html_body(soup: BeautifulSoup) -> str:
    body: BeautifulSoup = soup.find('body')
    if not body:
        return ''
    else:
        return body.text.strip()
