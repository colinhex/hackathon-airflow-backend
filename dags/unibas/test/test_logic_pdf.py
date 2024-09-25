
import unittest
from unittest.mock import MagicMock

from unibas.common.logic.logic_pdf import (
    parse_pdf_author,
    parse_pdf_date,
    parse_pdf_description,
    parse_pdf_keywords,
    PDFDocument, PdfExtractionParams, extract_text_from_pdf_bytes
)

MOCK_PDF = '''%PDF-1.4
%âãÏÓ
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page 
   /Parent 2 0 R 
   /MediaBox [0 0 612 792] 
   /Contents 4 0 R 
   /Resources << /Font << /F1 5 0 R >> >> 
>>
endobj
4 0 obj
<< /Length 55 >>
stream
BT /F1 24 Tf 100 700 Td (Hello, World!) Tj ET
endstream
endobj
5 0 obj
<< /Type /Font 
   /Subtype /Type1 
   /BaseFont /Helvetica 
>>
endobj
trailer
<< /Root 1 0 R >>
%%EOF'''

class TestPdfLogic(unittest.TestCase):

    def setUp(self):
        self.mock_document = MagicMock(spec=PDFDocument)
        self.mock_document.info = [{
            'Author': b'John Doe',
            'CreationDate': b'D:20230101000000Z',
            'Subject': b'Test PDF',
            'Keywords': b'pdf, test, example'
        }]

    def test_parse_pdf_author(self):
        author = parse_pdf_author(self.mock_document)
        self.assertEqual(author, 'John Doe')

    def test_parse_pdf_date(self):
        date = parse_pdf_date(self.mock_document)
        self.assertEqual(date, 'D:20230101000000Z')

    def test_parse_pdf_description(self):
        description = parse_pdf_description(self.mock_document)
        self.assertEqual(description, 'Test PDF')

    def test_parse_pdf_keywords(self):
        keywords = parse_pdf_keywords(self.mock_document)
        self.assertEqual(keywords, 'pdf, test, example')

    def test_extract_text_from_pdf_bytes(self):
        pdf_bytes = MOCK_PDF.encode('utf-8')

        parameters = PdfExtractionParams()

        text = extract_text_from_pdf_bytes(pdf_bytes, parameters)
        print(f'Extracted Text: {text}')
        self.assertIn('Hello, World!', text)


if __name__ == '__main__':
    unittest.main()