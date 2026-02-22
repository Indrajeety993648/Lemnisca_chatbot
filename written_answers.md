# Written Answers — Clearpath RAG Chatbot

## Q1 — Routing Logic
My system uses a **deterministic, rule-based decision tree** to classify queries into "Simple" or "Complex" before any LLM is invoked. This ensures maximum efficiency and cost-control.

**The Exact Rules:**
1. **Length Check**: Any query strictly over 120 characters is flagged as `Complex`.
2. **Intent Keywords**: Queries containing reasoning-heavy keywords like "compare", "difference", "workflow", "steps", or "how to" are marked as `Complex`.
3. **Punctuation Density**: Queries with more than one question mark (indicating multiple parts) are marked as `Complex`.
4. **Fallback**: All other queries (greetings, single-fact lookups) default to `Simple`.

**Boundary Justification:**
The 120-character limit was chosen because single-fact lookups (e.g., "What is the PTO policy?") rarely exceed this length, whereas ambiguous complaints or multi-paragraph issues always do. I chose Llama 3.3 70B for complex tasks because its larger parameter count handles cross-document reasoning significantly better than the 8B model.

**Misclassification Example:**
A query like "Hey! I'm really confused about the login process, please help me out!!???" was marked as `Complex` due to the multiple question marks and high character count, even though it is a single-fact lookup. This happened because the rule-set prioritizes "Safety-First Complexity"—it is better to use a more powerful model for a simple query than to use a weak model for a multifaceted problem.

**Improvements Without LLMs:**
I would implement a **TF-IDF based keyword density check**. By comparing the query against a pre-defined set of "Easy" vs "Hard" noun phrases extracted from the documentation, the router could identify if the user is asking about a high-level concept or a granular fact with better precision.

---

## Q2 — Retrieval Failures
During stress testing, I encountered a failure with the query: **"What happens if I break the rules?"**

**System Performance:**
The system retrieved chunks related to "Mobile App usage" and "Technical Support" rather than the "Code of Conduct" or "Employee Handbook."

**Why it failed:**
The query "break the rules" is highly semantic. The embedding model (`all-MiniLM-L6-v2`) found low-score matches for the word "rules" in the Technical Support documentation (rules for filing a ticket), but because the user didn't use the specific term "Code of Conduct" or "Policy," the retrieval score dropped below my 0.45 threshold, resulting in a **No-Context** flag.

**The Fix:**
I would implement **Query Expansion (HyDE)** or **Keyword Boosting**. By augmenting the query with synonyms or using a hybrid search (Dense Vector + BM25 BM25), the "Code of Conduct" document would have been boosted due to the high keyword overlap with "rules" and "guidelines."

---

## Q3 — Cost and Scale (5,000 Queries/Day)
**Assumptions:**
- **Simple (70%)**: 3,500 queries. (~150 input, ~100 output tokens)
- **Complex (30%)**: 1,500 queries. (~800 input, ~250 output tokens)

**Calculations:**
1. **Llama 3.1 8B (Simple)**: 
   - 3,500 * 250 = 875,000 tokens/day.
2. **Llama 3.3 70B (Complex)**: 
   - 1,500 * 1,050 = 1,575,000 tokens/day.

**Total Daily Usage**: ~2.45 Million Tokens.

**Biggest Cost Driver:**
Input tokens for the **Complex (70B) model**. Because RAG requires injecting several large text chunks as context, the input volume for complex reasoning grows exponentially compared to simple lookups.

**Highest-ROI Optimization:**
Implementing **Semantic Cache**. By storing the results of common queries (like "What is Clearpath?") in a redis-based vector cache, we could answer identical or near-identical questions without ever calling the LLM, reducing costs by an estimated 20-30% on day one.

**Optimization to Avoid:**
Reducing the **Top-K retrieval count**. While fewer chunks save input tokens, it drastically hurts the accuracy of complex reasoning. Saving 2 cents on a query isn't worth a wrong answer that hallucinates policy information.

---

## Q4 — What Is Broken
The most significant limitation is the **Lack of Global Document Coherence**.

**The Flaw:**
The system retrieves individual chunks and passes them to the LLM. If an answer requires knowing the relationship between Document A (Pricing) and Document B (Feature List) but the chunks for those specific facts are not in the Top-3, the LLM will give a partial or incorrect answer even if "Context was found."

**Why it shipped:**
Implementing a full "Map-Reduce" or "Agentic RAG" flow (where the LLM reads several pages across different docs) was too latency-heavy for a "Real-time Support" requirement and would exceed Groq's rate limits under heavy testing.

**The Fix:**
I would implement a **Document Summarization Index**. Creating a separate FAISS index containing high-level summaries of every document would allow the router to first identify which *documents* are relevant before the second stage retrieves specific *chunks*.

---

## AI Usage
**Prompt 1**: "Build a RAG chatbot using FastAPI and React. Use FAISS for vector search and Groq for the LLM."

**Prompt 2**: "Help me design a deterministic query router that decides between two models without using an LLM."

**Prompt 3**: "Implement a 3-check evaluator for RAG outputs: No-context, Refusal, and Hallucination-risk."

**Prompt 4**: "Redesign My UI to look like a premium AI Companion using dark mode and glassmorphism. preserving my theme color and robotic sense"

**Prompt 5**: "Deployed My project on AWS EC2 using docker compose but getting issue while querying, I checked network tab on inspect and found the api endpoint have wrong path, it should be http://localhost:8000/api/chat but it is showing http://localhost:5173/api/api/chat , what will be possible issue ? "

