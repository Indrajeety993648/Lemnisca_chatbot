# Clearpath — Router Rules Documentation

The deterministic router classifies every query as `simple` or `complex` using rule-based logic only. No LLM calls are made during classification.

## Model Mapping

| Classification | Groq Model | Max Response Tokens |
|---|---|---|
| `simple` | `llama-3.1-8b-instant` | 512 |
| `complex` | `llama-3.3-70b-versatile` | 1024 |

---

## Feature Extraction

| Feature | Method |
|---|---|
| `word_count` | `len(query.split())` |
| `char_count` | `len(query)` |
| `question_count` | Count of `?` in query |
| `has_complexity_keywords` | Whole-word regex match against COMPLEXITY_KEYWORDS |
| `has_ambiguity_markers` | Substring match against AMBIGUITY_MARKERS |
| `has_complaint_markers` | Substring match against COMPLAINT_MARKERS |
| `has_comparison_pattern` | Regex match against COMPARISON_PATTERNS |
| `sentence_count` | Count of `.?!` followed by whitespace or end-of-string |

---

## Decision Tree

```
NODE 1: word_count <= 3 AND question_count <= 1 AND NOT has_complexity_keywords?
  YES → SIMPLE

NODE 2: has_complaint_markers?
  YES → COMPLEX

NODE 3: question_count >= 3?
  YES → COMPLEX

NODE 4: has_comparison_pattern?
  YES → COMPLEX

NODE 5: complexity_score >= 2?
  (score = has_complexity_keywords×2 + has_ambiguity_markers×2
         + (word_count > 40)×1 + (sentence_count >= 3)×1)
  YES → COMPLEX

NODE 6: word_count > 25 AND has_ambiguity_markers?
  YES → COMPLEX

DEFAULT → SIMPLE
```

---

## Keyword Lists

### COMPLEXITY_KEYWORDS (whole-word match)
`compare`, `comparison`, `difference`, `differences`, `versus`, `vs`, `integrate`, `integration`, `configure`, `configuration`, `migrate`, `migration`, `troubleshoot`, `troubleshooting`, `architecture`, `workflow`, `optimize`, `optimization`, `analyze`, `analysis`, `strategy`, `strategies`, `compliance`, `security`, `audit`, `enterprise`, `scalability`, `performance`, `benchmark`, `custom`, `advanced`, `multiple`, `several`, `complex`, `detailed`, `comprehensive`, `explain how`, `walk me through`, `step by step`, `in depth`

### AMBIGUITY_MARKERS (substring match)
`it depends`, `what if`, `hypothetically`, `in general`, `is it possible`, `can you explain`, `could you elaborate`, `what are the pros and cons`, `trade-off`, `tradeoff`, `best practice`, `best practices`, `recommend`, `recommendation`, `should i`, `which one`, `what would`

### COMPLAINT_MARKERS (substring match)
`not working`, `broken`, `bug`, `issue`, `problem`, `error`, `frustrated`, `disappointed`, `unacceptable`, `terrible`, `worst`, `angry`, `complaint`, `escalate`, `refund`, `cancel`, `cancellation`, `speak to manager`, `supervisor`

### COMPARISON_PATTERNS (regex)
- `\bvs\.?\b`
- `\bversus\b`
- `\bcompared?\s+to\b`
- `\bdifference\s+between\b`
- `\bbetter\s+than\b`
- `\bworse\s+than\b`
- `\bor\b.*\bor\b`

---

## Classification Examples

| Query | Classification | Reason |
|---|---|---|
| "What is Clearpath?" | simple | NODE 1: 3 words, no complexity kws |
| "How do I reset my password?" | simple | No signals reach threshold |
| "What are your business hours?" | simple | Default |
| "Not working, need refund immediately. Unacceptable." | complex | NODE 2: complaint markers |
| "What? Why? How?" | complex | NODE 3: 3 question marks |
| "Pro vs Enterprise plan?" | complex | NODE 4: comparison pattern |
| "Explain how Slack integration works step by step?" | complex | NODE 5: complexity score ≥ 2 |
