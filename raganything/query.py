"""
Query functionality for RAGAnything

Contains all query-related methods for both text and multimodal queries
"""

import json
import hashlib
import re
import time
from typing import Dict, List, Any
from pathlib import Path
from lightrag import QueryParam
from lightrag.utils import always_get_an_event_loop
from raganything.prompt import PROMPTS
from raganything.utils import (
    get_processor_for_type,
    encode_image_to_base64,
    validate_image_file,
)


class QueryMixin:
    """QueryMixin class containing query functionality for RAGAnything"""

    def _generate_multimodal_cache_key(
        self, query: str, multimodal_content: List[Dict[str, Any]], mode: str, **kwargs
    ) -> str:
        """
        Generate cache key for multimodal query

        Args:
            query: Base query text
            multimodal_content: List of multimodal content
            mode: Query mode
            **kwargs: Additional parameters

        Returns:
            str: Cache key hash
        """
        pass

    async def aquery(
        self, query: str, mode: str = "mix", system_prompt: str | None = None, **kwargs
    ) -> str:
        """
        Pure text query - directly calls LightRAG's query functionality

        Args:
            query: Query text
            mode: Query mode ("local", "global", "hybrid", "naive", "mix", "bypass")
            system_prompt: Optional system prompt to include.
            **kwargs: Other query parameters, will be passed to QueryParam
                - vlm_enhanced: bool, default True when vision_model_func is available.
                  If True, will parse image paths in retrieved context and replace them
                  with base64 encoded images for VLM processing.

        Returns:
            str: Query result
        """
        pass

    async def aquery_with_multimodal(
        self,
        query: str,
        multimodal_content: List[Dict[str, Any]] = None,
        mode: str = "mix",
        **kwargs,
    ) -> str:
        """
        Multimodal query - combines text and multimodal content for querying

        Args:
            query: Base query text
            multimodal_content: List of multimodal content, each element contains:
                - type: Content type ("image", "table", "equation", etc.)
                - Other fields depend on type (e.g., img_path, table_data, latex, etc.)
            mode: Query mode ("local", "global", "hybrid", "naive", "mix", "bypass")
            **kwargs: Other query parameters, will be passed to QueryParam

        Returns:
            str: Query result

        Examples:
            # Pure text query
            result = await rag.query_with_multimodal("What is machine learning?")

            # Image query
            result = await rag.query_with_multimodal(
                "Analyze the content in this image",
                multimodal_content=[{
                    "type": "image",
                    "img_path": "./image.jpg"
                }]
            )

            # Table query
            result = await rag.query_with_multimodal(
                "Analyze the data trends in this table",
                multimodal_content=[{
                    "type": "table",
                    "table_data": "Name,Age\nAlice,25\nBob,30"
                }]
            )
        """
        pass

    async def aquery_vlm_enhanced(
        self,
        query: str,
        mode: str = "mix",
        system_prompt: str | None = None,
        extra_safe_dirs: List[str] = None,
        **kwargs,
    ) -> str:
        """
        VLM enhanced query - replaces image paths in retrieved context with base64 encoded images for VLM processing

        Args:
            query: User query
            mode: Underlying LightRAG query mode
            system_prompt: Optional system prompt to include
            extra_safe_dirs: Optional list of additional safe directories to allow images from
            **kwargs: Other query parameters

        Returns:
            str: VLM query result
        """
        pass

    async def _process_multimodal_query_content(
        self, base_query: str, multimodal_content: List[Dict[str, Any]]
    ) -> str:
        """
        Process multimodal query content to generate enhanced query text

        Args:
            base_query: Base query text
            multimodal_content: List of multimodal content

        Returns:
            str: Enhanced query text
        """
        pass

    async def _generate_query_content_description(
        self, processor, content: Dict[str, Any], content_type: str
    ) -> str:
        """
        Generate content description for query

        Args:
            processor: Multimodal processor
            content: Content data
            content_type: Content type

        Returns:
            str: Content description
        """
        pass

    async def _describe_image_for_query(
        self, processor, content: Dict[str, Any]
    ) -> str:
        """Generate image description for query"""
        pass

    async def _describe_table_for_query(
        self, processor, content: Dict[str, Any]
    ) -> str:
        """Generate table description for query"""
        pass

    async def _describe_equation_for_query(
        self, processor, content: Dict[str, Any]
    ) -> str:
        """Generate equation description for query"""
        pass

    async def _describe_generic_for_query(
        self, processor, content: Dict[str, Any], content_type: str
    ) -> str:
        """Generate generic content description for query"""
        pass

    async def _process_image_paths_for_vlm(
        self, prompt: str, extra_safe_dirs: List[str] = None
    ) -> tuple[str, int]:
        """
        Process image paths in prompt, keeping original paths and adding VLM markers

        Args:
            prompt: Original prompt
            extra_safe_dirs: Optional list of additional safe directories

        Returns:
            tuple: (processed prompt, image count)
        """
        pass

    def _build_vlm_messages_with_images(
        self, enhanced_prompt: str, user_query: str, system_prompt: str
    ) -> List[Dict]:
        """
        Build VLM message format, using markers to correspond images with text positions

        Args:
            enhanced_prompt: Enhanced prompt with image markers
            user_query: User query

        Returns:
            List[Dict]: VLM message format
        """
        pass

    async def _call_vlm_with_multimodal_content(self, messages: List[Dict]) -> str:
        """
        Call VLM to process multimodal content

        Args:
            messages: VLM message format

        Returns:
            str: VLM response result
        """
        pass

    # Synchronous versions of query methods
    def query(self, query: str, mode: str = "mix", **kwargs) -> str:
        """
        Synchronous version of pure text query

        Args:
            query: Query text
            mode: Query mode ("local", "global", "hybrid", "naive", "mix", "bypass")
            **kwargs: Other query parameters, will be passed to QueryParam
                - vlm_enhanced: bool, default True when vision_model_func is available.
                  If True, will parse image paths in retrieved context and replace them
                  with base64 encoded images for VLM processing.

        Returns:
            str: Query result
        """
        pass

    def query_with_multimodal(
        self,
        query: str,
        multimodal_content: List[Dict[str, Any]] = None,
        mode: str = "mix",
        **kwargs,
    ) -> str:
        """
        Synchronous version of multimodal query

        Args:
            query: Base query text
            multimodal_content: List of multimodal content, each element contains:
                - type: Content type ("image", "table", "equation", etc.)
                - Other fields depend on type (e.g., img_path, table_data, latex, etc.)
            mode: Query mode ("local", "global", "hybrid", "naive", "mix", "bypass")
            **kwargs: Other query parameters, will be passed to QueryParam

        Returns:
            str: Query result
        """
        pass
