"""
text_sanitizer.py — Input and output text sanitization utilities.

Provides two distinct sanitization functions:
1. sanitize_input() — sanitize raw user query input before processing.
2. sanitize_chunk() — sanitize retrieved chunks before prompt insertion (Section 3.7).

The sanitization rules exactly follow ARCHITECTURE.md Sections 3.7 and 8.
"""
import re


# Lines starting with these prefixes are considered prompt injection attempts.
# Matched case-insensitively at the start of any line (after optional whitespace).
_INJECTION_PATTERNS = [
    re.compile(r"^\s*SYSTEM\s*:", re.IGNORECASE),
    re.compile(r"^\s*INSTRUCTION\s*:", re.IGNORECASE),
    re.compile(r"^\s*IGNORE\s+PREVIOUS", re.IGNORECASE),
    re.compile(r"^\s*YOU\s+ARE", re.IGNORECASE),
]

# PAGE_BREAK marker pattern inserted during PDF ingestion
_PAGE_BREAK_RE = re.compile(r"\[PAGE_BREAK:\d+\]")

# Maximum tokens (approximate) for a single chunk in the prompt (Section 3.7 safety limit).
# We use the 0.75 words-per-token approximation for the truncation guard.
_CHUNK_MAX_TOKENS = 600


def sanitize_input(text: str) -> str:
    """
    Sanitize raw user query input before processing.

    Removes:
    - HTML tags
    - Null bytes
    - Non-printable control characters (except tab, newline, carriage-return)
    - Collapses excessive whitespace

    Does NOT truncate — length limits are enforced by Pydantic (max_length=2000).
    """
    if not text:
        return ""

    # Remove null bytes
    text = text.replace("\x00", "")

    # Remove HTML tags
    text = re.sub(r"<[^>]*>", "", text)

    # Remove non-printable control characters except \t \n \r
    text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E\x80-\xFF]", "", text)

    # Collapse multiple spaces/tabs to single space
    text = re.sub(r"[ \t]+", " ", text)

    # Collapse multiple newlines to at most two
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def sanitize_chunk(text: str) -> str:
    """
    Sanitize a retrieved chunk before insertion into the LLM prompt.

    Per Section 3.7 of ARCHITECTURE.md:
    1. Strip excessive whitespace.
    2. Remove [PAGE_BREAK:N] markers.
    3. Truncate to 600 tokens max (using word-based approximation).
    4. Remove lines that start with prompt-injection patterns:
       SYSTEM:, INSTRUCTION:, IGNORE PREVIOUS, YOU ARE.
    """
    if not text:
        return ""

    # Step 2: Remove PAGE_BREAK markers
    text = _PAGE_BREAK_RE.sub("", text)

    # Step 1: Collapse whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Step 4: Filter prompt injection lines
    lines = text.split("\n")
    filtered_lines = [
        line
        for line in lines
        if not any(pat.match(line) for pat in _INJECTION_PATTERNS)
    ]
    text = "\n".join(filtered_lines)

    # Step 3: Truncate to CHUNK_MAX_TOKENS (word-based approximation:
    # 1 token ≈ 0.75 words → max ~450 words for 600 tokens)
    max_words = int(_CHUNK_MAX_TOKENS * 0.75)
    words = text.split()
    if len(words) > max_words:
        text = " ".join(words[:max_words])

    return text.strip()


def sanitize_pdf_text(text: str) -> str:
    """
    Sanitize raw text extracted from a PDF page during ingestion.

    Removes control characters and collapses excessive whitespace while
    preserving structural newlines needed for chunking.
    """
    if not text:
        return ""

    # Remove null bytes and non-printable characters except whitespace
    text = text.replace("\x00", "")
    text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E\x80-\xFF]", "", text)

    # Collapse horizontal whitespace
    text = re.sub(r"[ \t]+", " ", text)

    # Collapse more than two consecutive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
