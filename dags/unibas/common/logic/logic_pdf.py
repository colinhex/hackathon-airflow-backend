from io import BytesIO, StringIO
from typing import Optional, Any

from pdfminer3.converter import (TextConverter)
from pdfminer3.layout import LAParams
from pdfminer3.pdfdocument import PDFDocument
from pdfminer3.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfparser import PDFParser
from pdfminer3.psparser import PSSyntaxError
from pydantic import BaseModel, Field


def get_pdf_document(pdf_bytes: bytes) -> Optional[PDFDocument]:
    """
    Create a PDFDocument object from PDF bytes.

    Args:
        pdf_bytes (bytes): The bytes of the PDF file.

    Returns:
        Optional[PDFDocument]: The PDFDocument object if parsing is successful, None otherwise.
    """
    fp = BytesIO(pdf_bytes)
    parser = PDFParser(fp)
    try:
        document = PDFDocument(parser)
        parser.set_document(document)
        return document
    except PSSyntaxError:
        # Handle corrupted PDF or parsing error
        return None


def parse_pdf_title(document: PDFDocument) -> Optional[str]:
    """
    Extract the title from a PDF document.

    Args:
        document (PDFDocument): The PDF document.

    Returns:
        Optional[str]: The title of the PDF document, or None if not found.
    """
    return get_metadata_field(document, 'Title')


def parse_pdf_author(document: PDFDocument) -> Optional[str]:
    """
    Extract the author from a PDF document.

    Args:
        document (PDFDocument): The PDF document.

    Returns:
        Optional[str]: The author of the PDF document, or None if not found.
    """
    return get_metadata_field(document, 'Author')


def parse_pdf_date(document: PDFDocument) -> Optional[str]:
    """
    Extract the creation date from a PDF document.

    Args:
        document (PDFDocument): The PDF document.

    Returns:
        Optional[str]: The creation date of the PDF document, or None if not found.
    """
    return get_metadata_field(document, 'CreationDate')


def parse_pdf_description(document: PDFDocument) -> Optional[str]:
    """
    Extract the description from a PDF document.

    Args:
        document (PDFDocument): The PDF document.

    Returns:
        Optional[str]: The description of the PDF document, or None if not found.
    """
    return get_metadata_field(document, 'Subject')


def parse_pdf_keywords(document: PDFDocument) -> Optional[str]:
    """
    Extract the keywords from a PDF document.

    Args:
        document (PDFDocument): The PDF document.

    Returns:
        Optional[str]: The keywords of the PDF document, or None if not found.
    """
    return get_metadata_field(document, 'Keywords')


def get_metadata_field(document: PDFDocument, field_name: str) -> Optional[str]:
    """
    Retrieve a specific metadata field from a PDF document.

    Args:
        document (PDFDocument): The PDF document.
        field_name (str): The name of the metadata field to retrieve.

    Returns:
        Optional[str]: The value of the metadata field, or None if not found.
    """
    if document is not None and document.info:
        info = document.info[0]  # document.info is a list of dictionaries
        if field_name in info:
            value = info[field_name]
            if isinstance(value, bytes):
                return value.decode('utf-8', errors='ignore')
            return str(value)
    return None


class PdfExtractionParams(BaseModel):
    """
    Parameters for PDF extraction using pdfminer3. Change for a specific pdf source.

    Attributes:
        page_numbers (Any): Specific page numbers to extract. Can be a set of page numbers or None for all pages.
        max_pages (int): Maximum number of pages to extract. Defaults to 0 (all pages).
        password (bytes): Password to decrypt the PDF if it's encrypted. Defaults to an empty byte string.
        pages_caching (bool): Whether to cache PDF pages for faster processing. Defaults to True.
        resource_manager_caching (bool): Whether to cache resources (fonts, images) during extraction. Defaults to True.
        check_extractable (bool): Whether to check if the PDF allows text extraction. Defaults to True.
        line_overlap (float): Tolerance for overlapping lines in the PDF layout analysis. Defaults to 0.5.
        char_margin (float): The margin between characters to consider them part of the same word. Defaults to 2.0.
        line_margin (float): The margin between lines to consider them part of the same block of text. Defaults to 0.5.
        word_margin (float): The margin between words to consider them part of the same line. Defaults to 0.1.
        boxes_flow (float): Control the layout flow analysis, with values from -1.0 (strictly horizontal) to +1.0 (strictly vertical). Defaults to 0.5.
        detect_vertical (bool): Whether to detect vertical text. Defaults to False.
        all_texts (bool): If True, extracts all text, including figures, captions, and footnotes. Defaults to False.
    """
    page_numbers: Any = Field(None)
    max_pages: int = Field(0)
    password: bytes = Field(b'')
    pages_caching: bool = Field(True)
    resource_manager_caching: bool = Field(True)
    check_extractable: bool = Field(True)
    line_overlap: float = Field(0.5)
    char_margin: float = Field(2.0)
    line_margin: float = Field(0.5)
    word_margin: float = Field(0.1)
    boxes_flow: float = Field(0.5)
    detect_vertical: bool = Field(False)
    all_texts: bool = Field(False)


def extract_text_from_pdf_bytes(
        pdf_bytes: bytes,
        parameters: Optional[PdfExtractionParams] = None
) -> str:
    """
    Extract text from PDF bytes using pdfminer3.

    Args:
        pdf_bytes (bytes): The bytes of the PDF file.
        parameters (Optional[PdfExtractionParams]): The parameters for PDF extraction. Defaults to None.

    Returns:
        str: The extracted text from the PDF.
    """
    if parameters is None:
        parameters = PdfExtractionParams()
    print(f'Parsing pdf size={pdf_bytes.__sizeof__()}b, parameters={parameters.model_dump_json()}')

    resource_manager = PDFResourceManager(caching=parameters.resource_manager_caching)

    string_buffer = StringIO()

    device = TextConverter(
        rsrcmgr=resource_manager,
        outfp=string_buffer,
        laparams=LAParams(
            line_overlap=parameters.line_overlap,
            char_margin=parameters.char_margin,
            line_margin=parameters.line_margin,
            word_margin=parameters.word_margin,
            boxes_flow=parameters.boxes_flow,
            detect_vertical=parameters.detect_vertical,
            all_texts=parameters.all_texts
        )
    )

    interpreter = PDFPageInterpreter(resource_manager, device)

    byte_buffer = BytesIO(pdf_bytes)
    for page in PDFPage.get_pages(
            byte_buffer,
            pagenos=parameters.page_numbers,
            maxpages=parameters.max_pages,
            password=parameters.password,
            caching=parameters.pages_caching,
            check_extractable=parameters.check_extractable
    ):
        interpreter.process_page(page)

    text = string_buffer.getvalue()

    byte_buffer.close()
    device.close()
    string_buffer.close()

    print(f'Parsed pdf, resulted in text length={len(text)}')
    return text