"""
SimuladorClinico - AI Service (Python)
FastAPI service for LLM orchestration with LangChain
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

from ai_service import AIService

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global AI Service instance
ai_service: Optional[AIService] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for FastAPI app"""
    global ai_service
    # Startup
    logger.info("Initializing AI Service...")
    ai_service = AIService()
    await ai_service.initialize()
    logger.info("AI Service initialized")
    yield
    # Shutdown
    logger.info("Shutting down AI Service...")
    await ai_service.shutdown()

# FastAPI app
app = FastAPI(
    title="SimuladorClinico - AI Service",
    description="LLM orchestration and management",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5070",
        "http://127.0.0.1:5070",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class GenerateResponseRequest(BaseModel):
    sessao_id: str
    user_message: str
    context: Optional[str] = None
    max_tokens: Optional[int] = 512
    disease: Optional[str] = None  # Nova: permite especificar a doença
    force_new_persona: Optional[bool] = False  # Se true, força atribuição de novo registo (.md)

class GenerateResponseResponse(BaseModel):
    response: str
    tokens_used: int
    model: str
    case_id: Optional[int] = None
    disease: str = "unknown"  # Nova: retorna a doença da sessão

class HealthResponse(BaseModel):
    status: str
    service: str
    ollama_status: str
    model: str

# Routes
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        ollama_status = "ok" if ai_service and await ai_service.check_ollama_health() else "unavailable"
    except Exception as e:
        logger.error(f"Ollama health check failed: {e}")
        ollama_status = "error"

    return HealthResponse(
        status="ok",
        service="ai-service",
        ollama_status=ollama_status,
        model=os.getenv("OLLAMA_MODEL", "mistral:latest")
    )

@app.post("/api/ai/generate", response_model=GenerateResponseResponse)
async def generate_response(request: GenerateResponseRequest):
    """Generate AI response using Ollama"""
    if not ai_service:
        raise HTTPException(status_code=500, detail="AI Service not initialized")

    try:
        logger.info(f"Generating response for session {request.sessao_id}")
        # Se o cliente pediu força de nova persona (por exemplo em refresh), atribui um novo registo
        if request.force_new_persona:
            ai_service.clear_session_history(request.sessao_id)
            await ai_service.start_roleplay_session(request.sessao_id, force_new=True)
        response = await ai_service.generate_response(
            sessao_id=request.sessao_id,
            user_message=request.user_message,
            context=request.context,
            max_tokens=request.max_tokens,
            disease=request.disease  # Novo: passar disease se for especificado
        )
        return response
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai/models")
async def get_available_models():
    """Get available models"""
    if not ai_service:
        raise HTTPException(status_code=500, detail="AI Service not initialized")

    try:
        models = await ai_service.get_available_models()
        return {"models": models}
    except Exception as e:
        logger.error(f"Error fetching models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai/knowledge/load")
async def load_knowledge():
    """Load and index knowledge base"""
    if not ai_service:
        raise HTTPException(status_code=500, detail="AI Service not initialized")

    try:
        result = await ai_service.load_knowledge_base()
        return result
    except Exception as e:
        logger.error(f"Error loading knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai/session/{sessao_id}/history")
async def get_session_history(sessao_id: str):
    """Get conversation history for a session"""
    if not ai_service:
        raise HTTPException(status_code=500, detail="AI Service not initialized")

    try:
        history = ai_service.get_session_history(sessao_id)
        return history
    except Exception as e:
        logger.error(f"Error retrieving session history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/ai/session/{sessao_id}/history")
async def clear_session_history(sessao_id: str):
    """Clear conversation history for a session"""
    if not ai_service:
        raise HTTPException(status_code=500, detail="AI Service not initialized")

    try:
        result = ai_service.clear_session_history(sessao_id)
        return result
    except Exception as e:
        logger.error(f"Error clearing session history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai/session/{sessao_id}/start-roleplay")
async def start_roleplay(sessao_id: str):
    """Assign a random knowledge .md record as persona for the session"""
    if not ai_service:
        raise HTTPException(status_code=500, detail="AI Service not initialized")

    try:
        ai_service.clear_session_history(sessao_id)
        result = await ai_service.start_roleplay_session(sessao_id, force_new=True)
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except Exception as e:
        logger.error(f"Error starting roleplay for session {sessao_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai/diseases")
async def get_available_diseases():
    """Get list of available diseases"""
    if not ai_service:
        raise HTTPException(status_code=500, detail="AI Service not initialized")

    try:
        return ai_service.get_available_diseases()
    except Exception as e:
        logger.error(f"Error fetching diseases: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai/session/{sessao_id}/disease")
async def get_session_disease(sessao_id: str):
    """Get current disease for a session"""
    if not ai_service:
        raise HTTPException(status_code=500, detail="AI Service not initialized")

    try:
        return ai_service.get_session_disease(sessao_id)
    except Exception as e:
        logger.error(f"Error fetching session disease: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/session/{sessao_id}/disease/{disease}")
async def set_session_disease(sessao_id: str, disease: str):
    """Set/change disease for a session"""
    if not ai_service:
        raise HTTPException(status_code=500, detail="AI Service not initialized")

    try:
        result = ai_service.set_session_disease(sessao_id, disease)
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except Exception as e:
        logger.error(f"Error setting session disease: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "SimuladorClinico AI Service",
        "version": "1.0.0",
        "features": [
            "Single isolated clinical case per session",
            "Session memory (conversation history)",
            "Random case selection from mental_health_data.py",
            "Ollama LLM integration",
            "Roleplay enforcement"
        ],
        "endpoints": {
            "health": "/health",
            "generate": "/api/ai/generate (POST)",
            "models": "/api/ai/models",
            "knowledge_load": "/api/ai/knowledge/load",
            "session_roleplay_start": "/api/ai/session/{sessao_id}/start-roleplay (POST)",
            "session_history": "/api/ai/session/{sessao_id}/history (GET)",
            "session_clear": "/api/ai/session/{sessao_id}/history (DELETE)",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PYTHON_AI_PORT", 5555))
    host = os.getenv("PYTHON_AI_HOST", "0.0.0.0")

    logger.info(f"Starting AI Service on {host}:{port}")
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.getenv("ENVIRONMENT") == "development"
    )








