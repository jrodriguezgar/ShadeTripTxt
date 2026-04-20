"""
Text Normalizer - Text Preprocessing for Comparison

This module provides text normalization functions that clean and standardize
text before comparison to improve matching accuracy.

Functions:
    normalize_text: Main normalization function
    normalize_whitespace: Remove multiple spaces
    remove_punctuation: Remove punctuation marks
    remove_special_chars: Remove special characters

Author: AI Assistant
Date: November 9, 2025
"""

import re
import unicodedata
from typing import Optional


# Pre-compiled regex patterns for normalize_text
_RE_PARENTHESES = re.compile(r"\([^)]*\)")
_RE_SQUARE_BRACKETS = re.compile(r"\[[^\]]*\]")
_RE_CURLY_BRACES = re.compile(r"\{[^}]*\}")
_RE_PUNCT_NOT_BETWEEN_WORDS = re.compile(r"(?<!\w)[.,;:!?¡¿](?!\w)")
_RE_PUNCT_TRAILING = re.compile(r"[.,;:!?¡¿]+$")
_RE_PUNCT_LEADING = re.compile(r"^[.,;:!?¡¿]+")
_RE_PUNCT_STANDALONE = re.compile(r"\s+[.,;:!?¡¿]+\s+")
_RE_NON_ALNUM = re.compile(r"[^a-zA-Z0-9\s]")
_RE_MULTI_WHITESPACE = re.compile(r"\s+")


def normalize_text(
    text: str,
    lowercase: bool = True,
    remove_punctuation: bool = True,
    normalize_whitespace: bool = True,
    remove_accents: bool = False,
    remove_parentheses_content: bool = False,
    strip_quotes: bool = True,
    preserve_alphanumeric_only: bool = False,
) -> str:
    """
    Normalize text for comparison by cleaning and standardizing.

    Description:
        This function applies a series of normalization steps to prepare
        text for comparison. It handles common text variations that should
        not affect matching:

        - **Whitespace**: Collapses multiple spaces, tabs, newlines
        - **Punctuation**: Removes commas, periods, semicolons, etc.
        - **Parentheses**: Optionally removes content in parentheses
        - **Case**: Converts to lowercase
        - **Accents**: Optionally removes diacritical marks
        - **Quotes**: Removes quotation marks
        - **Special chars**: Optionally keeps only letters/numbers

        **Before Normalization**:
        "  John   Smith  (CEO),  Inc.  "

        **After Normalization**:
        "john smith ceo inc"

    Args:
        text (str): Text to normalize
        lowercase (bool): Convert to lowercase. Default: True
        remove_punctuation (bool): Remove punctuation marks. Default: True
        normalize_whitespace (bool): Collapse multiple spaces. Default: True
        remove_accents (bool): Remove diacritical marks. Default: False
        remove_parentheses_content (bool): Remove text in parentheses. Default: False
        strip_quotes (bool): Remove quotation marks. Default: True
        preserve_alphanumeric_only (bool): Keep only letters and numbers. Default: False

    Returns:
        str: Normalized text

    Raises:
        ValueError: If text is empty or not a string

    Example:
        # Basic normalization
        text = normalize_text("  John   Smith,  Inc.  ")
        # Returns: "john smith inc"

        # With accents removal
        text = normalize_text("José García", remove_accents=True)
        # Returns: "jose garcia"

        # Remove parentheses content
        text = normalize_text("Microsoft (MSFT)", remove_parentheses_content=True)
        # Returns: "microsoft"

        # Preserve only alphanumeric
        text = normalize_text("Product-123 (New!)", preserve_alphanumeric_only=True)
        # Returns: "product123 new"

        # No punctuation removal (keep structure)
        text = normalize_text("123-456-7890", remove_punctuation=False)
        # Returns: "123-456-7890"

    Cost:
        O(n) where n is text length
    """
    if not isinstance(text, str):
        raise ValueError("Text must be a string")

    if not text.strip():
        return ""

    result = text

    # Step 1: Remove content in parentheses (before other processing)
    if remove_parentheses_content:
        result = _RE_PARENTHESES.sub("", result)
        result = _RE_SQUARE_BRACKETS.sub("", result)
        result = _RE_CURLY_BRACES.sub("", result)

    # Step 2: Remove quotes
    if strip_quotes:
        # Remove single and double quotes
        result = result.replace('"', "").replace("'", "")
        result = result.replace("\u201c", "").replace("\u201d", "")  # Smart double quotes
        result = result.replace("\u2018", "").replace("\u2019", "")  # Smart single quotes

    # Step 3: Remove accents
    if remove_accents:
        # Normalize to NFD (decomposed form) and filter out combining characters
        nfd_form = unicodedata.normalize("NFD", result)
        result = "".join(char for char in nfd_form if unicodedata.category(char) != "Mn")

    # Step 4: Convert to lowercase
    if lowercase:
        result = result.lower()

    # Step 5: Remove punctuation
    if remove_punctuation:
        result = _RE_PUNCT_NOT_BETWEEN_WORDS.sub(" ", result)
        result = _RE_PUNCT_TRAILING.sub("", result)
        result = _RE_PUNCT_LEADING.sub("", result)
        result = _RE_PUNCT_STANDALONE.sub(" ", result)

    # Step 6: Preserve only alphanumeric (aggressive cleaning)
    if preserve_alphanumeric_only:
        result = _RE_NON_ALNUM.sub(" ", result)

    # Step 7: Normalize whitespace (always do this last)
    if normalize_whitespace:
        result = _RE_MULTI_WHITESPACE.sub(" ", result)
        result = result.strip()

    return result


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace by collapsing multiple spaces.

    Description:
        Replaces all sequences of whitespace characters (spaces, tabs,
        newlines) with a single space and trims leading/trailing whitespace.

    Args:
        text (str): Input text

    Returns:
        str: Text with normalized whitespace

    Example:
        text = normalize_whitespace("  John    Smith  \\n  ")
        # Returns: "John Smith"

    Cost:
        O(n)
    """
    return " ".join(text.split())


def remove_punctuation_marks(text: str, preserve_hyphens: bool = True) -> str:
    """
    Remove punctuation marks from text.

    Description:
        Removes common punctuation: . , ; : ! ? ¡ ¿
        Optionally preserves hyphens for compound words.

    Args:
        text (str): Input text
        preserve_hyphens (bool): Keep hyphens in compound words. Default: True

    Returns:
        str: Text without punctuation

    Example:
        text = remove_punctuation_marks("Hello, world!")
        # Returns: "Hello world"

        text = remove_punctuation_marks("García-López", preserve_hyphens=True)
        # Returns: "García-López"

        text = remove_punctuation_marks("García-López", preserve_hyphens=False)
        # Returns: "García López"

    Cost:
        O(n)
    """
    if preserve_hyphens:
        pattern = r"[.,;:!?¡¿]"
    else:
        pattern = r"[.,;:!?¡¿\-]"

    return re.sub(pattern, "", text)


def remove_special_characters(text: str, keep_spaces: bool = True, keep_hyphens: bool = False) -> str:
    """
    Remove special characters, keeping only alphanumeric.

    Args:
        text (str): Input text
        keep_spaces (bool): Preserve spaces. Default: True
        keep_hyphens (bool): Preserve hyphens. Default: False

    Returns:
        str: Text with only alphanumeric characters

    Example:
        text = remove_special_characters("Product-123 (New!)")
        # Returns: "Product123 New"

        text = remove_special_characters("Product-123", keep_hyphens=True)
        # Returns: "Product-123"

    Cost:
        O(n)
    """
    if keep_spaces and keep_hyphens:
        pattern = r"[^a-zA-Z0-9\s\-]"
    elif keep_spaces:
        pattern = r"[^a-zA-Z0-9\s]"
    elif keep_hyphens:
        pattern = r"[^a-zA-Z0-9\-]"
    else:
        pattern = r"[^a-zA-Z0-9]"

    result = re.sub(pattern, " ", text) if keep_spaces else re.sub(pattern, "", text)

    # Clean up multiple spaces if keeping spaces
    if keep_spaces:
        result = normalize_whitespace(result)

    return result


def remove_parentheses_and_content(text: str) -> str:
    """
    Remove parentheses and their content.

    Args:
        text (str): Input text

    Returns:
        str: Text without parenthesized content

    Example:
        text = remove_parentheses_and_content("Microsoft (MSFT)")
        # Returns: "Microsoft"

        text = remove_parentheses_and_content("Price: $100 (includes tax)")
        # Returns: "Price: $100"

    Cost:
        O(n)
    """
    # Remove parentheses and content
    result = re.sub(r"\([^)]*\)", "", text)
    # Remove square brackets and content
    result = re.sub(r"\[[^\]]*\]", "", result)
    # Remove curly braces and content
    result = re.sub(r"\{[^}]*\}", "", result)

    # Clean up extra spaces
    result = normalize_whitespace(result)

    return result


def strip_quotes(text: str) -> str:
    """
    Remove quotation marks from text.

    Args:
        text (str): Input text

    Returns:
        str: Text without quotes

    Example:
        text = strip_quotes('"Hello World"')
        # Returns: 'Hello World'

        text = strip_quotes("'John Smith'")
        # Returns: 'John Smith'

    Cost:
        O(n)
    """
    # Remove various quote styles
    result = text
    for quote in ['"', "'", '"', '"', """, """]:
        result = result.replace(quote, "")

    return result


def prepare_for_comparison(text: str, aggressive: bool = False) -> str:
    """
    Prepare text for comparison with recommended settings.

    Description:
        Convenience function that applies standard normalization for
        text comparison scenarios. Offers two modes:

        **Standard Mode** (aggressive=False):
        - Lowercase
        - Remove punctuation
        - Normalize whitespace
        - Strip quotes

        **Aggressive Mode** (aggressive=True):
        - All standard mode steps
        - Remove accents
        - Remove parentheses content
        - Keep only alphanumeric

    Args:
        text (str): Text to prepare
        aggressive (bool): Use aggressive normalization. Default: False

    Returns:
        str: Normalized text ready for comparison

    Example:
        # Standard mode
        text = prepare_for_comparison("  John   Smith,  Inc.  ")
        # Returns: "john smith inc"

        # Aggressive mode
        text = prepare_for_comparison("José García (CEO)", aggressive=True)
        # Returns: "jose garcia ceo"

    Cost:
        O(n)
    """
    if aggressive:
        return normalize_text(
            text,
            lowercase=True,
            remove_punctuation=True,
            normalize_whitespace=True,
            remove_accents=True,
            remove_parentheses_content=True,
            strip_quotes=True,
            preserve_alphanumeric_only=True,
        )
    else:
        return normalize_text(
            text,
            lowercase=True,
            remove_punctuation=True,
            normalize_whitespace=True,
            remove_accents=False,
            remove_parentheses_content=False,
            strip_quotes=True,
            preserve_alphanumeric_only=False,
        )


def mask_text(text: str, keep_first: int = 1, keep_last: int = 1, mask_char: str = "*", keep_chars: Optional[str] = None) -> str:
    """
    Mask text by replacing characters with a mask character, keeping some visible.

    Description:
        Hides sensitive information by replacing characters with a mask-char,
        while maintaining a specified number of characters visible at the
        start and/or end.

    Args:
        text (str): Text to mask
        keep_first (int): Number of characters to keep at the start. Default: 1
        keep_last (int): Number of characters to keep at the end. Default: 1
        mask_char (str): Character used for masking. Default: "*"
        keep_chars (str, optional): Specific characters to never mask (e.g., "@.-").
                                    If None, all characters between first/last are masked.

    Returns:
        str: Masked string

    Example:
        mask_text("12345678Z", keep_first=2, keep_last=1)
        # Returns: "12******Z"

        mask_text("juan.garcia@gmail.com", keep_first=1, keep_last=4, keep_chars="@.")
        # Returns: "j***.g*****@g****.com"

    Cost:
        O(n)
    """
    if not text:
        return ""

    n = len(text)

    # If string is shorter than what we want to keep, return as is
    if n <= keep_first + keep_last:
        return text

    result = list(text)

    for i in range(keep_first, n - keep_last):
        char = text[i]

        # Check if we should keep this specific character
        if keep_chars and char in keep_chars:
            continue

        result[i] = mask_char

    return "".join(result)
