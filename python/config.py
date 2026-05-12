"""
Configuration for AI Service using environment variables
"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    # Ollama settings
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral:latest")
    
    # Knowledge base
    USE_KNOWLEDGE = os.getenv("USE_KNOWLEDGE", "true").lower() == "true"
    KNOWLEDGE_PATH = os.getenv("KNOWLEDGE_PATH", "docs/knowledge")
    KNOWLEDGE_MAX_CHARS = int(os.getenv("KNOWLEDGE_MAX_CHARS", "40000"))
    
    # System prompt
    SYSTEM_PROMPT = os.getenv(
        "SYSTEM_PROMPT",
        "Você é um simulador de paciente realista e pedagógico. Responda em português, de forma breve e clara, mantendo consistência."
    )
    
    # API settings
    PYTHON_AI_HOST = os.getenv("PYTHON_AI_HOST", "0.0.0.0")
    PYTHON_AI_PORT = int(os.getenv("PYTHON_AI_PORT", 5555))
    
    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = ENVIRONMENT == "development"
