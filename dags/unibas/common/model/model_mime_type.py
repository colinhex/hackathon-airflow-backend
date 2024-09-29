from enum import Enum
from typing import Set


class MimeType(str, Enum):
    """
    Enumeration of various MIME types.

    Attributes:
        UNKNOWN (str): Unknown MIME type.
        JSON (str): MIME type for JSON.
        JSON_LD (str): MIME type for JSON-LD.
        TEXT_XML (str): MIME type for XML.
        TEXT_HTML (str): MIME type for HTML.
        TEXT_PLAIN (str): MIME type for plain text.
        TEXT_CSV (str): MIME type for CSV.
        TEXT_JAVASCRIPT (str): MIME type for JavaScript.
        APPLICATION_JAVASCRIPT (str): MIME type for JavaScript.
        APPLICATION_X_JAVASCRIPT (str): MIME type for JavaScript.
        TEXT_CSS (str): MIME type for CSS.
        APPLICATION_XML (str): MIME type for XML.
        APPLICATION_RSS_XML (str): MIME type for RSS XML.
        APPLICATION_ATOM_XML (str): MIME type for Atom XML.
        APPLICATION_XHTML_XML (str): MIME type for XHTML XML.
        APPLICATION_PDF (str): MIME type for PDF.
        APPLICATION_MSWORD (str): MIME type for MS Word.
        APPLICATION_DOCX (str): MIME type for DOCX.
        APPLICATION_XLS (str): MIME type for Excel.
        APPLICATION_XLSX (str): MIME type for Excel.
        APPLICATION_PPT (str): MIME type for PowerPoint.
        APPLICATION_PPTX (str): MIME type for PowerPoint.
        IMAGE_JPEG (str): MIME type for JPEG images.
        IMAGE_PNG (str): MIME type for PNG images.
        IMAGE_GIF (str): MIME type for GIF images.
    """
    UNKNOWN = 'unknown'
    JSON = 'application/json'
    JSON_LD = 'application/ld+json'
    TEXT_XML = 'text/xml'
    TEXT_HTML = 'text/html'
    TEXT_PLAIN = 'text/plain'
    TEXT_CSV = 'text/csv'
    TEXT_JAVASCRIPT = 'text/javascript'
    APPLICATION_JAVASCRIPT = 'application/javascript'
    APPLICATION_X_JAVASCRIPT = 'application/x-javascript'
    TEXT_CSS = 'text/css'
    APPLICATION_XML = 'application/xml'
    APPLICATION_RSS_XML = 'application/rss+xml'
    APPLICATION_ATOM_XML = 'application/atom+xml'
    APPLICATION_XHTML_XML = 'application/xhtml+xml'
    APPLICATION_PDF = 'application/pdf'
    APPLICATION_MSWORD = 'application/msword'
    APPLICATION_DOCX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    APPLICATION_XLS = 'application/vnd.ms-excel'
    APPLICATION_XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    APPLICATION_PPT = 'application/vnd.ms-powerpoint'
    APPLICATION_PPTX = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    IMAGE_JPEG = 'image/jpeg'
    IMAGE_PNG = 'image/png'
    IMAGE_GIF = 'image/gif'

    @staticmethod
    def from_content_type(content_type: str):
        """
        Determines the MIME type from the content type string.

        Args:
            content_type (str): The content type string.

        Returns:
            MimeType: The corresponding MimeType enum value.
        """
        if content_type is None:
            return MimeType.UNKNOWN
        _content_type, _ = content_type.split(';')[0].strip() if ';' in content_type else content_type, None
        return MimeType(_content_type) if _content_type else MimeType.UNKNOWN

# Set of MIME types for text content
TEXT_MIME_TYPE: Set[MimeType] = {
    MimeType.TEXT_PLAIN,
    MimeType.TEXT_HTML,
    MimeType.TEXT_XML,
    MimeType.TEXT_CSS,
    MimeType.TEXT_CSV,
    MimeType.TEXT_JAVASCRIPT,
    MimeType.APPLICATION_XML,
    MimeType.APPLICATION_RSS_XML,
    MimeType.APPLICATION_ATOM_XML,
    MimeType.APPLICATION_XHTML_XML,
}

# Set of MIME types for binary content
BINARY_MIME_TYPE: Set[MimeType] = {
    MimeType.APPLICATION_PDF,
    MimeType.APPLICATION_MSWORD,
    MimeType.APPLICATION_DOCX,
    MimeType.APPLICATION_XLS,
    MimeType.APPLICATION_XLSX,
    MimeType.APPLICATION_PPT,
    MimeType.APPLICATION_PPTX,
    MimeType.IMAGE_JPEG,
    MimeType.IMAGE_PNG,
    MimeType.IMAGE_GIF,
}

# Set of MIME types for JSON content
JSON_MIME_TYPE: Set[MimeType] = {
    MimeType.JSON,
    MimeType.JSON_LD,
}

# Set of MIME types for XML content
XML_MIME_TYPE: Set[MimeType] = {
    MimeType.TEXT_XML,
    MimeType.APPLICATION_XML,
    MimeType.APPLICATION_RSS_XML,
    MimeType.APPLICATION_ATOM_XML,
    MimeType.APPLICATION_XHTML_XML,
}

# Set of MIME types for image content
IMAGE_MIME_TYPE: Set[MimeType] = {
    MimeType.IMAGE_JPEG,
    MimeType.IMAGE_PNG,
    MimeType.IMAGE_GIF,
}

# Set of MIME types for PDF content
PDF_MIME_TYPE: Set[MimeType] = {
    MimeType.APPLICATION_PDF,
}

# Combine all MIME type sets into one
MIME_TYPE_GROUP: Set[MimeType] = (
    TEXT_MIME_TYPE |
    BINARY_MIME_TYPE |
    JSON_MIME_TYPE |
    XML_MIME_TYPE |
    IMAGE_MIME_TYPE |
    PDF_MIME_TYPE
)


def is_in_mime_type_group(mime_type: MimeType, mime_type_group: MIME_TYPE_GROUP) -> bool:
    """
    Checks if a MIME type is in a given MIME type group.

    Args:
        mime_type (MimeType): The MIME type to check.
        mime_type_group (MIME_TYPE_GROUP): The group of MIME types.

    Returns:
        bool: True if the MIME type is in the group, False otherwise.
    """
    return mime_type in mime_type_group
