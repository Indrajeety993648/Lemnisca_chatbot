"""
groq_client.py — Groq API wrapper with retry logic.

Wraps the groq Python SDK Chat Completions API with:
- Support for both streaming and non-streaming responses.
- Max 2 retries with exponential backoff: 1s after attempt 1, 3s after attempt 2.
- Retry only on 5xx errors or timeouts; do NOT retry on 4xx.
- Raises ConnectionError if all retries are exhausted (caller returns 503).

Per Section 8 of ARCHITECTURE.md:
  Retry policy: max 2 retries, exponential backoff (1s, 3s)
  Timeout per request: 30 seconds
  Only retry on 5xx or timeout; never on 4xx
"""
import logging
import time
from typing import Any, Dict, List

import groq

from backend.config import settings

logger = logging.getLogger(__name__)

# Retry configuration (Section 8 — Fault Tolerance)
_MAX_RETRIES = 2
_BACKOFF_DELAYS = [1, 3]   # seconds between retries

# Request timeout in seconds
_REQUEST_TIMEOUT = 30.0


class GroqClient:
    """
    Thin wrapper around the groq Python SDK with retry logic.

    A single module-level instance (`groq_client`) is used throughout the
    backend to share the underlying HTTP connection pool.
    """

    def __init__(self, api_key: str = settings.GROQ_API_KEY) -> None:
        self._client = groq.Groq(api_key=api_key, timeout=_REQUEST_TIMEOUT)

    def generate(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        stream: bool = False,
    ) -> Any:
        """
        Call the Groq Chat Completions API.

        Args:
            model: Groq model ID. Must be one of:
                   'llama-3.1-8b-instant' (simple) or
                   'llama-3.3-70b-versatile' (complex).
            messages: List of {'role': '...', 'content': '...'} dicts.
            max_tokens: Maximum tokens in the completion response.
            stream: If True, returns an iterator of streaming chunks.

        Returns:
            groq.types.chat.ChatCompletion (non-streaming) or
            groq.Stream[groq.types.chat.ChatCompletionChunk] (streaming).

        Raises:
            ConnectionError: If Groq API is unreachable after all retries.
            groq.BadRequestError: For 4xx client errors (not retried).
        """
        last_exception: Exception | None = None

        for attempt in range(_MAX_RETRIES + 1):
            try:
                response = self._client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    stream=stream,
                )
                return response

            except groq.BadRequestError as exc:
                # 4xx — do NOT retry; re-raise immediately
                logger.error(
                    "Groq 4xx error (not retrying) for model=%s: %s", model, exc
                )
                raise

            except (groq.APIStatusError, groq.APITimeoutError, groq.APIConnectionError) as exc:
                last_exception = exc
                status_code = getattr(exc, "status_code", None)

                # Do not retry on 4xx responses from APIStatusError
                if status_code is not None and 400 <= status_code < 500:
                    logger.error(
                        "Groq 4xx status %d (not retrying) for model=%s: %s",
                        status_code,
                        model,
                        exc,
                    )
                    raise

                if attempt < _MAX_RETRIES:
                    delay = _BACKOFF_DELAYS[attempt]
                    logger.warning(
                        "Groq API error (attempt %d/%d), retrying in %ds: %s",
                        attempt + 1,
                        _MAX_RETRIES + 1,
                        delay,
                        exc,
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        "Groq API unreachable after %d attempts for model=%s: %s",
                        _MAX_RETRIES + 1,
                        model,
                        exc,
                    )

            except Exception as exc:
                # Unexpected exception — do not retry
                logger.exception(
                    "Unexpected error calling Groq API for model=%s", model
                )
                raise

        raise ConnectionError(
            f"Groq API unreachable after {_MAX_RETRIES + 1} attempts: {last_exception}"
        )


# Module-level singleton used throughout the backend.
groq_client = GroqClient()
