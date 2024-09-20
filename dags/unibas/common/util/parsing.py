from typing import Dict, Any

from bs4 import BeautifulSoup

from unibas.common.web.urls import parse_absolute_urls


def get_text_data_from_html(html: str) -> str:
    return BeautifulSoup(html, "html.parser").text


def parse_html_title(soup: BeautifulSoup) -> str | None:
    return soup.title.string if soup.title else soup.find('h1').text if soup.find('h1') else None


def parse_html_author(soup: BeautifulSoup) -> str | None:
    return (soup.find('meta', attrs={"name": "author"}) or {}).get('content', None)


def parse_html_data(soup: BeautifulSoup, or_else_date: str = None) -> str | None:
    return (soup.find('meta', attrs={"name": "date"}) or {}).get('content', or_else_date)


def parse_html_description(soup: BeautifulSoup) -> str | None:
    return (soup.find('meta', attrs={"name": "description"}) or {}).get('content', None)


def parse_html_keywords(soup: BeautifulSoup) -> str | None:
    return (soup.find('meta', attrs={"name": "keywords"}) or {}).get('content', None)


def parse_html_links(url: str, soup: BeautifulSoup) -> Dict[str, Any]:
    return parse_absolute_urls(url, soup)


def parse_html_body(soup: BeautifulSoup) -> str:
    return str(soup.find('body'))
