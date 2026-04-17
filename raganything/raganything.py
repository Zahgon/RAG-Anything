"""
Complete document parsing + multimodal content insertion Pipeline

This script integrates:
1. Document parsing (using configurable parsers)
2. Pure text content LightRAG insertion
3. Specialized processing for multimodal content (using different processors)
"""

import os
from typing import Dict, Any, Optional, Callable
import sys
import asyncio
import atexit
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

# Add project root directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file BEFORE importing LightRAG
# This is critical for TIKTOKEN_CACHE_DIR to work properly in offline environments
# The OS environment variables take precedence over the .env file
load_dotenv(dotenv_path=".env", override=False)

from lightrag import LightRAG
from lightrag.utils import logger

# Import configuration and modules
from raganything.config import RAGAnythingConfig
from raganything.query import QueryMixin
from raganything.processor import ProcessorMixin
from raganything.batch import BatchMixin
from raganything.utils import get_processor_supports
from raganything.parser import MineruParser, SUPPORTED_PARSERS, get_parser
from raganything.callbacks import CallbackManager

# Import specialized processors
from raganything.modalprocessors import (
    ImageModalProcessor,
    TableModalProcessor,
    EquationModalProcessor,
    GenericModalProcessor,
    ContextExtractor,
    ContextConfig,
)


@dataclass
class RAGAnything(QueryMixin, ProcessorMixin, BatchMixin):
    """Multimodal Document Processing Pipeline - Complete document parsing and insertion pipeline"""

    # Core Components
    # ---
    lightrag: Optional[LightRAG] = field(default=None)
    """Optional pre-initialized LightRAG instance."""

    llm_model_func: Optional[Callable] = field(default=None)
    """LLM model function for text analysis."""

    vision_model_func: Optional[Callable] = field(default=None)
    """Vision model function for image analysis."""

    embedding_func: Optional[Callable] = field(default=None)
    """Embedding function for text vectorization."""

    config: Optional[RAGAnythingConfig] = field(default=None)
    """Configuration object, if None will create with environment variables."""

    # LightRAG Configuration
    # ---
    lightrag_kwargs: Dict[str, Any] = field(default_factory=dict)
    """Additional keyword arguments for LightRAG initialization when lightrag is not provided.
    This allows passing all LightRAG configuration parameters like:
    - kv_storage, vector_storage, graph_storage, doc_status_storage
    - top_k, chunk_top_k, max_entity_tokens, max_relation_tokens, max_total_tokens
    - cosine_threshold, related_chunk_number
    - chunk_token_size, chunk_overlap_token_size, tokenizer, tiktoken_model_name
    - embedding_batch_num, embedding_func_max_async, embedding_cache_config
    - llm_model_name, llm_model_max_token_size, llm_model_max_async, llm_model_kwargs
    - rerank_model_func, vector_db_storage_cls_kwargs, enable_llm_cache
    - max_parallel_insert, max_graph_nodes, addon_params, etc.
    """

    # Internal State
    # ---
    modal_processors: Dict[str, Any] = field(default_factory=dict, init=False)
    """Dictionary of multimodal processors."""

    context_extractor: Optional[ContextExtractor] = field(default=None, init=False)
    """Context extractor for providing surrounding content to modal processors."""

    parse_cache: Optional[Any] = field(default=None, init=False)
    """Parse result cache storage using LightRAG KV storage."""

    callback_manager: CallbackManager = field(
        default_factory=CallbackManager, init=False, repr=False
    )
    """Processing callbacks manager (optional hooks for observability and metrics)."""

    _parser_installation_checked: bool = field(default=False, init=False)
    """Flag to track if parser installation has been checked."""

    def __post_init__(self):
        """Post-initialization setup following LightRAG pattern"""
        # Initialize configuration if not provided
        if self.config is None:
            self.config = RAGAnythingConfig()

        # Set working directory
        self.working_dir = self.config.working_dir

        # Set up logger (use existing logger, don't configure it)
        self.logger = logger

        # Set up document parser
        self.doc_parser = get_parser(self.config.parser)

        # Register close method for cleanup
        atexit.register(self.close)

        # Create working directory if needed
        if not os.path.exists(self.working_dir):
            os.makedirs(self.working_dir)
            self.logger.info(f"Created working directory: {self.working_dir}")

        # Log configuration info
        self.logger.info("RAGAnything initialized with config:")
        self.logger.info(f"  Working directory: {self.config.working_dir}")
        self.logger.info(f"  Parser: {self.config.parser}")
        self.logger.info(f"  Parse method: {self.config.parse_method}")
        self.logger.info(
            f"  Multimodal processing - Image: {self.config.enable_image_processing}, "
            f"Table: {self.config.enable_table_processing}, "
            f"Equation: {self.config.enable_equation_processing}"
        )
        self.logger.info(f"  Max concurrent files: {self.config.max_concurrent_files}")

    def close(self):
        """Cleanup resources when object is destroyed.

        Handles three common scenarios:
        1. Inside a running async context (e.g., FastAPI shutdown) -> schedule task
        2. No event loop in thread (typical atexit) -> create one with asyncio.run()
        3. Event loop exists but is closed/closing (atexit race) -> create new loop
        """
        pass

    def _create_context_config(self) -> ContextConfig:
        """Create context configuration from RAGAnything config"""
        pass

    def _create_context_extractor(self) -> ContextExtractor:
        """Create context extractor with tokenizer from LightRAG"""
        pass

    def _initialize_processors(self):
        """Initialize multimodal processors with appropriate model functions"""
        pass

    def update_config(self, **kwargs):
        """Update configuration with new values"""
        pass

    async def _ensure_lightrag_initialized(self):
        """Ensure LightRAG instance is initialized, create if necessary"""
        pass

    async def finalize_storages(self):
        """Finalize all storages including parse cache and LightRAG storages

        This method should be called when shutting down to properly clean up resources
        and persist any cached data. It will finalize both the parse cache and LightRAG's
        internal storages.

        Example usage:
            try:
                rag_anything = RAGAnything(...)
                await rag_anything.process_file("document.pdf")
                # ... other operations ...
            finally:
                # Always finalize storages to clean up resources
                if rag_anything:
                    await rag_anything.finalize_storages()

        Note:
            - This method is automatically called in __del__ when the object is destroyed
            - Manual calling is recommended in production environments
            - All finalization tasks run concurrently for better performance
        """
        pass

    def check_parser_installation(self) -> bool:
        """
        Check if the configured parser is properly installed

        Returns:
            bool: True if the configured parser is properly installed
        """
        pass

    def verify_parser_installation_once(self) -> bool:
        pass

    def get_config_info(self) -> Dict[str, Any]:
        """Get current configuration information"""
        pass

    def set_content_source_for_context(
        self, content_source, content_format: str = "auto"
    ):
        """Set content source for context extraction in all modal processors

        Args:
            content_source: Source content for context extraction (e.g., MinerU content list)
            content_format: Format of content source ("minerU", "text_chunks", "auto")
        """
        pass

    def update_context_config(self, **context_kwargs):
        """Update context extraction configuration

        Args:
            **context_kwargs: Context configuration parameters to update
                (context_window, context_mode, max_context_tokens, etc.)
        """
        pass

    def get_processor_info(self) -> Dict[str, Any]:
        """Get processor information"""
        pass
