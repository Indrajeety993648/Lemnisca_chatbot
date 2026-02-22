# Lemnisca Clearpath RAG Chatbot

## 🚀 Live Demo
**URL:** [http://65.1.114.237/](http://65.1.114.237/)
*This project is deployed on **AWS EC2** using a business-grade stack (FastAPI, Docker Compose, Nginx).*

## 🌟 Bonus Challenges Attempted
- [x] **Conversation Memory**: The chatbot maintains context across turns using a session-based approach.
- [x] **Streaming**: Implemented SSE (Server-Sent Events) for real-time, token-by-token responses.
- [x] **Live Deploy (AWS)**: Deployed to a public AWS EC2 instance. Optimized image size by 80% using CPU-only PyTorch.
- [x] **Advanced UI**: Redesigned the interface with a futuristic Glassmorphism theme and a technical Debug Panel.

## 🛠️ Tech Stack
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS.
- **Backend**: FastAPI, Uvicorn, Pydantic v2.
- **RAG Engine**: FAISS (Vector Store), `sentence-transformers` (Embeddings), PyMuPDF (Parsing).
- **LLM**: Groq (Llama 3.1 8B & Llama 3.3 70B).

## ⚙️ Local Setup

### Prerequisites
    ```bash
    chmod +x scripts/deploy_aws.sh
    ./scripts/deploy_aws.sh
    ```
4.  The script will prompt you for your `CLEARPATH_GROQ_API_KEY` and handle the rest (installing Docker, Nginx, and building the production stack).

---

## Features

- **RAG Pipeline**: PDF ingestion → chunk → embed (all-MiniLM-L6-v2) → FAISS → retrieve → generate
- **Deterministic Router**: Rule-based 6-node decision tree routes queries to 8B (simple) or 70B (complex) models — no LLM used for routing
- **Output Evaluator**: 3-check post-generation evaluation (context, refusal, hallucination detection)
- **SSE Streaming**: Real-time token streaming from Groq to the browser
- **Debug Panel**: In-browser debug metadata (classification, model, tokens, latency, evaluator flags)
- **Structured Logging**: JSONL append-only query logs with rotation

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full blueprint.

## Prerequisites

| Tool | Version |
|---|---|
| Python | 3.11+ |
| Node.js | 18+ |
| npm | 9+ |
| Groq API Key | [Get one free at console.groq.com](https://console.groq.com) |

## Setup

### 1. Clone the repository
```bash
git clone <repo-url>
cd Lemnisca_chatbot
```

### 2. Create Python virtual environment and install dependencies
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

### 3. Configure environment variables
```bash
cp .env.example .env
# Edit .env and add your CLEARPATH_GROQ_API_KEY
```

Required variables:
```env
CLEARPATH_GROQ_API_KEY=gsk_...
CLEARPATH_ALLOWED_ORIGINS=http://localhost:5173
CLEARPATH_LOG_LEVEL=INFO
```

### 4. Install frontend dependencies
```bash
cd frontend
npm install
cd ..
```

### 5. Ingest PDF documents
```bash
# Place your PDFs in backend/data/pdfs/
source venv/bin/activate
python scripts/ingest_all_pdfs.py
```

### 6. Start the development servers
```bash
bash scripts/run_dev.sh
```

The app will be available at:
- **Frontend**: [http://localhost:5173](http://localhost:5173)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

## Usage

1. Open the frontend at `http://localhost:5173`
2. Type a question in the input bar and press **Enter** or the send button
3. The assistant will respond using context from your ingested PDFs
4. Click **Debug** in the header to inspect classification, model, tokens, and evaluator flags

## API Reference

See [docs/api_reference.md](docs/api_reference.md) for full endpoint documentation.

## Development

### Run backend tests
```bash
source venv/bin/activate
python -m pytest tests/backend/ -v
```

### Run frontend tests
```bash
cd frontend
npm test
```

### Run with coverage
```bash
python -m pytest tests/backend/ --cov=backend --cov-report=term-missing
cd frontend && npm run test:coverage
```

### Validate FAISS index integrity
```bash
python scripts/validate_index.py
```

### Run with Docker
```bash
docker compose up --build
```

## License

MIT
