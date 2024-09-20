# Variables containing the content type
from typing import Tuple

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

# Global content type format map
CONTENT_TYPE_FORMAT_MAP = {
    'application/json': 'json',
    'application/ld+json': 'json',
    'text/xml': 'text',
    'text/html': 'text',
    'text/plain': 'text',
    'text/csv': 'text',
    'text/javascript': 'text',
    'application/javascript': 'text',
    'application/x-javascript': 'text',
    'text/css': 'text',
    'application/xml': 'text',
    'application/rss+xml': 'text',
    'application/atom+xml': 'text',
    'application/xhtml+xml': 'text',
    'application/pdf': 'binary',
    'application/msword': 'binary',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'binary',
    'application/vnd.ms-excel': 'binary',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'binary',
    'application/vnd.ms-powerpoint': 'binary',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'binary',
    'image/jpeg': 'binary',
    'image/png': 'binary',
    'image/gif': 'binary'
}

# Global UTF-8 convertibility map
UTF8_CONVERTIBLE_MAP = {
    'application/json': False,
    'application/ld+json': False,
    'text/xml': True,
    'text/html': True,
    'text/plain': True,
    'text/csv': True,
    'text/javascript': True,
    'application/javascript': True,
    'application/x-javascript': True,
    'text/css': True,
    'application/xml': True,
    'application/rss+xml': True,
    'application/atom+xml': True,
    'application/xhtml+xml': True,
    'application/pdf': False,
    'application/msword': False,
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': False,
    'application/vnd.ms-excel': False,
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': False,
    'application/vnd.ms-powerpoint': False,
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': False,
    'image/jpeg': False,
    'image/png': False,
    'image/gif': False
}


# Function to return the format (either 'json', 'text', or 'binary') for a given content type
def get_content_type_format(content_type: str) -> str:
    return CONTENT_TYPE_FORMAT_MAP.get(content_type, 'unknown')


# Function to check if the content type is UTF-8 convertible (True for 'text', False otherwise)
def is_content_type_utf8_convertible(content_type: str) -> bool:
    return UTF8_CONVERTIBLE_MAP.get(content_type, False)


def parse_content_type(content_type: str) -> Tuple[str, str | None]:
    if ';' in content_type:
        content_type, charset = content_type.split(';')
        return content_type, charset.split('=')[1]
    return content_type, None
