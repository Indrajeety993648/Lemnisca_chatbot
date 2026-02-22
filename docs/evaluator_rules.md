# Clearpath — Output Evaluator Rules

The Output Evaluator runs 3 sequential checks on every LLM response before returning it to the user. Flags are **annotations only** — they never block or modify the response.

---

## Check 1: No-Context Warning

| Property | Value |
|---|---|
| Flag | `no_context_warning` |
| Severity | `warning` |
| Trigger | `retrieval_count == 0` (no chunks passed the 0.35 similarity threshold) |
| Action | Annotate response; frontend shows yellow banner: *"This response was generated without supporting documentation."* |

```python
if retrieval_count == 0:
    flags.append("no_context_warning")
```

---

## Check 2: Refusal / Non-Answer Detection

| Property | Value |
|---|---|
| Flag | `refusal_detected` |
| Severity | `info` |
| Trigger | Response contains any phrase from REFUSAL_PHRASES (case-insensitive substring match) |
| Action | Annotate only. Expected behavior when query is out of domain. |
| Match threshold | 1 phrase (any single match triggers; flag added once max) |

**REFUSAL_PHRASES**:
- `i cannot`
- `i can't`
- `i don't have information`
- `i don't have enough information`
- `i do not have`
- `i'm not sure`
- `i am not sure`
- `i'm unable to`
- `i am unable to`
- `outside my knowledge`
- `beyond my scope`
- `not able to help`
- `cannot assist with`
- `no information available`
- `unfortunately, i don't`
- `i apologize, but i`
- `i'm sorry, but i don't`

---

## Check 3: Domain-Specific Hallucination Check

| Property | Value |
|---|---|
| Flag | `potential_hallucination` |
| Severity | `warning` |
| Trigger | Response contains prices or proper nouns not present in retrieved chunks |
| Action | Annotate; frontend shows orange banner: *"Some details in this response could not be verified against our documentation."* |

**Detection heuristic**:

1. **Price check** — regex: `\$\d+(?:\.\d{2})?(?:\s*/\s*(?:month|year|mo|yr))?`
   - Extract all currency amounts from response and from retrieved chunks.
   - If any response price does **not** appear in chunks → flag.

2. **Proper noun check** — regex: `\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b`
   - Extract capitalized multi-word proper nouns from response and from chunks.
   - If any response noun is not in chunks **and** not in the allowlist → flag.

**ALLOWED_TERMS** (never flagged regardless of chunk presence):
- `Clearpath`
- `Clearpath Assistant`
