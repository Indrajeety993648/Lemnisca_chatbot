"""
output_evaluator.py — 3-check post-generation output evaluator.

Implements Section 5 of ARCHITECTURE.md exactly. The evaluator runs
3 sequential checks on every LLM response before it is returned to the user.
Each check either appends a flag or does nothing. Flags annotate the response
— they do NOT block or modify the answer text.

Checks:
  1. No-Context Check (Section 5.1)
     Trigger: retrieval_count == 0
     Flag: 'no_context_warning'

  2. Refusal / Non-Answer Detection (Section 5.2)
     Trigger: response contains any phrase from REFUSAL_PHRASES (case-insensitive substring)
     Flag: 'refusal_detected'

  3. Domain-Specific Hallucination Check (Section 5.3)
     Trigger: response mentions a currency amount or capitalized proper noun
              that does not appear in the retrieved chunks.
     Flag: 'potential_hallucination'

All phrase lists and heuristics are immutable per the Universal Rules.
"""
import re
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Check 2: Refusal phrase list (Section 5.2 — immutable)
# ---------------------------------------------------------------------------

REFUSAL_PHRASES: List[str] = [
    "i cannot",
    "i can't",
    "i don't have information",
    "i don't have enough information",
    "i do not have",
    "i'm not sure",
    "i am not sure",
    "i'm unable to",
    "i am unable to",
    "outside my knowledge",
    "beyond my scope",
    "not able to help",
    "cannot assist with",
    "no information available",
    "unfortunately, i don't",
    "i apologize, but i",
    "i'm sorry, but i don't",
]

# ---------------------------------------------------------------------------
# Check 3: Hallucination — known safe terms (Section 5.3 — immutable)
# ---------------------------------------------------------------------------

ALLOWED_TERMS: List[str] = ["Clearpath", "Clearpath Assistant"]

# Regex patterns (Section 5.3 — immutable)
_PRICE_RE = re.compile(
    r"\$\d+(?:\.\d{2})?(?:\s*/\s*(?:month|year|mo|yr))?", re.IGNORECASE
)
_PROPER_NOUN_RE = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b")


# ---------------------------------------------------------------------------
# Helper functions for Check 3
# ---------------------------------------------------------------------------


def extract_prices(text: str) -> List[str]:
    """
    Extract all currency amount strings from text.

    Pattern: r'\\$\\d+(?:\\.\\d{2})?(?:\\s*/\\s*(?:month|year|mo|yr))?'
    as specified in Section 5.3.

    Returns a list of matched strings (e.g., ['$29.99', '$99/month']).
    """
    return _PRICE_RE.findall(text)


def extract_proper_nouns(text: str) -> List[str]:
    """
    Extract capitalized multi-word proper nouns from text.

    Pattern: r'\\b[A-Z][a-z]+(?:\\s+[A-Z][a-z]+)+\\b'
    as specified in Section 5.3.

    Returns a list of matched strings (e.g., ['Pro Plan', 'Enterprise Suite']).
    """
    return _PROPER_NOUN_RE.findall(text)


def check_hallucination(
    response_text: str, retrieved_chunks: List[Dict[str, Any]]
) -> Optional[str]:
    """
    Check for potential hallucinations in the LLM response.

    Detection heuristic (Section 5.3):
    1. Extract all currency amounts from the response.
    2. Extract all currency amounts from the concatenated retrieved chunks.
    3. If ANY amount in the response is not present in the chunks → flag.
    4. Extract capitalized multi-word proper nouns from the response.
    5. Extract capitalized multi-word proper nouns from the chunks.
    6. If ANY proper noun in the response is neither in the chunks nor in
       ALLOWED_TERMS → flag.

    Returns:
        'potential_hallucination' if a hallucination is detected, else None.
    """
    chunk_text = " ".join(c.get("text", "") for c in retrieved_chunks)

    # Price check
    response_prices = extract_prices(response_text)
    chunk_prices = extract_prices(chunk_text)
    chunk_prices_set = set(chunk_prices)

    for price in response_prices:
        if price not in chunk_prices_set:
            return "potential_hallucination"

    # Proper noun check
    response_names = extract_proper_nouns(response_text)
    chunk_names = extract_proper_nouns(chunk_text)
    chunk_names_set = set(chunk_names)

    for name in response_names:
        if name not in chunk_names_set and name not in ALLOWED_TERMS:
            return "potential_hallucination"

    return None


# ---------------------------------------------------------------------------
# Main evaluator function
# ---------------------------------------------------------------------------


def evaluate_output(
    response_text: str,
    retrieval_count: int,
    retrieved_chunks: List[Dict[str, Any]],
) -> List[str]:
    """
    Run all 3 output evaluation checks on an LLM response.

    Checks are run sequentially. Each produces at most one flag.
    Flags annotate the response — they do NOT modify or block it.

    Args:
        response_text: The raw LLM response string.
        retrieval_count: Number of chunks that passed the similarity threshold.
        retrieved_chunks: List of chunk dicts (keys: text, source_file,
                          page_number, score) — used for hallucination check.

    Returns:
        List of flag strings. Possible values:
          - 'no_context_warning'   (severity: warning)
          - 'refusal_detected'     (severity: info)
          - 'potential_hallucination' (severity: warning)
    """
    flags: List[str] = []

    # --- Check 1: No-Context Check (Section 5.1) ---
    if retrieval_count == 0:
        flags.append("no_context_warning")

    # --- Check 2: Refusal Detection (Section 5.2) ---
    response_lower = response_text.lower()
    for phrase in REFUSAL_PHRASES:
        if phrase in response_lower:
            flags.append("refusal_detected")
            break  # One match is sufficient — do not double-flag

    # --- Check 3: Hallucination Check (Section 5.3) ---
    hallucination_flag = check_hallucination(response_text, retrieved_chunks)
    if hallucination_flag:
        flags.append(hallucination_flag)

    return flags
