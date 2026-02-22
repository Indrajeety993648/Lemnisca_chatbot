"""
deterministic_router.py — Rule-based query classifier.

Implements the complete 6-node decision tree from Section 4 of ARCHITECTURE.md
exactly as specified. All keyword lists, regex patterns, thresholds, and
decision logic are immutable per Section 4 — Universal Rules.

Classification output: 'simple' or 'complex'

Model mapping (Section 4.1):
  simple  → llama-3.1-8b-instant   (max 512 response tokens)
  complex → llama-3.3-70b-versatile (max 1024 response tokens)
"""
import re
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Keyword / Phrase Lists (Section 4.1 — immutable)
# ---------------------------------------------------------------------------

# Case-insensitive whole-word boundary match (re.search with \b)
COMPLEXITY_KEYWORDS: List[str] = [
    "compare", "comparison", "difference", "differences", "versus", "vs",
    "integrate", "integration", "configure", "configuration", "migrate",
    "migration", "troubleshoot", "troubleshooting", "architecture",
    "workflow", "optimize", "optimization", "analyze", "analysis",
    "strategy", "strategies", "compliance", "security", "audit",
    "enterprise", "scalability", "performance", "benchmark", "custom",
    "advanced", "multiple", "several", "complex", "detailed", "comprehensive",
    "explain how", "walk me through", "step by step", "in depth",
]

# Case-insensitive substring match (in operator)
AMBIGUITY_MARKERS: List[str] = [
    "it depends", "what if", "hypothetically", "in general",
    "is it possible", "can you explain", "could you elaborate",
    "what are the pros and cons", "trade-off", "tradeoff",
    "best practice", "best practices", "recommend", "recommendation",
    "should i", "which one", "what would",
]

# Case-insensitive substring match (in operator)
COMPLAINT_MARKERS: List[str] = [
    "not working", "broken", "bug", "issue", "problem", "error",
    "frustrated", "disappointed", "unacceptable", "terrible",
    "worst", "angry", "complaint", "escalate", "refund",
    "cancel", "cancellation", "speak to manager", "supervisor",
]

# Regex patterns for comparison detection
COMPARISON_PATTERNS: List[str] = [
    r"\bvs\.?\b",
    r"\bversus\b",
    r"\bcompared?\s+to\b",
    r"\bdifference\s+between\b",
    r"\bbetter\s+than\b",
    r"\bworse\s+than\b",
    r"\bor\b.*\bor\b",
]

# Pre-compile patterns for performance
_COMPLEXITY_KEYWORD_RES = [
    re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE)
    for kw in COMPLEXITY_KEYWORDS
]
_COMPARISON_PATTERN_RES = [
    re.compile(pattern, re.IGNORECASE) for pattern in COMPARISON_PATTERNS
]
# Sentence-end detector: punctuation followed by a space or end-of-string
_SENTENCE_END_RE = re.compile(r"[.?!](?:\s|$)")


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------


def _extract_features(query: str) -> Dict:
    """
    Extract all classification features from a raw query string.

    Features:
        word_count              — whitespace-split token count
        char_count              — len(query)
        question_count          — count of '?' characters
        has_complexity_keywords — any COMPLEXITY_KEYWORDS whole-word match
        has_ambiguity_markers   — any AMBIGUITY_MARKERS substring present
        has_complaint_markers   — any COMPLAINT_MARKERS substring present
        has_comparison_pattern  — any COMPARISON_PATTERNS regex match
        sentence_count          — count of sentence-ending punctuation
    """
    query_lower = query.lower()

    word_count = len(query_lower.split())
    char_count = len(query)
    question_count = query.count("?")
    sentence_count = len(_SENTENCE_END_RE.findall(query))

    has_complexity_keywords = any(
        pat.search(query_lower) for pat in _COMPLEXITY_KEYWORD_RES
    )
    has_ambiguity_markers = any(m in query_lower for m in AMBIGUITY_MARKERS)
    has_complaint_markers = any(m in query_lower for m in COMPLAINT_MARKERS)
    has_comparison_pattern = any(
        pat.search(query_lower) for pat in _COMPARISON_PATTERN_RES
    )

    return {
        "word_count": word_count,
        "char_count": char_count,
        "question_count": question_count,
        "has_complexity_keywords": has_complexity_keywords,
        "has_ambiguity_markers": has_ambiguity_markers,
        "has_complaint_markers": has_complaint_markers,
        "has_comparison_pattern": has_comparison_pattern,
        "sentence_count": sentence_count,
    }


# ---------------------------------------------------------------------------
# Decision tree (Section 4.1 — 6 nodes, immutable)
# ---------------------------------------------------------------------------


def classify_query(query: str) -> str:
    """
    Classify a user query as 'simple' or 'complex' using the deterministic
    6-node decision tree from Section 4.1 of ARCHITECTURE.md.

    No LLM calls are made. Classification is based solely on:
    - word_count, question_count, sentence_count
    - Keyword/phrase lists: COMPLEXITY_KEYWORDS, AMBIGUITY_MARKERS,
      COMPLAINT_MARKERS, COMPARISON_PATTERNS

    Returns:
        'simple' or 'complex'
    """
    f = _extract_features(query)

    # NODE 1: Is word_count <= 3 AND question_count <= 1 AND NOT has_complexity_keywords?
    #         YES → simple (greeting or trivial query)
    if f["word_count"] <= 3 and f["question_count"] <= 1 and not f["has_complexity_keywords"]:
        return "simple"

    # NODE 2: Does the query have has_complaint_markers?
    #         YES → complex (complaints need nuanced handling)
    if f["has_complaint_markers"]:
        return "complex"

    # NODE 3: Is question_count >= 3?
    #         YES → complex (multi-part question)
    if f["question_count"] >= 3:
        return "complex"

    # NODE 4: Does the query have has_comparison_pattern?
    #         YES → complex (comparative analysis)
    if f["has_comparison_pattern"]:
        return "complex"

    # NODE 5: Count complexity indicators.
    #         complexity_score >= 2 → complex
    complexity_score = 0
    if f["has_complexity_keywords"]:
        complexity_score += 2
    if f["has_ambiguity_markers"]:
        complexity_score += 2
    if f["word_count"] > 40:
        complexity_score += 1
    if f["sentence_count"] >= 3:
        complexity_score += 1

    if complexity_score >= 2:
        return "complex"

    # NODE 6: Is word_count > 25 AND has_ambiguity_markers?
    #         YES → complex
    if f["word_count"] > 25 and f["has_ambiguity_markers"]:
        return "complex"

    # Default → simple
    return "simple"
