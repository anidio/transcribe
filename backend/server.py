from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import re

# Imports para Gemini
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai
from google.genai import types
from google.genai import errors as genai_errors 

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')
if not mongo_url:
    logging.warning("MONGO_URL not found in .env. Database will not be functional.")
    client = None
    db = None
else:
    try:
        client = AsyncIOMotorClient(mongo_url)
        db_name = os.environ.get('DB_NAME', 'youtube_summary_db')
        db = client[db_name]
    except Exception as e:
        logging.error(f"Failed to connect to MongoDB at startup: {e}")
        client = None
        db = None


# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# LLM Configuration
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Inicializa o cliente Gemini globalmente
try:
    if GEMINI_API_KEY:
        # Note: A biblioteca google-genai pode usar a variável GEMINI_API_KEY do ambiente automaticamente.
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    else:
        gemini_client = None
        logging.warning("GEMINI_API_KEY não configurada. A integração com IA pode falhar.")

except Exception as e:
    logging.error(f"Erro ao inicializar o cliente Gemini: {e}")
    gemini_client = None


# Define Models
class VideoRequest(BaseModel):
    url: str

class TranscriptRequest(BaseModel):
    text: str

class VideoResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: str
    transcript: str
    summary: Optional[str] = None
    enrichment: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProcessResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    result: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

def extract_video_id(url: str) -> str:
    """Extract YouTube video ID from URL"""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&\n?#]+)',
        r'youtube\.com/embed/([^&\n?#]+)',
        r'youtube\.com/v/([^&\n?#]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    raise ValueError("Invalid YouTube URL")

async def get_youtube_transcript(video_id: str) -> str:
    """Get YouTube transcript with fallback languages"""
    try:
        api = YouTubeTranscriptApi()
        
        # Try Portuguese first, then English
        for lang_codes in [['pt'], ['en'], ['pt-BR'], ['en-US']]:
            try:
                transcript = api.fetch(video_id, languages=lang_codes)
                transcript_text = ' '.join([entry.text for entry in transcript])
                return transcript_text
            except:
                continue
                
        # If no specific language works, try default (English)
        transcript = api.fetch(video_id, languages=['en'])
        transcript_text = ' '.join([entry.text for entry in transcript])
        return transcript_text
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Não foi possível obter a transcrição: {str(e)}")

async def process_with_ai(text: str, task: str) -> str:
    """Process text with AI using Google Generative AI (Gemini) direct client"""
    
    if gemini_client is None:
        raise HTTPException(status_code=500, detail="Cliente Gemini não inicializado. Verifique a GEMINI_API_KEY.")
    
    system_messages = {
        "summarize": "Você é um especialista em resumir conteúdo de vídeos do YouTube. Crie resumos claros, estruturados e informativos em português brasileiro.",
        "enrich": "Você é um especialista em aprimorar e enriquecer conteúdo. Adicione insights, organize melhor as informações e forneça contexto adicional valioso em português brasileiro."
    }
    
    prompts = {
        "summarize": f"""
Analise o seguinte texto de um vídeo do YouTube e crie um resumo estruturado:

**TEXTO:**
{text}

**INSTRUÇÕES:**
- Crie um resumo em português brasileiro
- Use tópicos organizados com bullet points
- Destaque os pontos principais
- Mantenha entre 200-500 palavras
- Use formatação markdown para melhor apresentação

**ESTRUTURA ESPERADA:**
## 📝 Resumo Executivo
## 🎯 Pontos Principais
## 💡 Insights Importantes
## 📋 Conclusão
""",
        "enrich": f"""
Analise o seguinte texto e crie uma versão aprimorada e enriquecida:

**TEXTO:**
{text}

**INSTRUÇÕES:**
- Organize o conteúdo de forma mais estruturada
- Adicione insights e contexto relevante
- Inclua possíveis aplicações práticas
- Use formatação markdown
- Responda em português brasileiro
- Expanda conceitos importantes

**ESTRUTURA ESPERADA:**
## 🚀 Conteúdo Aprimorado
## 🔍 Análise Detalhada
## 💼 Aplicações Práticas
## 🎓 Conceitos Chave
## 📈 Próximos Passos
"""
    }
    
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                prompts[task]
            ],
            config=types.GenerateContentConfig(
                system_instruction=system_messages[task]
            )
        )
        
        # Verifica se o conteúdo foi bloqueado
        if response.candidates and response.candidates[0].finish_reason.name == 'SAFETY':
             return "O conteúdo da transcrição foi bloqueado pelas políticas de segurança do modelo Gemini."
             
        return response.text
        
    except genai_errors.APIError as e:
        logging.error(f"Erro de API com Gemini: {e}")
        # A API Error geralmente significa chave inválida ou erro de cota
        raise HTTPException(status_code=500, detail="Erro de API com Gemini. Verifique se a GEMINI_API_KEY é válida ou se a cota foi excedida (grátis).")
    except Exception as e:
        logging.error(f"Erro ao processar com Gemini: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar com Gemini: {str(e)}")


# API Routes
@api_router.get("/")
async def root():
    return {"message": "YouTube Video AI Processor API"}

@api_router.post("/videos/transcribe", response_model=VideoResponse)
async def transcribe_video(request: VideoRequest):
    """Transcribe YouTube video"""
    try:
        video_id = extract_video_id(request.url)
        transcript = await get_youtube_transcript(video_id)
        
        video_response = VideoResponse(
            url=request.url,
            transcript=transcript
        )
        
        # Save to database
        # CORREÇÃO CRÍTICA: Mudança de 'if db:' para 'if db is not None:'
        if db is not None:
            await db.videos.insert_one(video_response.dict())
        else:
            logging.warning("Database client is not available. Skipping save operation.")
            
        return video_response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Erro interno, pode ser do DB
        logging.error(f"Erro interno no /transcribe: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@api_router.post("/videos/summarize", response_model=ProcessResult)
async def summarize_text(request: TranscriptRequest):
    """Summarize transcript text"""
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Texto não pode estar vazio")
            
        summary = await process_with_ai(request.text, "summarize")
        
        result = ProcessResult(result=summary)
        # CORREÇÃO CRÍTICA: Mudança de 'if db:' para 'if db is not None:'
        if db is not None:
            await db.summaries.insert_one(result.dict())
        
        return result
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Erro ao processar resumo: {str(e)}")

@api_router.post("/videos/enrich", response_model=ProcessResult)  
async def enrich_text(request: TranscriptRequest):
    """Enrich and enhance transcript text"""
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Texto não pode estar vazio")
            
        enrichment = await process_with_ai(request.text, "enrich")
        
        result = ProcessResult(result=enrichment)
        # CORREÇÃO CRÍTICA: Mudança de 'if db:' para 'if db is not None:'
        if db is not None:
            await db.enrichments.insert_one(result.dict())
        
        return result
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Erro ao processar aprimoramento: {str(e)}")

@api_router.get("/videos", response_model=List[VideoResponse])
async def get_videos():
    """Get all processed videos"""
    # CORREÇÃO CRÍTICA: Mudança de 'if not db:' para 'if db is None:'
    if db is None:
        raise HTTPException(status_code=500, detail="Conexão com o banco de dados indisponível.")
    
    videos = await db.videos.find().to_list(100)
    return [VideoResponse(**video) for video in videos]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    if client:
        client.close()