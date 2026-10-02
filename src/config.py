import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_GUIDELINES_DIR = DATA_DIR / "raw_guidelines"
CHROMA_PERSIST_DIR = DATA_DIR / "chromadb"
WEB_DIR = BASE_DIR / "web"

# Load .env file automatically
load_dotenv(dotenv_path=BASE_DIR / ".env")

class Settings(BaseModel):
    app_name: str = "CancerTwin AI"
    app_version: str = "0.1.0"
    app_env: str = os.getenv("APP_ENV", "development")
    
    # Server settings
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = int(os.getenv("PORT", "8000"))
    
    # Vector store (ChromaDB)
    chroma_persist_dir: str = str(CHROMA_PERSIST_DIR)
    chroma_collection_name: str = os.getenv("CHROMA_COLLECTION_NAME", "oncology_guidelines")
    
    # LLM Provider & Model Selection
    llm_provider: str = os.getenv("LLM_PROVIDER", "groq")  # 'groq', 'gemini', 'openai', 'mock'
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_base_url: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
    
    # Explicit Token Budgeting Controls
    llm_max_input_tokens: int = int(os.getenv("LLM_MAX_INPUT_TOKENS", "2048"))
    llm_max_output_tokens: int = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", os.getenv("LLM_MAX_TOKENS", "1024")))
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))

settings = Settings()
