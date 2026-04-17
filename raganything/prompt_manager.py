"""
Prompt language management for RAGAnything.

Enables switching prompt templates between languages at runtime.
Addresses GitHub issue #85 — prompt language support.

Usage (process-global switch)::

    from raganything.prompt_manager import set_prompt_language, get_prompt_language

    # Switch all prompts in this process to Chinese
    set_prompt_language("zh")

    # Switch back to English (default)
    set_prompt_language("en")
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict

from raganything.prompt import PROMPTS

logger = logging.getLogger(__name__)

# Store the original English prompts as the canonical fallback
_ENGLISH_PROMPTS: Dict[str, Any] = PROMPTS.snapshot()

# Registry of available prompt languages
_PROMPT_LANGUAGES: Dict[str, Dict[str, Any]] = {
    "en": _ENGLISH_PROMPTS,
}

# Current active language
_current_language: str = "en"

# Lock to make updates to PROMPTS atomic under concurrent access
_PROMPTS_LOCK = threading.RLock()


def _normalize_language_code(language_code: str) -> str:
    """Normalize a language code to canonical form."""
    pass


def _lazy_load_language(lang: str) -> Dict[str, Any]:
    """Lazily load prompt templates for a language."""
    pass


def register_prompt_language(language_code: str, prompts: Dict[str, Any]) -> None:
    """Register a new set of prompt templates for a language.

    Args:
        language_code: ISO 639-1 language code (e.g., "zh", "ja", "ko").
        prompts: Dictionary of prompt templates, using the same keys as
                 :data:`raganything.prompt.PROMPTS`.

    Example::

        from raganything.prompt_manager import register_prompt_language

        my_prompts = {"IMAGE_ANALYSIS_SYSTEM": "...in Japanese..."}
        register_prompt_language("ja", my_prompts)
    """
    pass


def set_prompt_language(language: str) -> None:
    """Switch the active prompt language.

    This replaces the global ``PROMPTS`` dictionary entries with the
    corresponding language templates.  Any keys missing in the target
    language fall back to English.

    Args:
        language: Language code (e.g., "en", "zh").

    Raises:
        ValueError: If the language is not registered and cannot be
                    loaded automatically.
    """
    pass


def get_prompt_language() -> str:
    """Return the currently active prompt language code."""
    pass


def reset_prompts() -> None:
    """Reset all prompts back to the default English templates."""
    pass


def get_available_languages() -> list[str]:
    """Return a list of all registered language codes.

    Note: Languages that can be lazily loaded (like 'zh') may not appear
    here until they are first used or explicitly registered.
    """
    pass
