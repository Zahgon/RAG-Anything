"""
Batch processing functionality for RAGAnything

Contains methods for processing multiple documents in batch mode
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, TYPE_CHECKING
import time

from .batch_parser import BatchParser, BatchProcessingResult

if TYPE_CHECKING:
    from .config import RAGAnythingConfig


class BatchMixin:
    """BatchMixin class containing batch processing functionality for RAGAnything"""

    # Type hints for mixin attributes (will be available when mixed into RAGAnything)
    config: "RAGAnythingConfig"
    logger: logging.Logger

    # Type hints for methods that will be available from other mixins
    async def _ensure_lightrag_initialized(self) -> None: ...
    async def process_document_complete(self, file_path: str, **kwargs) -> None: ...

    # ==========================================
    # ORIGINAL BATCH PROCESSING METHOD (RESTORED)
    # ==========================================

    async def process_folder_complete(
        self,
        folder_path: str,
        output_dir: str = None,
        parse_method: str = None,
        display_stats: bool = None,
        split_by_character: str | None = None,
        split_by_character_only: bool = False,
        file_extensions: Optional[List[str]] = None,
        recursive: bool = None,
        max_workers: int = None,
    ):
        """
        Process all supported files in a folder

        Args:
            folder_path: Path to the folder containing files to process
            output_dir: Directory for parsed outputs (optional)
            parse_method: Parsing method to use (optional)
            display_stats: Whether to display statistics (optional)
            split_by_character: Character to split by (optional)
            split_by_character_only: Whether to split only by character (optional)
            file_extensions: List of file extensions to process (optional)
            recursive: Whether to process folders recursively (optional)
            max_workers: Maximum number of workers for concurrent processing (optional)
        """
        pass

    # ==========================================
    # NEW ENHANCED BATCH PROCESSING METHODS
    # ==========================================

    def process_documents_batch(
        self,
        file_paths: List[str],
        output_dir: Optional[str] = None,
        parse_method: Optional[str] = None,
        max_workers: Optional[int] = None,
        recursive: Optional[bool] = None,
        show_progress: bool = True,
        **kwargs,
    ) -> BatchProcessingResult:
        """
        Process multiple documents in batch using the new BatchParser

        Args:
            file_paths: List of file paths or directories to process
            output_dir: Output directory for parsed files
            parse_method: Parsing method to use
            max_workers: Maximum number of workers for parallel processing
            recursive: Whether to process directories recursively
            show_progress: Whether to show progress bar
            **kwargs: Additional arguments passed to the parser

        Returns:
            BatchProcessingResult: Results of the batch processing
        """
        pass

    async def process_documents_batch_async(
        self,
        file_paths: List[str],
        output_dir: Optional[str] = None,
        parse_method: Optional[str] = None,
        max_workers: Optional[int] = None,
        recursive: Optional[bool] = None,
        show_progress: bool = True,
        **kwargs,
    ) -> BatchProcessingResult:
        """
        Asynchronously process multiple documents in batch

        Args:
            file_paths: List of file paths or directories to process
            output_dir: Output directory for parsed files
            parse_method: Parsing method to use
            max_workers: Maximum number of workers for parallel processing
            recursive: Whether to process directories recursively
            show_progress: Whether to show progress bar
            **kwargs: Additional arguments passed to the parser

        Returns:
            BatchProcessingResult: Results of the batch processing
        """
        pass

    def get_supported_file_extensions(self) -> List[str]:
        """Get list of supported file extensions for batch processing"""
        pass

    def filter_supported_files(
        self, file_paths: List[str], recursive: Optional[bool] = None
    ) -> List[str]:
        """
        Filter file paths to only include supported file types

        Args:
            file_paths: List of file paths to filter
            recursive: Whether to process directories recursively

        Returns:
            List of supported file paths
        """
        pass

    async def process_documents_with_rag_batch(
        self,
        file_paths: List[str],
        output_dir: Optional[str] = None,
        parse_method: Optional[str] = None,
        max_workers: Optional[int] = None,
        recursive: Optional[bool] = None,
        show_progress: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Process documents in batch and then add them to RAG

        This method combines document parsing and RAG insertion:
        1. First, parse all documents using batch processing
        2. Then, process each successfully parsed document with RAG

        Args:
            file_paths: List of file paths or directories to process
            output_dir: Output directory for parsed files
            parse_method: Parsing method to use
            max_workers: Maximum number of workers for parallel processing
            recursive: Whether to process directories recursively
            show_progress: Whether to show progress bar
            **kwargs: Additional arguments passed to the parser

        Returns:
            Dict containing both parse results and RAG processing results
        """
        pass
