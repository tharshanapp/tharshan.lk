"""
OpenGov AI Assistant - FastAPI Backend
Main application file with API endpoints
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import local modules
from rag_engine import get_rag_engine, RAGEngine
from ingest import PDFIngester

# ==================== Configuration ====================

# Get configuration from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")

# Validate API key
if not GEMINI_API_KEY or GEMINI_API_KEY == "":
    logger.warning("GEMINI_API_KEY not set or invalid. AI features will not work.")
    logger.warning("Please set your Gemini API key in .env file")

if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY is missing.")
    raise ValueError("GEMINI_API_KEY environment variable is not set.")

if not ADMIN_TOKEN:
    logger.warning("ADMIN_TOKEN not set. Using default development token.")
    ADMIN_TOKEN = "003575"


# ==================== Gemini API Setup ====================

# Try to import and setup Gemini
try:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    GEMINI_AVAILABLE = True
    logger.info("Gemini API configured successfully")
except ImportError:
    logger.warning("Google Generative AI package not installed")
    gemini_model = None
    GEMINI_AVAILABLE = False
except Exception as e:
    logger.warning(f"Error configuring Gemini API: {e}")
    gemini_model = None
    GEMINI_AVAILABLE = False

# ==================== Data Models ====================

class AskRequest(BaseModel):
    """Request model for asking questions"""
    question: str = Field(..., min_length=1, max_length=2000)
    category: str = Field(..., pattern="^(FR|Procurement|ECode)$")
    
    @validator('question')
    def validate_question(cls, v):
        """Validate and clean question input"""
        v = v.strip()
        if not v:
            raise ValueError("Question cannot be empty")
        # Basic prompt injection prevention
        dangerous_patterns = [
            r'ignore\s+previous',
            r'you\s+are\s+now',
            r'system\s+instruction',
            r'output\s+your\s+instructions'
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Invalid question format")
        return v

class AskResponse(BaseModel):
    """Response model for AI answers"""
    answer: str
    sources: List[Dict[str, Any]]
    category: str
    timestamp: str

class UploadResponse(BaseModel):
    """Response model for file upload"""
    status: str
    message: str
    documents_processed: int
    chunks_created: int
    filename: str

class StatsResponse(BaseModel):
    """Response model for statistics"""
    category: str
    document_count: int
    collection_name: str

# ==================== Application Lifespan ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("OpenGov AI Assistant starting up...")
    # Initialize RAG engine
    try:
        rag_engine = get_rag_engine()
        logger.info("RAG engine initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG engine during startup: {e}")
        logger.error("The application will continue but database operations may fail")
    yield
    # Shutdown
    logger.info("OpenGov AI Assistant shutting down...")

# ==================== FastAPI App ====================

app = FastAPI(
    title="OpenGov AI Assistant",
    description="AI-powered assistant for Sri Lankan government financial regulations",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Security ====================

async def verify_admin_token(authorization: Optional[str] = Header(None)):
    """Verify admin token for protected endpoints"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    # Support both "Bearer token" and just "token"
    token = authorization
    if token.startswith("Bearer "):
        token = token[7:]
    
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid authorization token")
    
    return True

# ==================== API Endpoints ====================

@app.get("/api")
async def root():
    """Root API endpoint with API information"""
    return {
        "name": "OpenGov AI Assistant API",
        "version": "1.0.0",
        "description": "AI-powered assistant for Sri Lankan government financial regulations",
        "endpoints": {
            "ask": "/ask",
            "upload": "/admin/upload",
            "stats": "/stats/{category}",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        rag_engine = get_rag_engine()
        rag_available = True
        rag_error = None
    except Exception as e:
        logger.warning(f"RAG engine health check failed: {e}")
        rag_available = False
        rag_error = str(e)
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "gemini_available": GEMINI_AVAILABLE,
        "rag_engine_available": rag_available,
        "rag_engine_error": rag_error
    }

@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    Ask a question to the AI assistant
    
    Args:
        request: AskRequest with question and category
        
    Returns:
        AskResponse with AI answer and sources
    """
    try:
        # Get RAG engine
        try:
            rag_engine = get_rag_engine()
        except Exception as e:
            logger.error(f"Failed to get RAG engine: {e}")
            raise HTTPException(
                status_code=503,
                detail="Database connection error. RAG engine not available. Check server logs for details."
            )
        
        # Perform similarity search
        try:
            relevant_docs = rag_engine.similarity_search(
                query=request.question,
                category=request.category,
                k=5
            )
        except Exception as e:
            logger.error(f"Similarity search error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error searching documents: {str(e)}"
            )
        
        # Check if we found any relevant documents
        if not relevant_docs:
            return AskResponse(
                answer="I apologize, but I couldn't find any relevant information in the documents for your question. Please try rephrasing your question or ensure that relevant PDF documents have been uploaded.",
                sources=[],
                category=request.category,
                timestamp=datetime.now().isoformat()
            )
        
        # Build context from relevant documents
        context_parts = []
        sources = []
        
        for i, doc in enumerate(relevant_docs, 1):
            context_parts.append(f"[Source {i}] {doc['content']}")
            sources.append({
                "source": doc['metadata'].get('source', 'Unknown'),
                "page": doc['metadata'].get('page', 'N/A'),
                "relevance_score": round(1 - doc['distance'], 3) if doc['distance'] else 0.0
            })
        
        context = "\n\n".join(context_parts)
        
        # Build prompt for Gemini
        system_prompt = """You are an AI assistant for Sri Lankan government officers, specializing in Financial Regulations (FR), Procurement Guidelines, and Expenditure Codes (ECode). 

Your role is to provide accurate, professional answers based ONLY on the provided context from official documents. 

Guidelines:
- Answer based strictly on the provided context
- If the context doesn't contain the answer, say you don't have that information
- Be professional and clear
- Cite specific regulations or guidelines when possible
- Keep answers concise but comprehensive

Context from official documents:
{context}

User Question: {question}

Please provide a clear, accurate answer based on the context above."""

        full_prompt = system_prompt.format(
            context=context,
            question=request.question
        )
        
        # Generate response using Gemini
        if GEMINI_AVAILABLE and gemini_model:
            try:
                response = gemini_model.generate_content(full_prompt)
                answer = response.text
            except Exception as e:
                logger.error(f"Gemini API error: {e}")
                answer = "I apologize, but I encountered an error while processing your question. Please try again later."
        else:
            # Fallback response when Gemini is not available
            answer = (
                f"I found relevant information for your question about '{request.question}'.\n\n"
                f"Based on the documents, here are the key points:\n\n"
                f"{context[:1000]}...\n\n"
                f"Note: AI generation is currently unavailable. Please refer to the source documents above."
            )
        
        return AskResponse(
            answer=answer,
            sources=sources,
            category=request.category,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.post("/admin/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    category: str = Form(...),
    background_tasks: BackgroundTasks = None,
    authorization: Optional[str] = Header(None),
    _: bool = Depends(verify_admin_token)
):
    """
    Upload a PDF file for ingestion
    
    Args:
        file: PDF file to upload
        category: Category (FR, Procurement, ECode)
        authorization: Admin token
        
    Returns:
        UploadResponse with processing results
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Validate category
    if category not in ["FR", "Procurement", "ECode"]:
        raise HTTPException(status_code=400, detail="Invalid category")
    
    file_path = None
    try:
        # Create category folder if it doesn't exist
        category_folder = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "data", 
            category
        )
        os.makedirs(category_folder, exist_ok=True)
        logger.info(f"Category folder ready: {category_folder}")
        
        # Save file
        file_path = os.path.join(category_folder, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        logger.info(f"File saved: {file_path}")
        
        # Process the uploaded PDF
        try:
            ingester = PDFIngester()
            result = ingester.ingest_single_file(file_path, category)
            logger.info(f"Ingestion result: {result}")
        except Exception as e:
            logger.error(f"Error during PDF ingestion: {e}", exc_info=True)
            # Clean up uploaded file if ingestion fails
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up failed upload: {file_path}")
            raise HTTPException(status_code=500, detail=f"PDF processing failed: {str(e)}")
        
        if result['status'] == 'success':
            return UploadResponse(
                status="success",
                message=f"Successfully uploaded and processed {file.filename}",
                documents_processed=result['documents_processed'],
                chunks_created=result['chunks_created'],
                filename=file.filename
            )
        else:
            logger.warning(f"Ingestion returned non-success status: {result}")
            raise HTTPException(status_code=400, detail=result.get('message', 'Processing failed'))
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}", exc_info=True)
        # Clean up uploaded file if it exists
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up file: {file_path}")
        raise HTTPException(status_code=500, detail=f"Error processing upload: {str(e)}")

@app.get("/stats/{category}", response_model=StatsResponse)
async def get_stats(
    category: str,
    authorization: Optional[str] = Header(None),
    _: bool = Depends(verify_admin_token)
):
    """
    Get statistics for a category
    
    Args:
        category: Category name
        authorization: Admin token
        
    Returns:
        StatsResponse with collection statistics
    """
    try:
        rag_engine = get_rag_engine()
        stats = rag_engine.get_collection_stats(category)
        return StatsResponse(**stats)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/admin/clear/{category}")
async def clear_category(
    category: str,
    authorization: Optional[str] = Header(None),
    _: bool = Depends(verify_admin_token)
):
    """
    Clear all documents from a category
    
    Args:
        category: Category name
        authorization: Admin token
        
    Returns:
        Status message
    """
    try:
        rag_engine = get_rag_engine()
        result = rag_engine.clear_collection(category)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error clearing category: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/ingest/{category}")
async def ingest_category(
    category: str,
    authorization: Optional[str] = Header(None),
    _: bool = Depends(verify_admin_token)
):
    """
    Trigger ingestion for a category
    
    Args:
        category: Category name
        authorization: Admin token
        
    Returns:
        Ingestion results
    """
    try:
        ingester = PDFIngester()
        result = ingester.ingest_folder(category)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error ingesting category: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Static Files (Frontend) ====================

# Mount frontend static files BEFORE defining catch-all route
frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "")
logger.info(f"Frontend directory: {frontend_dir}")

# Serve index.html at root
@app.get("/", include_in_schema=False)
async def serve_index():
    """Serve the main frontend HTML file"""
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    else:
        logger.warning(f"index.html not found at {index_path}")
        return {"error": "Frontend not found"}

# Mount static files for CSS, JS, etc.
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")
    logger.info(f"Static files mounted from {frontend_dir}")

# ==================== Error Handlers ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    logger.warning(f"HTTP error: {exc.status_code} - {exc.detail}")
    return {
        "status": "error",
        "code": exc.status_code,
        "message": exc.detail
    }

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return {
        "status": "error",
        "code": 500,
        "message": "An unexpected error occurred"
    }

# ==================== Main Entry Point ====================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting OpenGov AI Assistant server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if os.getenv("APP_ENV") == "development" else False
    )
