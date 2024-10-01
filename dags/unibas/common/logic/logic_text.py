import re
import ssl
import unicodedata
from typing import List

import nltk

from unibas.common.model.model_charset import Charset


def download_nltk_data():
    """
    Download necessary NLTK data files for sentence tokenization.
    """
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context

    nltk.download('punkt_tab', quiet=True)


download_nltk_data()


def collect_sentences_into_chunks(sentences: List[str], max_chunk_size: int = 8000) -> List[str]:
    """
    Collect sentences into chunks, ensuring each chunk does not exceed the specified maximum size.

    Args:
        sentences (List[str]): The list of sentences to collect into chunks.
        max_chunk_size (int, optional): The maximum size of each chunk. Defaults to 8000.

    Returns:
        TextChunks: The collected chunks of sentences.
    """
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        # Add 1 for the space character
        if len(current_chunk) + len(sentence) + 1 <= max_chunk_size:
            current_chunk += " " + sentence if current_chunk else sentence
        else:
            chunks.append(current_chunk)
            current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def get_as_string(content: str | bytes, charset: Charset = Charset.UTF_8) -> str:
    """
    Convert content to a string using the specified charset.

    Args:
        content (str | bytes): The content to convert.
        charset (Charset, optional): The charset to use for decoding bytes. Defaults to Charset.UTF_8.

    Returns:
        str: The content as a string.

    Raises:
        TypeError: If the content is not of type str or bytes.
    """
    if isinstance(content, bytes):
        return content.decode(charset)
    elif isinstance(content, str):
        return content
    else:
        raise TypeError(f'Unexpected type {type(content)}')


def get_as_bytes(content: str | bytes, charset: Charset = Charset.UTF_8) -> bytes:
    """
    Convert content to bytes using the specified charset.

    Args:
        content (str | bytes): The content to convert.
        charset (Charset, optional): The charset to use for encoding strings. Defaults to Charset.UTF_8.

    Returns:
        bytes: The content as bytes.

    Raises:
        TypeError: If the content is not of type str or bytes.
    """
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

    Args:
        text (str): The text to normalize.

    Returns:
        str: The normalized text.
    """
    return unicodedata.normalize('NFKC', text)


def remove_control_characters(text: str) -> str:
    """
    Remove non-printable control characters from the text, except for newlines which are replaced with spaces.
    Also replaces form feed characters with an empty string.

    Args:
        text (str): The text to clean.

    Returns:
        str: The cleaned text.
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

    Args:
        text (str): The text to clean.

    Returns:
        str: The cleaned text.
    """
    return re.sub(r'\s{2,}', ' ', text)


def strip_whitespace(text: str) -> str:
    """
    Strip leading and trailing whitespace from the text.

    Args:
        text (str): The text to clean.

    Returns:
        str: The cleaned text.
    """
    return text.strip()


def clean_text(text: str) -> str:
    """
    Combines all text cleaning steps into a single function.

    Args:
        text (str): The text to clean.

    Returns:
        str: The cleaned text.
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

    Args:
        text (str): The text to split.

    Returns:
        List[str]: The list of sentences.
    """
    return nltk.sent_tokenize(text)


def clean_and_split_text(text: str) -> List[str]:
    """
    Clean and split text into sentences.

    Args:
        text (str): The text to clean and split.

    Returns:
        TextChunks: The cleaned and split text chunks.
    """
    text = clean_text(text)
    sentences = nlp_split_into_sentences(text)
    chunks = collect_sentences_into_chunks(sentences)
    return chunks


def filter_below_word_count(chunks: List[str], min_word_count: int = 10) -> List[str]:
    """
    Filter out chunks that have a word count below the specified minimum.

    Args:
        chunks (List[str]): The list of chunks to filter.
        min_word_count (int): The minimum word count for a chunk to be retained.

    Returns:
        List[str]: The filtered list of chunks.
    """
    return [chunk for chunk in chunks if len(chunk.split()) >= min_word_count]