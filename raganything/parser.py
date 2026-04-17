# type: ignore
"""
Generic Document Parser Utility

This module provides functionality for parsing documents using the built-in
MinerU, Docling, and PaddleOCR parsers, and exposes a small registry for
**in-process** custom parsers (see :func:`register_parser`).

Important notes:

- The custom parser registry is primarily intended for Python usage, where your
  application imports a parser implementation and calls :func:`register_parser`
  before invoking RAGAnything APIs.
- The standalone CLI (``python -m raganything.parser`` or the installed console
  script) does **not** perform automatic plugin discovery; it will only see
  custom parsers that have already been registered in the current process
  (for example via a wrapper script or :mod:`sitecustomize`).

MinerU 2.0 no longer includes LibreOffice document conversion module.
For Office documents (.doc, .docx, .ppt, .pptx), please convert them to PDF
format first.
"""

from __future__ import annotations


import os
import hashlib
import json
import argparse
import base64
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import (
    Dict,
    List,
    Optional,
    Union,
    Tuple,
    Any,
    Iterator,
    TypeVar,
)

T = TypeVar("T")


class MineruExecutionError(Exception):
    """catch mineru error"""

    def __init__(self, return_code, error_msg):
        self.return_code = return_code
        self.error_msg = error_msg
        super().__init__(
            f"Mineru command failed with return code {return_code}: {error_msg}"
        )


class Parser:
    """
    Base class for document parsing utilities.

    Defines common functionality and constants for parsing different document types.
    """

    # Define common file formats
    OFFICE_FORMATS = {".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx"}
    IMAGE_FORMATS = {".png", ".jpeg", ".jpg", ".bmp", ".tiff", ".tif", ".gif", ".webp"}
    TEXT_FORMATS = {".txt", ".md"}

    # Class-level logger
    logger = logging.getLogger(__name__)

    def __init__(self) -> None:
        """Initialize the base parser."""
        pass

    @staticmethod
    def _unique_output_dir(
        base_dir: Union[str, Path], file_path: Union[str, Path]
    ) -> Path:
        """Create a unique output subdirectory for a file to prevent same-name collisions.

        When multiple files share the same name (e.g. dir1/paper.pdf and dir2/paper.pdf),
        their parser output would collide in the same output directory. This creates a
        unique subdirectory by appending a short hash of the file's absolute path. (Fixes #51)

        Args:
            base_dir: The base output directory
            file_path: Path to the input file

        Returns:
            Path like base_dir/paper_a1b2c3d4/ unique per absolute file path.
        """
        pass

    @classmethod
    def convert_office_to_pdf(
        cls, doc_path: Union[str, Path], output_dir: Optional[str] = None
    ) -> Path:
        """
        Convert Office document (.doc, .docx, .ppt, .pptx, .xls, .xlsx) to PDF.
        Requires LibreOffice to be installed.

        Args:
            doc_path: Path to the Office document file
            output_dir: Output directory for the PDF file

        Returns:
            Path to the generated PDF file
        """
        pass

    @classmethod
    def convert_text_to_pdf(
        cls, text_path: Union[str, Path], output_dir: Optional[str] = None
    ) -> Path:
        """
        Convert text file (.txt, .md) to PDF using ReportLab with full markdown support.

        Args:
            text_path: Path to the text file
            output_dir: Output directory for the PDF file

        Returns:
            Path to the generated PDF file
        """
        pass

    @classmethod
    def _process_inline_markdown(cls, text: str) -> str:
        """
        Process inline markdown formatting (bold, italic, code, links)

        Args:
            text: Raw text with markdown formatting

        Returns:
            Text with ReportLab markup
        """
        pass

    def parse_pdf(
        self,
        pdf_path: Union[str, Path],
        output_dir: Optional[str] = None,
        method: str = "auto",
        lang: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Abstract method to parse PDF document.
        Must be implemented by subclasses.

        Args:
            pdf_path: Path to the PDF file
            output_dir: Output directory path
            method: Parsing method (auto, txt, ocr)
            lang: Document language for OCR optimization
            **kwargs: Additional parameters for parser-specific command

        Returns:
            List[Dict[str, Any]]: List of content blocks
        """
        raise NotImplementedError("parse_pdf must be implemented by subclasses")

    def parse_image(
        self,
        image_path: Union[str, Path],
        output_dir: Optional[str] = None,
        lang: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Abstract method to parse image document.
        Must be implemented by subclasses.

        Note: Different parsers may support different image formats.
        Check the specific parser's documentation for supported formats.

        Args:
            image_path: Path to the image file
            output_dir: Output directory path
            lang: Document language for OCR optimization
            **kwargs: Additional parameters for parser-specific command

        Returns:
            List[Dict[str, Any]]: List of content blocks
        """
        raise NotImplementedError("parse_image must be implemented by subclasses")

    def parse_document(
        self,
        file_path: Union[str, Path],
        method: str = "auto",
        output_dir: Optional[str] = None,
        lang: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Abstract method to parse a document.
        Must be implemented by subclasses.

        Args:
            file_path: Path to the file to be parsed
            method: Parsing method (auto, txt, ocr)
            output_dir: Output directory path
            lang: Document language for OCR optimization
            **kwargs: Additional parameters for parser-specific command

        Returns:
            List[Dict[str, Any]]: List of content blocks
        """
        raise NotImplementedError("parse_document must be implemented by subclasses")

    def check_installation(self) -> bool:
        """
        Abstract method to check if the parser is properly installed.
        Must be implemented by subclasses.

        Returns:
            bool: True if installation is valid, False otherwise
        """
        raise NotImplementedError(
            "check_installation must be implemented by subclasses"
        )


class MineruParser(Parser):
    """
    MinerU 2.0 document parsing utility class

    Supports parsing PDF and image documents, converting the content into structured data
    and generating markdown and JSON output.

    Note: Office documents are no longer directly supported. Please convert them to PDF first.
    """

    __slots__ = ()

    # Class-level logger
    logger = logging.getLogger(__name__)

    def __init__(self) -> None:
        """Initialize MineruParser"""
        super().__init__()

    @classmethod
    def _run_mineru_command(
        cls,
        input_path: Union[str, Path],
        output_dir: Union[str, Path],
        method: str = "auto",
        lang: Optional[str] = None,
        backend: Optional[str] = None,
        start_page: Optional[int] = None,
        end_page: Optional[int] = None,
        formula: bool = True,
        table: bool = True,
        device: Optional[str] = None,
        source: Optional[str] = None,
        vlm_url: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        Run mineru command line tool

        Args:
            input_path: Path to input file or directory
            output_dir: Output directory path
            method: Parsing method (auto, txt, ocr)
            lang: Document language for OCR optimization
            backend: Parsing backend
            start_page: Starting page number (0-based)
            end_page: Ending page number (0-based)
            formula: Enable formula parsing
            table: Enable table parsing
            device: Inference device
            source: Model source
            vlm_url: When the backend is `vlm-http-client`, you need to specify the server_url
            **kwargs: Additional parameters for subprocess (e.g., env)
        """
        pass

    @classmethod
    def _read_output_files(
        cls, output_dir: Path, file_stem: str, method: str = "auto"
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Read the output files generated by mineru

        Args:
            output_dir: Output directory
            file_stem: File name without extension
            method: Parsing method (used as fallback if subdirectory scan fails)

        Returns:
            Tuple containing (content list JSON, Markdown text)
        """
        pass

    def parse_pdf(
        self,
        pdf_path: Union[str, Path],
        output_dir: Optional[str] = None,
        method: str = "auto",
        lang: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Parse PDF document using MinerU 2.0

        Args:
            pdf_path: Path to the PDF file
            output_dir: Output directory path
            method: Parsing method (auto, txt, ocr)
            lang: Document language for OCR optimization
            **kwargs: Additional parameters for mineru command

        Returns:
            List[Dict[str, Any]]: List of content blocks
        """
        pass

    def parse_image(
        self,
        image_path: Union[str, Path],
        output_dir: Optional[str] = None,
        lang: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Parse image document using MinerU 2.0

        Note: MinerU 2.0 natively supports .png, .jpeg, .jpg formats.
        Other formats (.bmp, .tiff, .tif, etc.) will be automatically converted to .png.

        Args:
            image_path: Path to the image file
            output_dir: Output directory path
            lang: Document language for OCR optimization
            **kwargs: Additional parameters for mineru command

        Returns:
            List[Dict[str, Any]]: List of content blocks
        """
        pass

    def parse_office_doc(
        self,
        doc_path: Union[str, Path],
        output_dir: Optional[str] = None,
        lang: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Parse office document by first converting to PDF, then parsing with MinerU 2.0

        Note: This method requires LibreOffice to be installed separately for PDF conversion.
        MinerU 2.0 no longer includes built-in Office document conversion.

        Supported formats: .doc, .docx, .ppt, .pptx, .xls, .xlsx

        Args:
            doc_path: Path to the document file (.doc, .docx, .ppt, .pptx, .xls, .xlsx)
            output_dir: Output directory path
            lang: Document language for OCR optimization
            **kwargs: Additional parameters for mineru command

        Returns:
            List[Dict[str, Any]]: List of content blocks
        """
        pass

    def parse_text_file(
        self,
        text_path: Union[str, Path],
        output_dir: Optional[str] = None,
        lang: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Parse text file by first converting to PDF, then parsing with MinerU 2.0

        Supported formats: .txt, .md

        Args:
            text_path: Path to the text file (.txt, .md)
            output_dir: Output directory path
            lang: Document language for OCR optimization
            **kwargs: Additional parameters for mineru command

        Returns:
            List[Dict[str, Any]]: List of content blocks
        """
        pass

    def parse_document(
        self,
        file_path: Union[str, Path],
        method: str = "auto",
        output_dir: Optional[str] = None,
        lang: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Parse document using MinerU 2.0 based on file extension

        Args:
            file_path: Path to the file to be parsed
            method: Parsing method (auto, txt, ocr)
            output_dir: Output directory path
            lang: Document language for OCR optimization
            **kwargs: Additional parameters for mineru command

        Returns:
            List[Dict[str, Any]]: List of content blocks
        """
        pass

    def check_installation(self) -> bool:
        """
        Check if MinerU 2.0 is properly installed

        Returns:
            bool: True if installation is valid, False otherwise
        """
        pass


class DoclingParser(Parser):
    """
    Docling document parsing utility class.

    Specialized in parsing Office documents and HTML files, converting the content
    into structured data and generating markdown and JSON output.
    """

    # Define Docling-specific formats
    HTML_FORMATS = {".html", ".htm", ".xhtml"}

    def __init__(self) -> None:
        """Initialize DoclingParser"""
        super().__init__()

    def parse_pdf(
        self,
        pdf_path: Union[str, Path],
        output_dir: Optional[str] = None,
        method: str = "auto",
        lang: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Parse PDF document using Docling

        Args:
            pdf_path: Path to the PDF file
            output_dir: Output directory path
            method: Parsing method (auto, txt, ocr)
            lang: Document language for OCR optimization
            **kwargs: Additional parameters for docling command

        Returns:
            List[Dict[str, Any]]: List of content blocks
        """
        pass

    def parse_document(
        self,
        file_path: Union[str, Path],
        method: str = "auto",
        output_dir: Optional[str] = None,
        lang: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Parse document using Docling based on file extension

        Args:
            file_path: Path to the file to be parsed
            method: Parsing method
            output_dir: Output directory path
            lang: Document language for optimization
            **kwargs: Additional parameters for docling command

        Returns:
            List[Dict[str, Any]]: List of content blocks
        """
        pass

    def _run_docling_command(
        self,
        input_path: Union[str, Path],
        output_dir: Union[str, Path],
        file_stem: str,
        **kwargs,
    ) -> None:
        """
        Run docling command line tool

        Args:
            input_path: Path to input file or directory
            output_dir: Output directory path
            file_stem: File stem for creating subdirectory
            **kwargs: Additional parameters for docling command
        """
        pass

    def _read_output_files(
        self,
        output_dir: Path,
        file_stem: str,
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Read the output files generated by docling and convert to MinerU format

        Args:
            output_dir: Output directory
            file_stem: File name without extension

        Returns:
            Tuple containing (content list JSON, Markdown text)
        """
        pass

    def read_from_block_recursive(
        self,
        block,
        type: str,
        output_dir: Path,
        cnt: int,
        num: str,
        docling_content: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        pass

    def read_from_block(
        self, block, type: str, output_dir: Path, cnt: int, num: str
    ) -> Dict[str, Any]:
        pass

    def parse_office_doc(
        self,
        doc_path: Union[str, Path],
        output_dir: Optional[str] = None,
        lang: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Parse office document directly using Docling

        Supported formats: .doc, .docx, .ppt, .pptx, .xls, .xlsx

        Args:
            doc_path: Path to the document file
            output_dir: Output directory path
            lang: Document language for optimization
            **kwargs: Additional parameters for docling command

        Returns:
            List[Dict[str, Any]]: List of content blocks
        """
        pass

    def parse_html(
        self,
        html_path: Union[str, Path],
        output_dir: Optional[str] = None,
        lang: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Parse HTML document using Docling

        Supported formats: .html, .htm, .xhtml

        Args:
            html_path: Path to the HTML file
            output_dir: Output directory path
            lang: Document language for optimization
            **kwargs: Additional parameters for docling command

        Returns:
            List[Dict[str, Any]]: List of content blocks
        """
        pass

    def check_installation(self) -> bool:
        """
        Check if Docling is properly installed

        Returns:
            bool: True if installation is valid, False otherwise
        """
        pass


class PaddleOCRParser(Parser):
    """PaddleOCR document parser with optional PDF page rendering support."""

    def __init__(self, default_lang: str = "en") -> None:
        super().__init__()
        self.default_lang = default_lang
        self._ocr_instances: Dict[str, Any] = {}

    def _require_paddleocr(self):
        pass

    def _get_ocr(self, lang: Optional[str] = None):
        pass

    def _extract_text_lines(self, result: Any) -> List[str]:
        pass

    def _ocr_input(
        self, input_data: Any, lang: Optional[str] = None, cls_enabled: bool = True
    ) -> List[str]:
        pass

    def _extract_pdf_page_inputs(self, pdf_path: Path) -> Iterator[Tuple[int, Any]]:
        pass

    def _ocr_rendered_page(
        self, rendered_page: Any, lang: Optional[str] = None, cls_enabled: bool = True
    ) -> List[str]:
        pass

    def parse_pdf(
        self,
        pdf_path: Union[str, Path],
        output_dir: Optional[str] = None,
        method: str = "auto",
        lang: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        pass

    def parse_image(
        self,
        image_path: Union[str, Path],
        output_dir: Optional[str] = None,
        lang: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        pass

    def parse_office_doc(
        self,
        doc_path: Union[str, Path],
        output_dir: Optional[str] = None,
        lang: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        pass

    def parse_text_file(
        self,
        text_path: Union[str, Path],
        output_dir: Optional[str] = None,
        lang: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        pass

    def parse_document(
        self,
        file_path: Union[str, Path],
        method: str = "auto",
        output_dir: Optional[str] = None,
        lang: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        pass

    def check_installation(self) -> bool:
        pass


def _normalize_parser_name(name: str) -> str:
    """Normalize and validate a parser name for registry APIs."""
    pass


# Custom parser registry for Bring-Your-Own-Parser support (see #151)
_CUSTOM_PARSERS: Dict[str, type] = {}


def register_parser(name: str, parser_class: type) -> None:
    """Register a custom parser class for use with RAGAnything.

    This enables the Bring-Your-Own-Parser pattern: users can integrate
    any document parser (e.g., Marker, Unstructured, Surya) by subclassing
    ``Parser`` and registering it here.

    Args:
        name: Unique identifier for the parser (e.g., "marker", "surya").
              Must not collide with built-in names ("mineru", "docling", "paddleocr").
        parser_class: A subclass of ``Parser`` that implements at least
                      ``parse_document``, ``check_installation``, and
                      optionally ``parse_pdf``, ``parse_image``, ``parse_office_doc``.

    Raises:
        TypeError: If *parser_class* is not a subclass of ``Parser``.
        ValueError: If *name* collides with a built-in parser name.

    Example::

        from raganything.parser import Parser, register_parser

        class MarkerParser(Parser):
            def check_installation(self) -> bool:
                try:
                    import marker
                    return True
                except ImportError:
                    return False

            def parse_pdf(self, pdf_path, output_dir="./output", method="auto", **kw):
                import marker
                # ... your implementation ...
                return content_list

            def parse_document(self, file_path, output_dir="./output", method="auto", **kw):
                return self.parse_pdf(pdf_path=file_path, output_dir=output_dir, method=method, **kw)

        register_parser("marker", MarkerParser)
    """
    pass


def unregister_parser(name: str) -> None:
    """Remove a previously registered custom parser.

    Args:
        name: The parser name to remove.

    Raises:
        TypeError: If *name* is not a string.
        ValueError: If *name* is empty or only whitespace.
        KeyError: If no custom parser with that name is registered.
    """
    pass


def list_parsers() -> Dict[str, str]:
    """Return a mapping of all available parser names to their class names.

    Returns:
        Dict mapping parser name to the fully-qualified class name.
        Includes both built-in and custom parsers.
    """
    pass


SUPPORTED_PARSERS = ("mineru", "docling", "paddleocr")


def get_supported_parsers() -> tuple:
    """Return all supported parser names including custom registered parsers."""
    pass


def get_parser(parser_type: str) -> Parser:
    """Get a parser instance by name.

    Checks built-in parsers first, then falls back to the custom parser
    registry populated via :func:`register_parser`.

    Args:
        parser_type: Parser name (e.g., "mineru", "docling", "paddleocr",
                     or any custom registered name).

    Returns:
        An instance of the requested parser.

    Raises:
        ValueError: If the parser name is not recognized.
    """
    pass


def main():
    """
    Main function to run the document parser from command line
    """
    pass


if __name__ == "__main__":
    exit(main())
