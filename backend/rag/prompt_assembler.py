"""
prompt_assembler.py — Prompt template assembly for the LLM.

Builds the messages list passed to the Groq API by:
1. Using the exact SYSTEM_PROMPT and USER_PROMPT_TEMPLATE from Section 3.8
   of ARCHITECTURE.md.
2. Assembling retrieved chunks into a context block with source citations.
3. Sanitizing each chunk for prompt injection before insertion.

The assembled messages format follows the OpenAI Chat Completions API:
  [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
"""
import logging
from typing import Dict, List

from backend.rag.retriever import RetrievedChunk
from backend.utils.text_sanitizer import sanitize_chunk

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt templates (exactly as specified in Section 3.8 of ARCHITECTURE.md)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are Clearpath Assistant, a helpful customer support agent for Clearpath.
You answer questions based ONLY on the provided context. If the context does not contain
enough information to answer the question, say "I don't have enough information in our
documentation to answer that question."

Do not make up information. Do not reference external sources. Be concise and helpful."""

USER_PROMPT_TEMPLATE = """Context:
---
{context_chunks}
---

Question: {user_query}

Answer:"""


# ---------------------------------------------------------------------------
# Assembly function
# ---------------------------------------------------------------------------


def assemble_prompt(
    query: str, chunks: List[RetrievedChunk]
) -> List[Dict[str, str]]:
    """
    Construct the full messages list for the Groq Chat Completions API.

    Each retrieved chunk is sanitized (prompt injection removal, whitespace
    normalization, 600-token truncation) before being inserted into the
    context block.

    Args:
        query: The sanitized user query.
        chunks: List of RetrievedChunk objects from the retriever.

    Returns:
        Two-element list of message dicts:
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": <assembled user message>}
        ]
    """
    context_text = ""
    for chunk in chunks:
        # Sanitize chunk text per Section 3.7
        clean_text = sanitize_chunk(chunk.text)
        context_text += f"[Source: {chunk.source_file}, Page {chunk.page_number}]\n"
        context_text += clean_text + "\n\n"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.strip()},
        {
            "role": "user",
            "content": USER_PROMPT_TEMPLATE.format(
                context_chunks=context_text.strip(),
                user_query=query,
            ),
        },
    ]

    logger.debug(
        "Assembled prompt: %d chunks, context length ~%d chars",
        len(chunks),
        len(context_text),
    )

    return messages
