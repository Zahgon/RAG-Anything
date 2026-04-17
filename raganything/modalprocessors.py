"""
Specialized processors for different modalities

Includes:
- ContextExtractor: Universal context extraction for multimodal content
- ImageModalProcessor: Specialized processor for image content
- TableModalProcessor: Specialized processor for table content
- EquationModalProcessor: Specialized processor for equation content
- GenericModalProcessor: Processor for other modal content
"""

import re
import json
import time
import base64
from typing import Dict, Any, Tuple, List
from pathlib import Path
from dataclasses import dataclass

from lightrag.utils import (
    logger,
    compute_mdhash_id,
)
from lightrag.lightrag import LightRAG
from dataclasses import asdict
from lightrag.kg.shared_storage import get_namespace_data, get_pipeline_status_lock
from lightrag.operate import extract_entities, merge_nodes_and_edges

# Import prompt templates
from raganything.prompt import PROMPTS


@dataclass
class ContextConfig:
    """Configuration for context extraction"""

    context_window: int = 1  # Window size for context extraction
    context_mode: str = "page"  # "page", "chunk", "token"
    max_context_tokens: int = 2000  # Maximum context tokens
    include_headers: bool = True  # Whether to include headers/titles
    include_captions: bool = True  # Whether to include image/table captions
    filter_content_types: List[str] = None  # Content types to include

    def __post_init__(self):
        if self.filter_content_types is None:
            self.filter_content_types = ["text"]


class ContextExtractor:
    """Universal context extractor supporting multiple content source formats"""

    def __init__(self, config: ContextConfig = None, tokenizer=None):
        """Initialize context extractor

        Args:
            config: Context extraction configuration
            tokenizer: Tokenizer for accurate token counting
        """
        self.config = config or ContextConfig()
        self.tokenizer = tokenizer

    def extract_context(
        self,
        content_source: Any,
        current_item_info: Dict[str, Any],
        content_format: str = "auto",
    ) -> str:
        """Extract context for current item from content source

        Args:
            content_source: Source content (list, dict, or other format)
            current_item_info: Information about current item (page_idx, index, etc.)
            content_format: Format hint for content source ("minerU", "text_chunks", "auto", etc.)

        Returns:
            Extracted context text
        """
        pass

    def _extract_from_content_list(
        self, content_list: List[Dict], current_item_info: Dict
    ) -> str:
        """Extract context from MinerU-style content list

        Args:
            content_list: List of content items with page_idx and type info
            current_item_info: Current item information

        Returns:
            Context text from surrounding pages/chunks
        """
        pass

    def _extract_page_context(
        self, content_list: List[Dict], current_item_info: Dict
    ) -> str:
        """Extract context based on page boundaries

        Args:
            content_list: List of content items
            current_item_info: Current item with page_idx

        Returns:
            Context text from surrounding pages
        """
        pass

    def _extract_chunk_context(
        self, content_list: List[Dict], current_item_info: Dict
    ) -> str:
        """Extract context based on content chunks

        Args:
            content_list: List of content items
            current_item_info: Current item with index info

        Returns:
            Context text from surrounding chunks
        """
        pass

    def _extract_text_from_item(self, item: Dict) -> str:
        """Extract text content from a content item

        Args:
            item: Content item dictionary

        Returns:
            Extracted text content
        """
        pass

    def _extract_from_dict_source(
        self, dict_source: Dict, current_item_info: Dict
    ) -> str:
        """Extract context from dictionary-based content source

        Args:
            dict_source: Dictionary containing content
            current_item_info: Current item information

        Returns:
            Extracted context text
        """
        pass

    def _extract_from_text_source(
        self, text_source: str, current_item_info: Dict
    ) -> str:
        """Extract context from plain text source

        Args:
            text_source: Plain text content
            current_item_info: Current item information

        Returns:
            Truncated text context
        """
        pass

    def _extract_from_text_chunks(
        self, text_chunks: List[str], current_item_info: Dict
    ) -> str:
        """Extract context from simple text chunks list

        Args:
            text_chunks: List of text strings
            current_item_info: Current item information with index

        Returns:
            Context text from surrounding chunks
        """
        pass

    def _truncate_context(self, context: str) -> str:
        """Truncate context to maximum token limit

        Args:
            context: Context text to truncate

        Returns:
            Truncated context text
        """
        pass


class BaseModalProcessor:
    """Base class for modal processors"""

    def __init__(
        self,
        lightrag: LightRAG,
        modal_caption_func,
        context_extractor: ContextExtractor = None,
    ):
        """Initialize base processor

        Args:
            lightrag: LightRAG instance
            modal_caption_func: Function for generating descriptions
            context_extractor: Context extractor instance
        """
        self.lightrag = lightrag
        self.modal_caption_func = modal_caption_func

        # Use LightRAG's storage instances
        self.text_chunks_db = lightrag.text_chunks
        self.chunks_vdb = lightrag.chunks_vdb
        self.entities_vdb = lightrag.entities_vdb
        self.relationships_vdb = lightrag.relationships_vdb
        self.knowledge_graph_inst = lightrag.chunk_entity_relation_graph

        # Use LightRAG's configuration and functions
        self.embedding_func = lightrag.embedding_func
        self.llm_model_func = lightrag.llm_model_func
        self.global_config = asdict(lightrag)
        self.hashing_kv = lightrag.llm_response_cache
        self.tokenizer = lightrag.tokenizer

        # Initialize context extractor with tokenizer if not provided
        if context_extractor is None:
            self.context_extractor = ContextExtractor(tokenizer=self.tokenizer)
        else:
            self.context_extractor = context_extractor
            # Update tokenizer if context_extractor doesn't have one
            if self.context_extractor.tokenizer is None:
                self.context_extractor.tokenizer = self.tokenizer

        # Content source for context extraction
        self.content_source = None
        self.content_format = "auto"

    def set_content_source(self, content_source: Any, content_format: str = "auto"):
        """Set content source for context extraction

        Args:
            content_source: Source content for context extraction
            content_format: Format of content source ("minerU", "text_chunks", "auto")
        """
        pass

    def _get_context_for_item(self, item_info: Dict[str, Any]) -> str:
        """Get context for current processing item

        Args:
            item_info: Information about current item (page_idx, index, etc.)

        Returns:
            Context text for the item
        """
        pass

    async def generate_description_only(
        self,
        modal_content,
        content_type: str,
        item_info: Dict[str, Any] = None,
        entity_name: str = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate text description and entity info only, without entity relation extraction.
        Used for batch processing stage 1.

        Args:
            modal_content: Modal content to process
            content_type: Type of modal content
            item_info: Item information for context extraction
            entity_name: Optional predefined entity name

        Returns:
            Tuple of (description, entity_info)
        """
        # Subclasses must implement this method
        raise NotImplementedError("Subclasses must implement this method")

    async def _create_entity_and_chunk(
        self,
        modal_chunk: str,
        entity_info: Dict[str, Any],
        file_path: str,
        batch_mode: bool = False,
        doc_id: str = None,
        chunk_order_index: int = 0,
    ) -> Tuple[str, Dict[str, Any]]:
        """Create entity and text chunk"""
        pass

    @staticmethod
    def _strip_thinking_tags(text: str) -> str:
        """Remove <think>/<thinking> tags produced by reasoning models.

        Models such as DeepSeek-R1 and Qwen2.5-think wrap their internal
        chain-of-thought in ``<think>…</think>`` or ``<thinking>…</thinking>``
        blocks before emitting the final answer.  When JSON parsing fails and
        the raw LLM response is used as a fallback, storing the entire response
        (including the reasoning preamble) pollutes the knowledge graph with
        internal model thoughts rather than actual content descriptions.

        This helper strips those blocks so that only the final answer text is
        stored or surfaced to callers.
        """
        pass

    def _robust_json_parse(self, response: str) -> dict:
        """Robust JSON parsing with multiple fallback strategies"""
        pass

    def _extract_all_json_candidates(self, response: str) -> list:
        """Extract all possible JSON candidates from response"""
        pass

    def _try_parse_json(self, json_str: str) -> dict:
        """Try to parse JSON string, return None if failed"""
        pass

    def _basic_json_cleanup(self, json_str: str) -> str:
        """Basic cleanup for common JSON issues"""
        pass

    def _progressive_quote_fix(self, json_str: str) -> str:
        """Progressive fixing of quote and escape issues"""
        pass

    def _extract_fields_with_regex(self, response: str) -> dict:
        """Extract required fields using regex as last resort"""
        pass

    def _extract_json_from_response(self, response: str) -> str:
        """Legacy method - now handled by _extract_all_json_candidates"""
        pass

    def _fix_json_escapes(self, json_str: str) -> str:
        """Legacy method - now handled by progressive strategies"""
        pass

    async def _process_chunk_for_extraction(
        self, chunk_id: str, modal_entity_name: str, batch_mode: bool = False
    ):
        """Process chunk for entity and relationship extraction"""
        pass


class ImageModalProcessor(BaseModalProcessor):
    """Processor specialized for image content"""

    def __init__(
        self,
        lightrag: LightRAG,
        modal_caption_func,
        context_extractor: ContextExtractor = None,
    ):
        """Initialize image processor

        Args:
            lightrag: LightRAG instance
            modal_caption_func: Function for generating descriptions (supporting image understanding)
            context_extractor: Context extractor instance
        """
        super().__init__(lightrag, modal_caption_func, context_extractor)

    def _encode_image_to_base64(self, image_path: str) -> str:
        """Encode image to base64"""
        pass

    async def generate_description_only(
        self,
        modal_content,
        content_type: str,
        item_info: Dict[str, Any] = None,
        entity_name: str = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate image description and entity info only, without entity relation extraction.
        Used for batch processing stage 1.

        Args:
            modal_content: Image content to process
            content_type: Type of modal content ("image")
            item_info: Item information for context extraction
            entity_name: Optional predefined entity name

        Returns:
            Tuple of (enhanced_caption, entity_info)
        """
        pass

    async def process_multimodal_content(
        self,
        modal_content,
        content_type: str,
        file_path: str = "manual_creation",
        entity_name: str = None,
        item_info: Dict[str, Any] = None,
        batch_mode: bool = False,
        doc_id: str = None,
        chunk_order_index: int = 0,
    ) -> Tuple[str, Dict[str, Any]]:
        """Process image content with context support"""
        pass

    def _parse_response(
        self, response: str, entity_name: str = None
    ) -> Tuple[str, Dict[str, Any]]:
        """Parse model response"""
        pass


class TableModalProcessor(BaseModalProcessor):
    """Processor specialized for table content"""

    async def generate_description_only(
        self,
        modal_content,
        content_type: str,
        item_info: Dict[str, Any] = None,
        entity_name: str = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate table description and entity info only, without entity relation extraction.
        Used for batch processing stage 1.

        Args:
            modal_content: Table content to process
            content_type: Type of modal content ("table")
            item_info: Item information for context extraction
            entity_name: Optional predefined entity name

        Returns:
            Tuple of (enhanced_caption, entity_info)
        """
        pass

    async def process_multimodal_content(
        self,
        modal_content,
        content_type: str,
        file_path: str = "manual_creation",
        entity_name: str = None,
        item_info: Dict[str, Any] = None,
        batch_mode: bool = False,
        doc_id: str = None,
        chunk_order_index: int = 0,
    ) -> Tuple[str, Dict[str, Any]]:
        """Process table content with context support"""
        pass

    def _parse_table_response(
        self, response: str, entity_name: str = None
    ) -> Tuple[str, Dict[str, Any]]:
        """Parse table analysis response"""
        pass


class EquationModalProcessor(BaseModalProcessor):
    """Processor specialized for equation content"""

    async def generate_description_only(
        self,
        modal_content,
        content_type: str,
        item_info: Dict[str, Any] = None,
        entity_name: str = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate equation description and entity info only, without entity relation extraction.
        Used for batch processing stage 1.

        Args:
            modal_content: Equation content to process
            content_type: Type of modal content ("equation")
            item_info: Item information for context extraction
            entity_name: Optional predefined entity name

        Returns:
            Tuple of (enhanced_caption, entity_info)
        """
        pass

    async def process_multimodal_content(
        self,
        modal_content,
        content_type: str,
        file_path: str = "manual_creation",
        entity_name: str = None,
        item_info: Dict[str, Any] = None,
        batch_mode: bool = False,
        doc_id: str = None,
        chunk_order_index: int = 0,
    ) -> Tuple[str, Dict[str, Any]]:
        """Process equation content with context support"""
        pass

    def _parse_equation_response(
        self, response: str, entity_name: str = None
    ) -> Tuple[str, Dict[str, Any]]:
        """Parse equation analysis response with robust JSON handling"""
        pass


class GenericModalProcessor(BaseModalProcessor):
    """Generic processor for other types of modal content"""

    async def generate_description_only(
        self,
        modal_content,
        content_type: str,
        item_info: Dict[str, Any] = None,
        entity_name: str = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate generic modal description and entity info only, without entity relation extraction.
        Used for batch processing stage 1.

        Args:
            modal_content: Generic modal content to process
            content_type: Type of modal content
            item_info: Item information for context extraction
            entity_name: Optional predefined entity name

        Returns:
            Tuple of (enhanced_caption, entity_info)
        """
        pass

    async def process_multimodal_content(
        self,
        modal_content,
        content_type: str,
        file_path: str = "manual_creation",
        entity_name: str = None,
        item_info: Dict[str, Any] = None,
        batch_mode: bool = False,
        doc_id: str = None,
        chunk_order_index: int = 0,
    ) -> Tuple[str, Dict[str, Any]]:
        """Process generic modal content with context support"""
        pass

    def _parse_generic_response(
        self, response: str, entity_name: str = None, content_type: str = "content"
    ) -> Tuple[str, Dict[str, Any]]:
        """Parse generic analysis response"""
        pass
