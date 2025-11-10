import logging
from pathlib import Path
from typing import Optional

from src.exceptions import PDFParsingException, PDFValidationError
from src.schemas.pdf_parser.models import PdfContent

from .doc_parser_utils import DoclingParser



class PDFParserService:
    """Service for parsing PDF documents using DoclingParser."""

    def __init__(self, max_pages: Optional[int] = 30, max_size_mb: Optional[int] = 20, do_ocr: bool = False, do_table_structure: bool = True):
        
        self.parser = DoclingParser(max_pages=max_pages, max_size_mb=max_size_mb, do_ocr=do_ocr, do_table_structure=do_table_structure)


    async def parse_pdf(self, pdf_path: Path) -> Optional[PdfContent]:
        """
        Parse PDF using Docling parser only.

        Args:
            pdf_path: Path to PDF file

        Returns:
            PdfContent object or None if parsing failed
        """
        if not pdf_path.exists():
            raise PDFValidationError(f"PDF file not found: {pdf_path}")

        try:
            result = await self.docling_parser.parse_pdf(pdf_path)
            if result:
                return result
            else:
                raise PDFParsingException(f"Docling parsing returned no result for {pdf_path.name}")

        except (PDFValidationError, PDFParsingException):
            raise
        except Exception as e:
            raise PDFParsingException(f"Docling parsing error for {pdf_path.name}: {e}")


