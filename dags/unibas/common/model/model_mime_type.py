from enum import Enum
from typing import Set


class MimeType(str, Enum):
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
        if content_type is None:
            return MimeType.UNKNOWN
        _content_type, _ = content_type.split(';')[0].strip() if ';' in content_type else content_type, None
        return MimeType(_content_type) if _content_type else MimeType.UNKNOWN


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

JSON_MIME_TYPE: Set[MimeType] = {
    MimeType.JSON,
    MimeType.JSON_LD,
}

XML_MIME_TYPE: Set[MimeType] = {
    MimeType.TEXT_XML,
    MimeType.APPLICATION_XML,
    MimeType.APPLICATION_RSS_XML,
    MimeType.APPLICATION_ATOM_XML,
    MimeType.APPLICATION_XHTML_XML,
}

IMAGE_MIME_TYPE: Set[MimeType] = {
    MimeType.IMAGE_JPEG,
    MimeType.IMAGE_PNG,
    MimeType.IMAGE_GIF,
}

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
    return mime_type in mime_type_group


if __name__ == '__main__':
    print(is_in_mime_type_group(MimeType.TEXT_XML, XML_MIME_TYPE))
    print(is_in_mime_type_group(MimeType.TEXT_XML, JSON_MIME_TYPE))
