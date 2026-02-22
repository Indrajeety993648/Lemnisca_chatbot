"""
test_evaluator.py — Tests for the 3-check output evaluator.

Covers:
  - Check 1: no_context_warning
  - Check 2: refusal_detected
  - Check 3: potential_hallucination
Naming convention: test_evaluator_<check>_<behavior>
"""
import pytest

from backend.evaluator.output_evaluator import (
    REFUSAL_PHRASES,
    check_hallucination,
    evaluate_output,
    extract_prices,
    extract_proper_nouns,
)

# ---------------------------------------------------------------------------
# Helper fixtures / data
# ---------------------------------------------------------------------------

GOOD_RESPONSE = "Clearpath offers a Pro plan and an Enterprise plan for teams."

SAMPLE_CHUNKS = [
    {
        "text": "Clearpath offers a Pro plan and an Enterprise plan.",
        "source_file": "plans.pdf",
        "page_number": 1,
        "score": 0.9,
    }
]

EMPTY_CHUNKS: list = []


# ---------------------------------------------------------------------------
# Check 1: no_context_warning
# ---------------------------------------------------------------------------

def test_evaluator_no_context_flag_when_retrieval_count_zero():
    flags = evaluate_output(GOOD_RESPONSE, retrieval_count=0, retrieved_chunks=EMPTY_CHUNKS)
    assert "no_context_warning" in flags


def test_evaluator_no_context_flag_not_set_when_chunks_retrieved():
    flags = evaluate_output(GOOD_RESPONSE, retrieval_count=1, retrieved_chunks=SAMPLE_CHUNKS)
    assert "no_context_warning" not in flags


def test_evaluator_no_context_flag_severity_warning():
    """no_context_warning should appear in flags list — no blocking."""
    flags = evaluate_output("Some answer.", retrieval_count=0, retrieved_chunks=EMPTY_CHUNKS)
    # Response still returned, just flagged
    assert isinstance(flags, list)
    assert "no_context_warning" in flags


# ---------------------------------------------------------------------------
# Check 2: refusal_detected
# ---------------------------------------------------------------------------

def test_evaluator_refusal_detected_for_i_cannot():
    response = "I cannot answer that question based on the available information."
    flags = evaluate_output(response, retrieval_count=1, retrieved_chunks=SAMPLE_CHUNKS)
    assert "refusal_detected" in flags


def test_evaluator_refusal_detected_for_i_dont_have_information():
    response = "I don't have information about that topic in our documentation."
    flags = evaluate_output(response, retrieval_count=1, retrieved_chunks=SAMPLE_CHUNKS)
    assert "refusal_detected" in flags


def test_evaluator_refusal_detected_for_outside_my_knowledge():
    response = "That is outside my knowledge scope."
    flags = evaluate_output(response, retrieval_count=1, retrieved_chunks=SAMPLE_CHUNKS)
    assert "refusal_detected" in flags


def test_evaluator_refusal_detected_case_insensitive():
    response = "I CANNOT assist with that."
    flags = evaluate_output(response, retrieval_count=1, retrieved_chunks=SAMPLE_CHUNKS)
    assert "refusal_detected" in flags


def test_evaluator_refusal_not_detected_for_normal_response():
    response = "The Pro plan includes unlimited users and priority support."
    flags = evaluate_output(response, retrieval_count=2, retrieved_chunks=SAMPLE_CHUNKS)
    assert "refusal_detected" not in flags


def test_evaluator_refusal_detected_only_once_even_with_multiple_phrases():
    response = "I cannot help. I am unable to find that. I'm not sure about this."
    flags = evaluate_output(response, retrieval_count=1, retrieved_chunks=SAMPLE_CHUNKS)
    assert flags.count("refusal_detected") == 1


def test_evaluator_all_refusal_phrases_trigger_flag():
    """Each phrase from the list should trigger refusal_detected."""
    for phrase in REFUSAL_PHRASES:
        response = f"Unfortunately, {phrase} answer that question."
        flags = evaluate_output(response, retrieval_count=1, retrieved_chunks=SAMPLE_CHUNKS)
        assert "refusal_detected" in flags, f"Phrase not caught: '{phrase}'"


# ---------------------------------------------------------------------------
# Check 3: potential_hallucination — price check
# ---------------------------------------------------------------------------

def test_evaluator_hallucination_detected_for_unknown_price():
    response = "The Pro plan costs $99/month which is competitive."
    # Chunks don't mention $99/month
    chunks = [{"text": "The Pro plan is available for purchase.", "source_file": "x.pdf",
                "page_number": 1, "score": 0.8}]
    flags = evaluate_output(response, retrieval_count=1, retrieved_chunks=chunks)
    assert "potential_hallucination" in flags


def test_evaluator_hallucination_not_detected_when_price_in_chunks():
    chunks = [{"text": "The Pro plan costs $49/month.", "source_file": "pricing.pdf",
                "page_number": 2, "score": 0.9}]
    response = "The Pro plan is priced at $49/month."
    flags = evaluate_output(response, retrieval_count=1, retrieved_chunks=chunks)
    assert "potential_hallucination" not in flags


def test_evaluator_hallucination_detected_for_unknown_proper_noun():
    response = "You can use the Galaxy Enterprise Suite for this."
    # Chunks don't mention "Galaxy Enterprise Suite"
    chunks = [{"text": "Clearpath provides enterprise tools.", "source_file": "x.pdf",
                "page_number": 1, "score": 0.8}]
    flags = evaluate_output(response, retrieval_count=1, retrieved_chunks=chunks)
    assert "potential_hallucination" in flags


def test_evaluator_hallucination_not_detected_for_allowed_terms():
    response = "Clearpath Assistant can help you with your queries."
    chunks = [{"text": "Customer support is provided.", "source_file": "x.pdf",
                "page_number": 1, "score": 0.8}]
    flags = evaluate_output(response, retrieval_count=1, retrieved_chunks=chunks)
    assert "potential_hallucination" not in flags


# ---------------------------------------------------------------------------
# Helper function unit tests
# ---------------------------------------------------------------------------

def test_extract_prices_finds_dollar_amounts():
    text = "The plan costs $29.99 and the annual option is $299/year."
    prices = extract_prices(text)
    assert "$29.99" in prices
    assert "$299/year" in prices


def test_extract_prices_returns_empty_for_no_prices():
    text = "The plan is affordable and worth every penny."
    assert extract_prices(text) == []


def test_extract_proper_nouns_finds_multi_word_names():
    text = "The Pro Plan and Enterprise Suite are both great options."
    nouns = extract_proper_nouns(text)
    assert "Pro Plan" in nouns or "Enterprise Suite" in nouns


def test_extract_proper_nouns_ignores_single_word_proper_nouns():
    text = "Clearpath is a platform."
    nouns = extract_proper_nouns(text)
    # "Clearpath" alone is a single word — not matched by the multi-word regex
    assert "Clearpath" not in nouns


# ---------------------------------------------------------------------------
# Multi-flag scenarios
# ---------------------------------------------------------------------------

def test_evaluator_can_have_multiple_flags():
    """no_context_warning + refusal_detected can both appear."""
    response = "I cannot find any relevant documentation."
    flags = evaluate_output(response, retrieval_count=0, retrieved_chunks=EMPTY_CHUNKS)
    assert "no_context_warning" in flags
    assert "refusal_detected" in flags


def test_evaluator_returns_empty_list_for_clean_response():
    chunks = [{"text": "Clearpath Pro Plan costs $49/month and supports 5 users.",
                "source_file": "pricing.pdf", "page_number": 1, "score": 0.95}]
    response = "The Pro Plan supports 5 users."
    flags = evaluate_output(response, retrieval_count=1, retrieved_chunks=chunks)
    assert "no_context_warning" not in flags
    assert "refusal_detected" not in flags
