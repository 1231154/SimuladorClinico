# Arquitetura Híbrida .NET + Python - SimuladorClinico

## Visão Geral

A arquitetura agora é **híbrida**, separando as responsabilidades:

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React/TypeScript)           │
│                     http://localhost:5173               │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP
┌────────────────────▼────────────────────────────────────┐
│         .NET API (SimuladorClinico.Api)                 │
│              http://localhost:5070                      │
│                                                          │
│  Responsabilidades:                                     │
│  - Endpoints REST: /api/simulacoes/sessoes             │
│  - Orquestração de negócio                             │
│  - Gestão de sessões                                   │
│  - Integração com dados                                │
│  - CORS, autenticação, logging                         │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP (HttpClient)
┌────────────────────▼────────────────────────────────────┐
│    Python AI Service (FastAPI + LangChain)             │
│          http://localhost:5555                          │
│                                                          │
│  Responsabilidades:                                     │
│  - Orquestração de LLM com LangChain                   │
│  - Gerenciamento de conhecimento (RAG)                 │
│  - Vector Store (FAISS) para busca semântica           │
│  - Integração com Ollama                               │
│  - Processamento de embeddings                         │
│  - Análise e avaliação de respostas                    │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP
┌────────────────────▼────────────────────────────────────┐
│            Ollama (Inference Engine)                    │
│           http://localhost:11434                        │
│                                                          │
│  - Modelo: mistral:latest (4.4 GB)                     │
│  - Respostas em ~10-30s (CPU)                          │
│  - Suporta GPU com CUDA                                │
└──────────────────────────────────────────────────────────┘
```

## Componentes

### 1. Frontend (React/TypeScript/Vite)
- **Localização**: `src/SimuladorClinico.Web/`
- **Porta**: 5173
- **Tecnologias**: React 18, TypeScript, Vite
- **Responsabilidades**:
  - UI do simulador clínico
  - Interação do utilizador
  - Chamadas à API .NET via Vite proxy

### 2. Backend .NET (ASP.NET Core 8.0)
- **Localização**: `src/SimuladorClinico.Api/`
- **Porta**: 5070
- **Arquitektura**: Clean Architecture com DDD
- **Camadas**:
  - `SimuladorClinico.Api` - Controllers e endpoints REST
  - `SimuladorClinico.Application` - Lógica de negócio
  - `SimuladorClinico.Domain` - Entidades e regras de negócio
  - `SimuladorClinico.Infrastructure` - Serviços e integrações
- **Responsabilidades**:
  - Endpoints REST (POST /api/simulacoes/sessoes)
  - Orquestração de negócio
  - Chamadas ao serviço Python AI
  - Gestão de sessões
  - Logging e CORS

### 3. Python AI Service (FastAPI + LangChain)
- **Localização**: `python/`
- **Porta**: 5555
- **Servidor**: Uvicorn
- **Tecnologias**: FastAPI, LangChain, FAISS, Ollama
- **Ficheiros principais**:
  - `main.py` - Aplicação FastAPI
  - `ai_service.py` - Lógica de IA com LangChain
  - `config.py` - Configuração
  - `.env` - Variáveis de ambiente
  - `requirements.txt` - Dependências Python

#### Funcionalidades:
- **LangChain Integration**: Orquestração avançada de LLM
- **RAG (Retrieval Augmented Generation)**: Busca semântica em conhecimento
- **Vector Store (FAISS)**: Indexação de documentos em `docs/knowledge/`
- **FastEmbedEmbeddings**: Embeddings rápidos e eficientes
- **Async Support**: Request handling assíncrono para melhor performance
- **Auto-loading**: Carrega automaticamente conhecimento ao iniciar

#### Endpoints:
- `GET /health` - Health check
- `POST /api/ai/generate` - Gerar resposta do LLM
- `GET /api/ai/models` - Listar modelos disponíveis
- `GET /api/ai/knowledge/load` - Carregar base de conhecimento
- `GET /docs` - Swagger API documentation

### 4. Ollama (Inference Engine)
- **Localização**: Serviço do sistema operativo
- **Porta**: 11434
- **Modelo**: mistral:latest (4.4 GB)
- **Performance**:
  - CPU: 10-30 segundos por resposta
  - GPU CUDA: 2-5 segundos por resposta

## Fluxo de Dados

### 1. Utilizador Envia Mensagem
```
Frontend (React)
    ↓ POST /api/simulacoes/sessoes/{id}/mensagens
.NET API
    ↓ HttpClient POST http://localhost:5555/api/ai/generate
Python AI Service (FastAPI)
    ↓ LangChain + FAISS retrieval
    ↓ Context building
    ↓ HTTP POST to Ollama
Ollama
    ↓ Modelo Mistral gera resposta
    ↓ Streaming response (NDJSON)
Python AI Service
    ↓ Processa e retorna JSON
.NET API
    ↓ Persiste em base de dados
Frontend
    ↓ Exibe resposta
Utilizador vê resposta do "paciente"
```

## Benefícios da Arquitetura Híbrida

### .NET Recebe:
- ✅ Clean Architecture clara
- ✅ API REST estruturada
- ✅ Tipagem forte
- ✅ Ecosystem enterprise
- ✅ Fácil testes unitários
- ✅ Logging integrado

### Python Recebe:
- ✅ Flexibilidade para ML/AI
- ✅ LangChain ecosystem
- ✅ Vector stores (FAISS, Pinecone, etc)
- ✅ RAG capabilities
- ✅ Fácil fine-tuning
- ✅ Data science libraries

### Separação de Concerns:
- ✅ Backend cuida de regras de negócio
- ✅ Python cuida de IA/LLM
- ✅ Cada um usa melhor tecnologia para seu caso
- ✅ Escalável independentemente
- ✅ Deploy desacoplado

## Configuração e Variáveis de Ambiente

### .NET (appsettings.Development.json)
```json
{
  "LLM": {
    "SystemPrompt": "..."
  },
  "USE_KNOWLEDGE": "true",
  "KNOWLEDGE_PATH": "docs/knowledge",
  "KNOWLEDGE_MAX_CHARS": "4000"
}
```

### Python (python/.env)
```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral:latest
USE_KNOWLEDGE=true
KNOWLEDGE_PATH=../docs/knowledge
KNOWLEDGE_MAX_CHARS=4000
PYTHON_AI_HOST=0.0.0.0
PYTHON_AI_PORT=5555
```

## Como Iniciar

### Automático (Recomendado)
```powershell
./scripts/start-all.ps1
```

Abre 4 janelas PowerShell:
1. Ollama
2. Python AI Service
3. Backend .NET
4. Frontend React

### Manual

Terminal 1 - Ollama:
```powershell
ollama run mistral:latest
```

Terminal 2 - Python AI Service:
```powershell
./scripts/start-ai-service.ps1
```

Terminal 3 - Backend .NET:
```powershell
cd src/SimuladorClinico.Api
dotnet run
```

Terminal 4 - Frontend:
```powershell
cd src/SimuladorClinico.Web
npm install
npm run dev
```

## Próximas Melhorias

### Curto Prazo
- [ ] Adicionar historico de conversa (chat memory)
- [ ] Implementar rate limiting
- [ ] Adicionar autenticação/autorização
- [ ] Testes de integração .NET + Python

### Médio Prazo
- [ ] Suporte a múltiplos modelos (GPT, Claude via API)
- [ ] Fine-tuning de Mistral com dados clínicos
- [ ] Métricas de qualidade de resposta
- [ ] Dashboard de monitoramento
- [ ] Dockerização (Docker Compose)

### Longo Prazo
- [ ] Deploy em produção com GPU
- [ ] Suporte a streaming responses
- [ ] Base de dados vetorial (Pinecone, Weaviate)
- [ ] Integração com EHR/EMR systems
- [ ] Multi-language support
- [ ] Evaluation framework com IA

## Troubleshooting

| Problema | .NET | Python | Solução |
|----------|------|--------|---------|
| "Connection refused" | ✓ |  | Python não está rodando |
| "Timeout" |  | ✓ | Ollama lento, aumentar timeout |
| "No module named" |  | ✓ | `pip install -r requirements.txt` |
| "Port already in use" | ✓ | ✓ | Mudar porta em config |

## Monitoring

### .NET API
- Logs: Console e ficheiros
- Swagger: http://localhost:5070/swagger

### Python AI Service
- Logs: Console (uvicorn)
- Interactive docs: http://localhost:5555/docs
- ReDoc: http://localhost:5555/redoc

### Ollama
- Status: `/api/tags` endpoint
- Models: Verificar com `ollama list`

## Performance

| Componente | Startup | Memory | CPU |
|-----------|---------|--------|-----|
| Ollama | 5-10s | 4.4 GB | High during inference |
| Python AI | 10-15s | 500 MB | Low in idle |
| .NET API | 2-3s | 250 MB | Low in idle |
| Frontend | 2-3s | 100 MB (browser) | Low in idle |

**Total Response Time**: 15-45 segundos (Ollama domina)

---

**Data**: 29/04/2026  
**Versão**: 1.0.0  
**Status**: Em Desenvolvimento ✓
