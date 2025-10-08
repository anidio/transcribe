import os
import re
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Optional, Annotated

# FastAPI / Starlette
from fastapi import FastAPI, APIRouter, HTTPException, Request, Header
from starlette.middleware.cors import CORSMiddleware
from ipware import get_client_ip # Para capturar o IP

# MongoDB
from motor.motor_asyncio import AsyncIOMotorClient
from motor.core import AgnosticCollection

# Pydantic / Tipagem
from pydantic import BaseModel, Field
import uuid
from datetime import datetime, timezone, timedelta 

# Gemini / YT Transcript
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai
from google.genai import types
from google.genai import errors as genai_errors 

# --- Configuração Inicial e Variáveis de Ambiente ---
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Variáveis de Configuração de Monetização
MAX_REQUESTS_PER_HOUR = 5 
RATE_LIMIT_DURATION_SECONDS = 3600 # 60 minutos

# Chave Pro para Bypass
PRO_API_KEY = os.environ.get('PRO_API_KEY')
if not PRO_API_KEY:
    logging.warning("PRO_API_KEY não configurada. A funcionalidade Pro não será habilitada.")

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')
client = None
db = None
if not mongo_url:
    logging.warning("MONGO_URL not found. Database will not be functional.")
else:
    try:
        client = AsyncIOMotorClient(mongo_url)
        db_name = os.environ.get('DB_NAME', 'youtube_summary_db')
        db = client[db_name]
    except Exception as e:
        logging.error(f"Failed to connect to MongoDB at startup: {e}")
        client = None
        db = None

# LLM Configuration
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
gemini_client = None
try:
    if GEMINI_API_KEY:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    else:
        logging.warning("GEMINI_API_KEY não configurada. A integração com IA pode falhar.")

except Exception as e:
    logging.error(f"Erro ao inicializar o cliente Gemini: {e}")
    gemini_client = None


# --- Modelos de Dados ---
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


# --- Lógica de Rate Limiting com Bypass (Monetização) ---

async def check_rate_limit(
    collection: AgnosticCollection, 
    client_id: str,
    pro_key_header: Optional[str] = None # Novo parâmetro para o cabeçalho
):
    """Verifica e atualiza o limite de requisições por IP na última hora, com bypass Pro."""
    
    # 1. BYPASS PRO KEY: Se a chave Pro for enviada e for válida, ignora o limite.
    if pro_key_header and pro_key_header == PRO_API_KEY:
        logging.info(f"PRO_API_KEY valid. Bypassing rate limit for client: {client_id}")
        return
    
    if db is None:
        logging.warning("DB is None. Skipping rate limit check.")
        return
    
    current_time = datetime.now(timezone.utc)
    one_hour_ago = current_time - timedelta(seconds=RATE_LIMIT_DURATION_SECONDS)
    
    # Limpa entradas antigas (mais de uma hora)
    await collection.delete_many({
        "client_id": client_id,
        "timestamp": {"$lt": one_hour_ago}
    })
    
    # Conta as requisições restantes
    request_count = await collection.count_documents({
        "client_id": client_id
    })
    
    if request_count >= MAX_REQUESTS_PER_HOUR:
        # Limite excedido
        logging.warning(f"Rate limit exceeded for client: {client_id}")
        raise HTTPException(
            status_code=429, 
            detail=f"Limite de requisições ({MAX_REQUESTS_PER_HOUR}/hora) excedido. Faça upgrade para a Versão Pro para uso ilimitado!",
        )
    
    # Registra a nova requisição
    await collection.insert_one({
        "client_id": client_id,
        "timestamp": current_time,
        "type": "ai_call"
    })


# --- Funções de Negócio ---

def extract_video_id(url: str) -> str:
    """Extrai o ID do vídeo de diversas URLs do YouTube"""
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
    """Get YouTube transcript with fallback languages and proxy support."""
    
    proxy_url = os.environ.get('TRANSCRIPTION_PROXY')
    proxies = {'http': proxy_url, 'https': proxy_url} if proxy_url else None

    try:
        # Tenta buscar PT e EN (o método 'get_transcript' é estático)
        transcript_list = YouTubeTranscriptApi.get_transcript(
            video_id, 
            languages=['pt', 'en', 'pt-BR', 'en-US'],
            # proxies=proxies # NOTE: A lib youtube-transcript-api só aceita proxies se instalada com um fork ou versão mais antiga. Removido o argumento para não causar erro, dependendo do deploy.
        )
        transcript_text = ' '.join([entry['text'] for entry in transcript_list])
        return transcript_text
        
    except Exception as e:
        logging.error(f"Erro na transcrição: {e}")
        # Erro de bloqueio de IP da Cloud ou falha no proxy
        raise HTTPException(status_code=400, detail=f"Não foi possível obter a transcrição. (ID de vídeo inválido ou erro de API): {str(e)}")

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


# --- Configuração do FastAPI ---
app = FastAPI()
api_router = APIRouter(prefix="/api")


# --- ROTAS DA API ---

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
        if db is not None:
            await db.videos.insert_one(video_response.dict())
        else:
            logging.warning("Database client is not available. Skipping save operation.")
            
        return video_response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Erro interno no /transcribe: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@api_router.post("/videos/summarize", response_model=ProcessResult)
async def summarize_text(
    request: TranscriptRequest, 
    request_info: Request,
    x_pro_key: Annotated[Optional[str], Header(alias="X-PRO-KEY")] = None # Lê o cabeçalho PRO
): 
    """Summarize transcript text"""
    
    # --- Lógica de Rate Limiting ---
    client_ip, _ = get_client_ip(request_info.headers)
    if client_ip:
        # Passa a chave PRO para check_rate_limit
        await check_rate_limit(db.rate_limits, client_ip, x_pro_key)
    # --- Fim Rate Limiting ---

    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Texto não pode estar vazio")
            
        summary = await process_with_ai(request.text, "summarize")
        
        result = ProcessResult(result=summary)
        if db is not None:
            await db.summaries.insert_one(result.dict())
        
        return result
        
    except Exception as e:
        if isinstance(e, HTTPException):
            # Se for um erro de Rate Limit (429), propaga
            raise e
        raise HTTPException(status_code=500, detail=f"Erro ao processar resumo: {str(e)}")

@api_router.post("/videos/enrich", response_model=ProcessResult)  
async def enrich_text(
    request: TranscriptRequest, 
    request_info: Request,
    x_pro_key: Annotated[Optional[str], Header(alias="X-PRO-KEY")] = None # Lê o cabeçalho PRO
): 
    """Enrich and enhance transcript text"""
    
    # --- Lógica de Rate Limiting ---
    client_ip, _ = get_client_ip(request_info.headers)
    if client_ip:
        # Passa a chave PRO para check_rate_limit
        await check_rate_limit(db.rate_limits, client_ip, x_pro_key)
    # --- Fim Rate Limiting ---

    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Texto não pode estar vazio")
            
        enrichment = await process_with_ai(request.text, "enrich")
        
        result = ProcessResult(result=enrichment)
        if db is not None:
            await db.enrichments.insert_one(result.dict())
        
        return result
        
    except Exception as e:
        if isinstance(e, HTTPException):
            # Se for um erro de Rate Limit (429), propaga
            raise e
        raise HTTPException(status_code=500, detail=f"Erro ao processar aprimoramento: {str(e)}")

@api_router.get("/videos", response_model=List[VideoResponse])
async def get_videos():
    """Get all processed videos"""
    if db is None:
        raise HTTPException(status_code=500, detail="Conexão com o banco de dados indisponível.")
    
    videos = await db.videos.find().to_list(100)
    return [VideoResponse(**video) for video in videos]

# Inclui o router no main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configura o logging (mantenha)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    if client:
        client.close()