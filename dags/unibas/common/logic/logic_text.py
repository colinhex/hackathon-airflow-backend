import re
import ssl
import unicodedata
from typing import List

import nltk

from unibas.common.model.model_charset import Charset


def download_nltk_data():
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context

    nltk.download('punkt_tab', quiet=True)


download_nltk_data()

from unibas.common.model.model_parsed import TextChunks


def collect_sentences_into_chunks(sentences: List[str], max_chunk_size: int = 8000) -> TextChunks:
    """
    Collect sentences into chunks, ensuring each chunk does not exceed the specified maximum size.
    """
    chunks = {}
    current_chunk = ""
    chunk_index = 0

    for sentence in sentences:
        # Add 1 for the space character
        if len(current_chunk) + len(sentence) + 1 <= max_chunk_size:
            current_chunk += " " + sentence if current_chunk else sentence
        else:
            chunks[chunk_index] = current_chunk
            chunk_index += 1
            current_chunk = sentence

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


def normalize_unicode(text: str) -> str:
    """
    Normalize unicode characters to a standard form using NFKC normalization.
    This helps in unifying different representations of similar characters.
    """
    return unicodedata.normalize('NFKC', text)


def remove_control_characters(text: str) -> str:
    """
    Remove non-printable control characters from the text, except for newlines which are replaced with spaces.
    Also replaces form feed characters with an empty string.
    """
    cleaned_text = []
    for ch in text:
        if ch == '\n':
            cleaned_text.append(' ')
        elif ch == '\x0c':
            continue
        elif unicodedata.category(ch)[0] != 'C':
            cleaned_text.append(ch)
    return ''.join(cleaned_text)


def remove_multiple_spaces(text: str) -> str:
    """
    Replace multiple consecutive whitespace characters with a single space.
    """
    return re.sub(r'\s{2,}', ' ', text)


def strip_whitespace(text: str) -> str:
    """
    Strip leading and trailing whitespace from the text.
    """
    return text.strip()


def clean_text(text: str) -> str:
    """
    Combines all text cleaning steps into a single function.
    """
    text = normalize_unicode(text)
    text = remove_control_characters(text)
    text = remove_multiple_spaces(text)
    text = strip_whitespace(text)
    return text


def nlp_split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences using NLTK's sentence tokenizer.
    This method is more accurate than simple regex splitting.
    """
    return nltk.sent_tokenize(text)


def clean_and_split_text(text: str) -> TextChunks:
    """
    Clean and split text into sentences.
    """
    text = clean_text(text)
    sentences = nlp_split_into_sentences(text)
    return collect_sentences_into_chunks(sentences)
