import re
from typing import List, Dict

from unibas.common.model.charset_model import Charset


def replace_escape_sequences_with_spaces(text: str) -> str:
    return re.sub(r'[\n\t\r\f\v]+', ' ', text).strip()


def contract_consecutive_whitespaces(text: str) -> str:
    return re.sub(r' {2,}', ' ', text).strip()


def split_into_sentences(text: str) -> List[str]:
    return re.compile(r'(?<=[.!?])\s+').split(text)


def collect_sentences_into_chunks(sentences: List[str]) -> Dict[int, str]:
    chunks = dict()
    current_chunk = ""

    chunk_index = 0
    for sent in sentences:
        if len(current_chunk) + len(sent) <= 8000:
            current_chunk += " " + sent if current_chunk else sent
        else:
            chunks[chunk_index] = current_chunk
            chunk_index += 1
            current_chunk = sent

    # Add the last chunk if there's any leftover text
    if current_chunk:
        chunks[chunk_index] = current_chunk

    return chunks


def get_as_string(content: str | bytes, charset: Charset = Charset.UTF_8) -> str:
    if isinstance(content, bytes):
        return content.decode(charset)
    elif isinstance(content, str):
        return content
    else:
        raise TypeError(f'Unexpected type {type(content)}')


def get_as_bytes(content: str | bytes, charset: Charset = Charset.UTF_8) -> bytes:
    if isinstance(content, str):
        return content.encode(charset)
    elif isinstance(content, bytes):
        return content
    else:
        raise TypeError(f'Unexpected type {type(content)}')

