"""
test_router.py — Tests for the deterministic query router.

Covers all 6 decision tree nodes from ARCHITECTURE.md Section 4.
Naming convention: test_router_<behavior>
"""
import pytest

from backend.router.deterministic_router import classify_query


# ---------------------------------------------------------------------------
# NODE 1: word_count <= 3 AND question_count <= 1 AND NOT has_complexity_kws
# ---------------------------------------------------------------------------

def test_router_classifies_single_word_as_simple():
    assert classify_query("Hello") == "simple"


def test_router_classifies_greeting_as_simple():
    assert classify_query("Hi there") == "simple"


def test_router_classifies_trivial_three_word_question_as_simple():
    assert classify_query("What is Clearpath?") == "simple"


def test_router_node1_bypassed_by_complexity_keyword():
    # "vs" is a complexity keyword; even short queries bypass NODE 1
    assert classify_query("A vs B?") == "complex"


# ---------------------------------------------------------------------------
# NODE 2: has_complaint_markers → complex
# ---------------------------------------------------------------------------

def test_router_classifies_not_working_as_complex():
    assert classify_query("The login is not working") == "complex"


def test_router_classifies_refund_request_as_complex():
    assert classify_query("I want a refund immediately.") == "complex"


def test_router_classifies_billing_error_complaint_as_complex():
    # From ARCHITECTURE.md Example 3
    assert classify_query(
        "The billing system is not working and I want a refund immediately. This is unacceptable."
    ) == "complex"


def test_router_classifies_cancellation_as_complex():
    assert classify_query("I want to cancel my subscription.") == "complex"


def test_router_classifies_escalation_request_as_complex():
    assert classify_query("I need to escalate this issue to a supervisor.") == "complex"


# ---------------------------------------------------------------------------
# NODE 3: question_count >= 3 → complex
# ---------------------------------------------------------------------------

def test_router_classifies_three_questions_as_complex():
    # From ARCHITECTURE.md Example 4
    query = (
        "What is the difference between the Pro plan and the Enterprise plan? "
        "Which one should I choose? Are there any hidden fees?"
    )
    assert classify_query(query) == "complex"


def test_router_classifies_exactly_three_question_marks_as_complex():
    assert classify_query("What? Why? How?") == "complex"


def test_router_two_questions_does_not_trigger_node3():
    # Two question marks alone do not trigger NODE 3
    # (will fall through to node 5/6 — simple if no other signals)
    result = classify_query("What are your hours? Are you open weekends?")
    # word_count=8, q=2 → NODE 3: NO. No complaint, no complexity → simple
    assert result == "simple"


# ---------------------------------------------------------------------------
# NODE 4: has_comparison_pattern → complex
# ---------------------------------------------------------------------------

def test_router_classifies_vs_as_complex():
    assert classify_query("Pro vs Enterprise plan comparison") == "complex"


def test_router_classifies_versus_as_complex():
    assert classify_query("Free tier versus paid tier") == "complex"


def test_router_classifies_difference_between_as_complex():
    assert classify_query("What is the difference between plan A and plan B?") == "complex"


def test_router_classifies_better_than_as_complex():
    assert classify_query("Is the Pro plan better than the Free plan?") == "complex"


# ---------------------------------------------------------------------------
# NODE 5: complexity_score >= 2 → complex
# ---------------------------------------------------------------------------

def test_router_classifies_complexity_keyword_query_as_complex():
    # From ARCHITECTURE.md Example 5
    assert classify_query(
        "Can you explain how the integration with Slack works step by step?"
    ) == "complex"


def test_router_classifies_advanced_configuration_as_complex():
    assert classify_query("How do I configure the advanced enterprise integration?") == "complex"


def test_router_classifies_optimization_strategy_as_complex():
    assert classify_query("What is the best optimization strategy for scalability?") == "complex"


def test_router_classifies_security_audit_as_complex():
    assert classify_query("How do I perform a security audit on my account?") == "complex"


def test_router_classifies_troubleshooting_as_complex():
    assert classify_query("Help me troubleshoot this configuration issue") == "complex"


# ---------------------------------------------------------------------------
# NODE 6: word_count > 25 AND has_ambiguity_markers → complex
# ---------------------------------------------------------------------------

def test_router_classifies_long_ambiguous_query_as_complex():
    query = (
        "I'm not sure what would be the best option for our team. "
        "We have about fifteen users and we're considering different plans. "
        "Could you recommend something based on our usage patterns?"
    )
    # has 'recommend' (ambiguity marker) and word_count > 25
    assert classify_query(query) == "complex"


# ---------------------------------------------------------------------------
# Default → simple
# ---------------------------------------------------------------------------

def test_router_classifies_business_hours_as_simple():
    # From ARCHITECTURE.md Example 6
    assert classify_query("What are your business hours?") == "simple"


def test_router_classifies_password_reset_as_simple():
    # From ARCHITECTURE.md Example 2
    assert classify_query("How do I reset my password?") == "simple"


def test_router_classifies_plain_factual_question_as_simple():
    assert classify_query("How many users are included in the Pro plan?") == "simple"


def test_router_classifies_contact_info_query_as_simple():
    assert classify_query("What is your email address?") == "simple"


def test_router_returns_only_valid_classifications():
    """Ensure the router never returns an unexpected value."""
    test_queries = [
        "Help",
        "How do I log in?",
        "Compare Pro and Enterprise plans.",
        "I want a refund!",
        "Tell me everything about security compliance and audit strategies.",
    ]
    for q in test_queries:
        result = classify_query(q)
        assert result in ("simple", "complex"), f"Unexpected result '{result}' for query: {q}"
