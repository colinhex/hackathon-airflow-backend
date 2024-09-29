from bs4 import BeautifulSoup
from pydantic import AnyUrl

from unibas.common.logic.logic_url import UrlParseResult, parse_absolute_urls


def get_soup(html: str) -> BeautifulSoup:
    """
    Parse the given HTML string and return a BeautifulSoup object.

    Args:
        html (str): The HTML content to parse.

    Returns:
        BeautifulSoup: A BeautifulSoup object representing the parsed HTML.
    """
    return BeautifulSoup(html, "html.parser")


def parse_html_title(soup: BeautifulSoup) -> str | None:
    """
    Extract the title from the given BeautifulSoup object.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object to extract the title from.

    Returns:
        str | None: The extracted title, or None if no title is found.
    """
    title = soup.title.string if soup.title else soup.find('h1').text if soup.find('h1') else None
    if title is None:
        h1 = soup.find('h1')
        if h1 is not None:
            title = h1.text
    return title


def parse_html_author(soup: BeautifulSoup) -> str | None:
    """
    Extract the author from the given BeautifulSoup object.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object to extract the author from.

    Returns:
        str | None: The extracted author, or None if no author is found.
    """
    return (soup.find('meta', attrs={"name": "author"}) or {}).get('content', None)


def parse_html_date(soup: BeautifulSoup, or_else_date: str = None) -> str | None:
    """
    Extract the date from the given BeautifulSoup object.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object to extract the date from.
        or_else_date (str, optional): The default date to return if no date is found. Defaults to None.

    Returns:
        str | None: The extracted date, or the default date if no date is found.
    """
    return (soup.find('meta', attrs={"name": "date"}) or {}).get('content', or_else_date)


def parse_html_description(soup: BeautifulSoup) -> str | None:
    """
    Extract the description from the given BeautifulSoup object.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object to extract the description from.

    Returns:
        str | None: The extracted description, or None if no description is found.
    """
    return (soup.find('meta', attrs={"name": "description"}) or {}).get('content', None)


def parse_html_keywords(soup: BeautifulSoup) -> str | None:
    """
    Extract the keywords from the given BeautifulSoup object.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object to extract the keywords from.

    Returns:
        str | None: The extracted keywords, or None if no keywords are found.
    """
    return (soup.find('meta', attrs={"name": "keywords"}) or {}).get('content', None)


def parse_html_links(url: AnyUrl, soup: BeautifulSoup) -> UrlParseResult:
    """
    Extract and parse absolute URLs from the given BeautifulSoup object.

    Args:
        url (AnyUrl): The base URL to resolve relative links against.
        soup (BeautifulSoup): The BeautifulSoup object to extract the links from.

    Returns:
        UrlParseResult: The result of parsing the URLs.
    """
    return parse_absolute_urls(url, soup)


def get_all_text_from_html_body(soup: BeautifulSoup) -> str:
    """
    Extract all text content from the body of the given BeautifulSoup object.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object to extract the text from.

    Returns:
        str: The extracted text content, or an empty string if no body is found.
    """
    body: BeautifulSoup = soup.find('body')
    if not body:
        return ''
    else:
        return body.get_text(separator=' ').strip()