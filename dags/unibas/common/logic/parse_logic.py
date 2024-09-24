from toolz import pipe

from unibas.common.model.mime_model import *
from unibas.common.model.parsed_model import *

from unibas.common.logic.html_logic import *
from unibas.common.logic.text_logic import *
from unibas.common.logic.xml_logic import *
from unibas.common.logic.pdf_logic import *


def parse(content: WebContent) -> 'ParsedContentUnion':
    if isinstance(content, WebContent):
        try:
            started_parsing_at: datetime = datetime.now()
            return parse_web_content(content).add_parse_time(started_parsing_at)
        except NotImplementedError as nie:
            return ParsedWebContentFailure.create(content=content, reason=nie)
        except Exception as exception:
            raise Exception('Something happened during parsing: ', exception)
    else:
        raise ValueError(f'Content not recognized: {type(content)}')


def parse_web_content(content: WebContent) -> 'ParsedContentUnion':
    match content:
        case WebContent(mime_type=MimeType.TEXT_HTML):
            print(f"Matched: {content.loc}, MIME Type: {MimeType.TEXT_HTML}")
            return parse_web_content_text_html(content)
        case WebContent(mime_type=MimeType.JSON):
            print(f"Matched: {content.loc}, MIME Type: {MimeType.JSON}")
            return parse_web_content_json(content)
        case WebContent(mime_type=MimeType.JSON_LD):
            print(f"Matched: {content.loc}, MIME Type: {MimeType.JSON_LD}")
            return parse_web_content_json_ld(content)
        case WebContent(mime_type=MimeType.TEXT_XML):
            print(f"Matched: {content.loc}, MIME Type: {MimeType.TEXT_XML}")
            return parse_web_content_text_xml(content)
        case WebContent(mime_type=MimeType.TEXT_PLAIN):
            print(f"Matched: {content.loc}, MIME Type: {MimeType.TEXT_PLAIN}")
            return parse_web_content_text_plain(content)
        case WebContent(mime_type=MimeType.TEXT_CSV):
            print(f"Matched: {content.loc}, MIME Type: {MimeType.TEXT_CSV}")
            return parse_web_content_text_csv(content)
        case WebContent(mime_type=MimeType.TEXT_JAVASCRIPT):
            print(f"Matched: {content.loc}, MIME Type: {MimeType.TEXT_JAVASCRIPT}")
            return parse_web_content_text_javascript(content)
        case WebContent(mime_type=MimeType.APPLICATION_JAVASCRIPT):
            print(f"Matched: {content.loc}, MIME Type: {MimeType.APPLICATION_JAVASCRIPT}")
            return parse_web_content_application_javascript(content)
        case WebContent(mime_type=MimeType.TEXT_CSS):
            print(f"Matched: {content.loc}, MIME Type: {MimeType.TEXT_CSS}")
            return parse_web_content_text_css(content)
        case WebContent(mime_type=MimeType.APPLICATION_XML):
            print(f"Matched: {content.loc}, MIME Type: {MimeType.APPLICATION_XML}")
            return parse_web_content_application_xml(content)
        case WebContent(mime_type=MimeType.APPLICATION_RSS_XML):
            print(f"Matched: {content.loc}, MIME Type: {MimeType.APPLICATION_RSS_XML}")
            return parse_web_content_application_rss_xml(content)
        case WebContent(mime_type=MimeType.APPLICATION_ATOM_XML):
            print(f"Matched: {content.loc}, MIME Type: {MimeType.APPLICATION_ATOM_XML}")
            return parse_web_content_application_atom_xml(content)
        case WebContent(mime_type=MimeType.APPLICATION_XHTML_XML):
            print(f"Matched: {content.loc}, MIME Type: {MimeType.APPLICATION_XHTML_XML}")
            return parse_web_content_application_xhtml_xml(content)
        case WebContent(mime_type=MimeType.APPLICATION_PDF):
            print(f"Matched: {content.loc}, MIME Type: {MimeType.APPLICATION_PDF}")
            return parse_web_content_application_pdf(content)
        case WebContent(mime_type=MimeType.APPLICATION_MSWORD):
            print(f"Matched: {content.loc}, MIME Type: {MimeType.APPLICATION_MSWORD}")
            return parse_web_content_application_msword(content)
        case WebContent(mime_type=MimeType.APPLICATION_DOCX):
            print(f"Matched: {content.loc}, MIME Type: {MimeType.APPLICATION_DOCX}")
            return parse_web_content_application_docx(content)
        case WebContent(mime_type=MimeType.APPLICATION_XLS):
            print(f"Matched: {content.loc}, MIME Type: {MimeType.APPLICATION_XLS}")
            return parse_web_content_application_xls(content)
        case WebContent(mime_type=MimeType.APPLICATION_XLSX):
            print(f"Matched: {content.loc}, MIME Type: {MimeType.APPLICATION_XLSX}")
            return parse_web_content_application_xlsx(content)
        case WebContent(mime_type=MimeType.APPLICATION_PPT):
            print(f"Matched: {content.loc}, MIME Type: {MimeType.APPLICATION_PPT}")
            return parse_web_content_application_ppt(content)
        case WebContent(mime_type=MimeType.APPLICATION_PPTX):
            print(f"Matched: {content.loc}, MIME Type: {MimeType.APPLICATION_PPTX}")
            return parse_web_content_application_pptx(content)
        case WebContent(mime_type=MimeType.IMAGE_JPEG):
            print(f"Matched: {content.loc}, MIME Type: {MimeType.IMAGE_JPEG}")
            return parse_web_content_image_jpeg(content)
        case WebContent(mime_type=MimeType.IMAGE_PNG):
            print(f"Matched: {content.loc}, MIME Type: {MimeType.IMAGE_PNG}")
            return parse_web_content_image_png(content)
        case WebContent(mime_type=MimeType.IMAGE_GIF):
            print(f"Matched: {content.loc}, MIME Type: {MimeType.IMAGE_GIF}")
            return parse_web_content_image_gif(content)
        case _:
            raise ValueError(f"Unsupported MIME type: {content.mime_type}")


# ##################################################################################################
# XML PARSING --------------------------------------------------------------------------------------


def parse_web_content_text_xml(content: WebContent):
    soup: BeautifulSoup = get_xml_soup(content.content, charset=content.charset)
    if is_sitemap(soup):
        return parse_web_content_xml_sitemap(content)

    raise NotImplementedError("Parsing for TEXT_XML is not implemented.")


def parse_web_content_application_xml(content: WebContent):
    soup: BeautifulSoup = get_xml_soup(content.content, charset=content.charset)
    if is_sitemap(soup):
        return parse_web_content_xml_sitemap(content)

    raise NotImplementedError("Parsing for APPLICATION_XML is not implemented.")


def parse_web_content_application_rss_xml(content: WebContent):
    soup: BeautifulSoup = get_xml_soup(content.content, charset=content.charset)
    if is_sitemap(soup):
        return parse_web_content_xml_sitemap(content)

    raise NotImplementedError("Parsing for APPLICATION_RSS_XML is not implemented.")


def parse_web_content_application_atom_xml(content: WebContent):
    soup: BeautifulSoup = get_xml_soup(content.content, charset=content.charset)
    if is_sitemap(soup):
        return parse_web_content_xml_sitemap(content)

    raise NotImplementedError("Parsing for APPLICATION_ATOM_XML is not implemented.")


def parse_web_content_application_xhtml_xml(content: WebContent):
    soup: BeautifulSoup = get_xml_soup(content.content, charset=content.charset)
    if is_sitemap(soup):
        return parse_web_content_xml_sitemap(content)

    raise NotImplementedError("Parsing for APPLICATION_XHTML_XML is not implemented.")


def parse_web_content_xml_sitemap(content: WebContent):
    print(f'Parsing WebContent XML Sitemap: {content.loc}')
    xml_soup = get_xml_soup(content.content, charset=content.charset)

    match content:
        case WebContent(loc='https://www.dummy-host.com/specific-path/specific-thing.any'):
            # Special Parsing for an exact resource.
            raise ValueError()
        case _:
            if content.is_same_host('https://www.dummy-host.com'):
                # Special Parsing for a given host.
                raise ValueError()
            elif content.is_sub_path_from('https://www.dummy-host.com/some-path'):
                # Special Parsing for given sub-path.
                raise ValueError()
            elif content.is_sub_path_from_any([
                'https://www.dummy-host.com/some-path',
                'https://www.dummy-host.com/some-other-path'
            ]):
                # Special Parsing for multiple sub-paths.
                raise ValueError()
            filter_paths = None

    return ParsedWebContentXmlSitemapResult(
        loc=content.loc,
        lastmod=content.lastmod,
        code=content.code,
        mime_type=content.mime_type,
        charset=content.charset,
        content=parse_web_resources_from_sitemap(xml_soup, filter_paths=filter_paths)
    )


# XML PARSING -------------------------------------------------------------------------------------
# #################################################################################################
# HTML PARSING ------------------------------------------------------------------------------------

def parse_web_content_text_html(content: WebContent) -> 'ParsedContentUnion':
    attributes: HtmlAttributes = parse_html_to_attributes(content)
    return ParsedWebContentHtml(
        loc=content.loc,
        lastmod=content.lastmod,
        code=content.code,
        mime_type=content.mime_type,
        charset=content.charset,
        attributes=attributes,
        content=parse_html_body(content)
    )


def parse_html_to_attributes(content: WebContent) -> HtmlAttributes:
    html_text: str = get_as_string(content.content, charset=content.charset)
    soup: BeautifulSoup = get_soup(html_text)

    title: Optional[str] = parse_html_title(soup)
    author: Optional[str] = parse_html_author(soup)
    date: Optional[str] = parse_html_date(soup)
    description: Optional[str] = parse_html_description(soup)
    keywords: Optional[str] = parse_html_keywords(soup)
    links: UrlParseResult = parse_html_links(content.loc, soup)

    return HtmlAttributes(
        title=title,
        author=author,
        date=date,
        description=description,
        keywords=keywords,
        links=links,
    )


def parse_html_body(content: WebContent) -> 'TextChunks':
    html_text: str = get_as_string(content.content, charset=content.charset)
    soup: BeautifulSoup = get_soup(html_text)

    match content:
        case WebContent(loc='https://www.dummy-host.com/specific-path/specific-thing.any'):
            # Special Parsing for an exact resource.
            raise ValueError()
        case _:
            if content.is_same_host('https://www.dummy-host.com'):
                # Special Parsing for a given host.
                raise ValueError()
            elif content.is_sub_path_from('https://www.dummy-host.com/some-path'):
                # Special Parsing for given sub-path.
                raise ValueError()
            elif content.is_sub_path_from_any([
                'https://www.dummy-host.com/some-path',
                'https://www.dummy-host.com/some-other-path'
            ]):
                # Special Parsing for multiple sub-paths.
                raise ValueError()
            return pipe(
                get_all_text_from_html_body(soup),
                replace_escape_sequences_with_spaces,
                contract_consecutive_whitespaces,
                split_into_sentences,
                collect_sentences_into_chunks
            )


# HTML PARSING -------------------------------------------------------------------------------------
# ##################################################################################################
# PDF PARSING --------------------------------------------------------------------------------------


def parse_web_content_application_pdf(content: WebContent) -> 'ParsedContentUnion':
    attributes: 'PdfAttributes' = parse_pdf_to_attributes(content)
    return ParsedWebContentPdf(
        loc=content.loc,
        lastmod=content.lastmod,
        code=content.code,
        mime_type=content.mime_type,
        charset=content.charset,
        attributes=attributes,
        content=parse_pdf_body(content)
    )


def parse_pdf_to_attributes(content: WebContent) -> PdfAttributes:
    pdf_bytes = get_as_bytes(content.content, charset=content.charset)
    document = get_pdf_document(pdf_bytes)

    title: Optional[str] = parse_pdf_title(document)
    author: Optional[str] = parse_pdf_author(document)
    date: Optional[str] = parse_pdf_date(document)
    description: Optional[str] = parse_pdf_description(document)
    keywords: Optional[str] = parse_pdf_keywords(document)

    return PdfAttributes(
        title=title,
        author=author,
        date=date,
        description=description,
        keywords=keywords,
    )


def parse_pdf_body(content: WebContent) -> 'TextChunks':
    pdf_bytes: bytes = get_as_bytes(content.content, charset=content.charset)

    match content:
        case WebContent(loc='https://www.dummy-host.com/specific-path/specific-thing.any'):
            # Special Parsing for an exact resource.
            raise ValueError()
        case _:
            if content.is_same_host('https://www.dummy-host.com'):
                # Special Parsing for a given host.
                raise ValueError()
            elif content.is_sub_path_from('https://www.dummy-host.com/some-path'):
                # Special Parsing for given sub-path.
                raise ValueError()
            elif content.is_sub_path_from_any([
                'https://www.dummy-host.com/some-path',
                'https://www.dummy-host.com/some-other-path'
            ]):
                # Special Parsing for multiple sub-paths.
                raise ValueError()
            return pipe(
                extract_text_from_pdf_bytes(pdf_bytes),
                replace_escape_sequences_with_spaces,
                contract_consecutive_whitespaces,
                split_into_sentences,
                collect_sentences_into_chunks
            )


# PDF PARSING --------------------------------------------------------------------------------------
# ##################################################################################################
# UNIMPLEMENTED ------------------------------------------------------------------------------------


def parse_web_content_json(content: WebContent):
    raise NotImplementedError("Parsing for JSON is not implemented.")


def parse_web_content_json_ld(content: WebContent):
    raise NotImplementedError("Parsing for JSON_LD is not implemented.")


def parse_web_content_text_plain(content: WebContent):
    raise NotImplementedError("Parsing for TEXT_PLAIN is not implemented.")


def parse_web_content_text_csv(content: WebContent):
    raise NotImplementedError("Parsing for TEXT_CSV is not implemented.")


def parse_web_content_text_javascript(content: WebContent):
    raise NotImplementedError("Parsing for TEXT_JAVASCRIPT is not implemented.")


def parse_web_content_application_javascript(content: WebContent):
    raise NotImplementedError("Parsing for APPLICATION_JAVASCRIPT is not implemented.")


def parse_web_content_text_css(content: WebContent):
    raise NotImplementedError("Parsing for TEXT_CSS is not implemented.")


def parse_web_content_application_msword(content: WebContent):
    raise NotImplementedError("Parsing for APPLICATION_MSWORD is not implemented.")


def parse_web_content_application_docx(content: WebContent):
    raise NotImplementedError("Parsing for APPLICATION_DOCX is not implemented.")


def parse_web_content_application_xls(content: WebContent):
    raise NotImplementedError("Parsing for APPLICATION_XLS is not implemented.")


def parse_web_content_application_xlsx(content: WebContent):
    raise NotImplementedError("Parsing for APPLICATION_XLSX is not implemented.")


def parse_web_content_application_ppt(content: WebContent):
    raise NotImplementedError("Parsing for APPLICATION_PPT is not implemented.")


def parse_web_content_application_pptx(content: WebContent):
    raise NotImplementedError("Parsing for APPLICATION_PPTX is not implemented.")


def parse_web_content_image_jpeg(content: WebContent):
    raise NotImplementedError("Parsing for IMAGE_JPEG is not implemented.")


def parse_web_content_image_png(content: WebContent):
    raise NotImplementedError("Parsing for IMAGE_PNG is not implemented.")


def parse_web_content_image_gif(content: WebContent):
    raise NotImplementedError("Parsing for IMAGE_GIF is not implemented.")

