import unittest

from unibas.common.logic.text_logic import (
    collect_sentences_into_chunks,
    get_as_string,
    get_as_bytes,
    normalize_unicode,
    remove_control_characters,
    remove_multiple_spaces,
    strip_whitespace,
    clean_text,
    nlp_split_into_sentences,
    clean_and_split_text
)
from unibas.common.model.charset_model import Charset


class TestTextLogic(unittest.TestCase):

    def test_collect_sentences_into_chunks_handles_empty_list(self):
        result = collect_sentences_into_chunks([])
        self.assertEqual({}, result)

    def test_collect_sentences_into_chunks_handles_single_sentence(self):
        result = collect_sentences_into_chunks(["Hello world."])
        self.assertEqual({0: "Hello world."}, result)

    def test_collect_sentences_into_chunks_handles_multiple_sentences(self):
        sentences = ["Hello world.", "This is a test.", "Another sentence."]
        result = collect_sentences_into_chunks(sentences, max_chunk_size=20)
        self.assertEqual({0: "Hello world.", 1: "This is a test.", 2: "Another sentence."}, result)

    def test_get_as_string_handles_bytes(self):
        result = get_as_string(b"Hello world", Charset.UTF_8)
        self.assertEqual("Hello world", result)

    def test_get_as_string_handles_string(self):
        result = get_as_string("Hello world", Charset.UTF_8)
        self.assertEqual("Hello world", result)

    def test_get_as_bytes_handles_string(self):
        result = get_as_bytes("Hello world", Charset.UTF_8)
        self.assertEqual(b"Hello world", result)

    def test_get_as_bytes_handles_bytes(self):
        result = get_as_bytes(b"Hello world", Charset.UTF_8)
        self.assertEqual(b"Hello world", result)

    def test_normalize_unicode_handles_special_characters(self):
        result = normalize_unicode("Café")
        self.assertEqual("Café", result)

    def test_remove_control_characters_handles_control_characters(self):
        result = remove_control_characters("Hello\x0cWorld")
        self.assertEqual("HelloWorld", result)

    def test_remove_multiple_spaces_handles_multiple_spaces(self):
        result = remove_multiple_spaces("Hello  World   !")
        self.assertEqual("Hello World !", result)

    def test_strip_whitespace_handles_leading_and_trailing_spaces(self):
        result = strip_whitespace("  Hello World!  ")
        self.assertEqual("Hello World!", result)

    def test_clean_text_combines_all_cleaning_steps(self):
        result = clean_text("  Café\nWorld\x0c!  ")
        self.assertEqual("Café World!", result)

    def test_nlp_split_into_sentences_handles_simple_text(self):
        result = nlp_split_into_sentences("Hello world. This is a test.")
        self.assertEqual(["Hello world.", "This is a test."], result)

    def test_clean_and_split_text_handles_complex_text(self):
        result = clean_and_split_text("  Café\nWorld\x0c! This is a test.  ")
        self.assertEqual({0: "Café World! This is a test."}, result)


if __name__ == '__main__':
    unittest.main()
