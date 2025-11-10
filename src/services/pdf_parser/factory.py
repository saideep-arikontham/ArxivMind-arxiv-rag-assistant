from functools import lru_cache
from .doc_parser import PDFParserService



@lru_cache(maxsize=1)
def make_pdf_parser_service() -> PDFParserService:
    """Factory function to create a cached instance of PDFParserService."""
    settings = {"pdf_parser_max_pages": 30,
                "pdf_parser_max_size_mb": 20,
                "pdf_parser_do_ocr": False,
                "pdf_parser_do_table_structure": True}
    
    return PDFParserService(
        max_pages=settings["pdf_parser_max_pages"],
        max_size_mb=settings["pdf_parser_max_size_mb"],
        do_ocr=settings["pdf_parser_do_ocr"],
        do_table_structure=settings["pdf_parser_do_table_structure"],
    )

def reset_pdf_parser_service_cache():
    """Function to clear the cached PDFParserService instance."""
    make_pdf_parser_service.cache_clear()