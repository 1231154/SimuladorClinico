# SimuladorClinico - AI Service (Python)

## Overview

FastAPI-based AI service for LLM orchestration with LangChain integration.

**Port**: `5555`

## Architecture

```
.NET API (5070)
     ↓ HTTP
Python AI Service (5555) - FastAPI + LangChain
     ↓ HTTP
Ollama (11434) - Mistral 7B Model
```

## Setup

### 1. Install Python 3.10+
```powershell
python --version  # Must be 3.10 or higher
```

### 2. Install Dependencies
```powershell
cd python
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Configure Environment
Edit `python/.env`:
```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral:latest
USE_KNOWLEDGE=true
KNOWLEDGE_PATH=../docs/knowledge
PYTHON_AI_PORT=5555
```

## Running

### Development Mode
```powershell
cd python
.\venv\Scripts\Activate.ps1
python main.py
```

### Via Script
```powershell
.\scripts\start-ai-service.ps1
```

## API Endpoints

### Health Check
```bash
GET http://localhost:5555/health
```

### Generate Response
```bash
POST http://localhost:5555/api/ai/generate
Content-Type: application/json

{
  "sessao_id": "uuid",
  "user_message": "I have shortness of breath",
  "context": null,
  "max_tokens": 512
}
```

### Get Available Models
```bash
GET http://localhost:5555/api/ai/models
```

### Load Knowledge Base
```bash
GET http://localhost:5555/api/ai/knowledge/load
```

## Features

- **LangChain Integration**: Advanced LLM orchestration and chaining
- **Vector Store (FAISS)**: Semantic search over documents
- **FastEmbedEmbeddings**: Fast and efficient embeddings
- **Async Support**: Full async/await for better performance
- **Knowledge Base**: Automatic loading from `docs/knowledge/`
- **CORS**: Configured for local development

## Configuration

All settings via environment variables in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server address |
| `OLLAMA_MODEL` | `mistral:latest` | Model to use |
| `USE_KNOWLEDGE` | `true` | Enable knowledge base |
| `KNOWLEDGE_PATH` | `docs/knowledge` | Path to knowledge documents |
| `KNOWLEDGE_MAX_CHARS` | `4000` | Max chars from knowledge |
| `PYTHON_AI_HOST` | `0.0.0.0` | Service host |
| `PYTHON_AI_PORT` | `5555` | Service port |
| `ENVIRONMENT` | `development` | Environment (development/production) |

## Knowledge Base

Place markdown or text files in `docs/knowledge/`:

```
docs/knowledge/
├── asma.md
├── covid.md
├── diabetes.md
└── clinical_protocols.txt
```

Automatically loaded and indexed on startup. Documents are chunked and indexed in FAISS vector store for semantic search.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Ollama not found" | Ensure Ollama is running on 11434 |
| "Port 5555 already in use" | Change `PYTHON_AI_PORT` in `.env` |
| "No module named langchain" | Run `pip install -r requirements.txt` |
| "FAISS import error" | Run `pip install faiss-cpu` |
| "Slow embeddings" | Use FastEmbedEmbeddings (already configured) |

## Integration with .NET

The .NET API calls this service at:
```
http://localhost:5555/api/ai/generate
```

See `SimuladorClinico.Api/Services/AIPythonServiceClient.cs` for implementation.

## Docs

Interactive API docs available at:
```
http://localhost:5555/docs (Swagger UI)
http://localhost:5555/redoc (ReDoc)
```

## Performance

- **Startup time**: ~10-15 seconds (first FAISS index creation)
- **Response time**: Depends on Ollama (10-30s on CPU)
- **Memory**: ~2-3 GB (Ollama + vector store + LangChain)

## Next Steps

1. Integrate additional models (GPT, Claude via API)
2. Add conversation memory (chat history)
3. Implement fine-tuning pipeline
4. Add streaming responses
5. Deploy with Docker + GPU support

---

**Created**: 29/04/2026  
**Version**: 1.0.0
