import logging
from pathlib import Path
from typing import Optional

import pypdfium2 as pdfium
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from src.exceptions import PDFParsingException, PDFValidationError
from src.schemas.pdf_parser.models import PaperSection, PdfContent


class DoclingParser:
    """Docling PDF Parser"""

    def __init__(self, max_pages: int = 30, max_size_mb: int = 20,
                 do_ocr: bool = False, do_table_structure: bool = True):
        self.max_pages = max_pages
        self.max_size_bytes = max_size_mb * 1024 * 1024

        pipeline_options = PdfPipelineOptions(
            do_table_structure=do_table_structure,
            do_ocr=do_ocr
        )
        self.converter = DocumentConverter(format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        })
        self.warmed_up = False

    def _warm_up_model(self) -> None:
        if not self.warmed_up:
            # place any heavy init here
            self.warmed_up = True

    def _validate_pdf(self, file_path: Path) -> None:
        """Validate the PDF file before parsing.
        
        Args:
            file_path: Path to the PDF file

        Raises:
            PDFValidationError: If the PDF is invalid
        """
        pdf_reader = None
        try:
            if not file_path.is_file():
                raise PDFValidationError(f"File {file_path} does not exist.")

            file_size = file_path.stat().st_size
            if file_size == 0:
                raise PDFValidationError("PDF file is empty.")
            if file_size > self.max_size_bytes:
                raise PDFValidationError(
                    f"PDF file size {file_size / (1024*1024):.2f} MB exceeds the maximum "
                    f"allowed size of {self.max_size_bytes / (1024*1024):.2f} MB."
                )

            # Validate PDF header (strict)
            with open(file_path, "rb") as f:
                header = f.read(8)
                if not header.startswith(b"%PDF-"):
                    raise PDFValidationError("File is not a valid PDF (missing %PDF- header).")

            # Count pages
            pdf_reader = pdfium.PdfDocument(file_path)
            try:
                num_pages = len(pdf_reader)
            finally:
                # ensure close even if len() raises
                try:
                    pdf_reader.close()
                except Exception:
                    pass

            if num_pages > self.max_pages:
                raise PDFValidationError(
                    f"PDF has {num_pages} pages, which exceeds the maximum allowed {self.max_pages} pages."
                )

        except PDFValidationError:
            raise
        except Exception as e:
            raise PDFValidationError(f"PDF validation failed: {e}") from e

    async def parse_pdf(self, file_path: Path) -> Optional[PdfContent]:
        """Parse the PDF file and extract content using Docling.
        
        Args:
            file_path: Path to the PDF file

        Returns:
            PdfContent object with extracted content
        """
        try:
            # 1) Validate
            self._validate_pdf(file_path)

            # 2) Warm up
            self._warm_up_model()

            # 3) Convert with Docling
            result = self.converter.convert(
                str(file_path),
                max_num_pages=self.max_pages,
                max_file_size=self.max_size_bytes
            )
            doc = result.document

            # 4) Build sections
            sections = []
            current = {"title": "Content", "content": ""}

            for element in getattr(doc, "texts", []):
                if hasattr(element, "label") and element.label in ["title", "section_header"]:
                    if current["content"].strip():
                        sections.append(PaperSection(title=current["title"], content=current["content"].strip()))
                    current = {"title": element.text.strip(), "content": ""}
                else:
                    if hasattr(element, "text") and element.text:
                        current["content"] += element.text + "\n"

            if current["content"].strip():
                sections.append(PaperSection(title=current["title"], content=current["content"].strip()))

            return PdfContent(
                sections=sections,
                figures=[],
                tables=[],
                raw_text=doc.export_to_text(),
                references=[],
                parser_used="DOCLING",
                metadata={"source": "docling", "note": "Content extracted from PDF, metadata comes from arXiv API"},
            )

        except PDFValidationError:
            raise
        except Exception as e:
            raise PDFParsingException(f"Error parsing PDF {file_path}: {e}") from e