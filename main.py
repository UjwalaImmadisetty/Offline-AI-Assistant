from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, validator
import os
import logging

from rag_engine import process_file, ask_question, general_ai, load_vector_store

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Offline AI Assistant", description="Professional RAG with Ollama")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates & Static files
templates = Jinja2Templates(directory="templates")
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Load FAISS index at startup
logger.info("Loading vector store...")
try:
    load_vector_store()
    logger.info("✅ Vector store loaded successfully")
except Exception as e:
    logger.warning(f"⚠️  Vector store not found (first run): {e}")

# Request model with validation
class Question(BaseModel):
    query: str
    
    @validator('query')
    def query_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        if len(v) > 5000:
            raise ValueError("Query too long (max 5000 characters)")
        return v.strip()


# Health check
@app.get("/health")
def health():
    return {"status": "✅ API is running", "version": "1.0"}


# UI
@app.get("/", response_class=HTMLResponse)
def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})


# Upload file endpoint
@app.post("/upload_file")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Validate file type
        allowed_types = {".pdf", ".txt", ".docx", ".pptx"}
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_types:
            raise HTTPException(status_code=400, detail=f"File type {file_ext} not supported")
        
        # Validate file size (max 50MB)
        contents = await file.read()
        if len(contents) > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 50MB)")
        
        # Save and process
        path = f"uploads/{file.filename}"
        with open(path, "wb") as f:
            f.write(contents)
        
        logger.info(f"Processing file: {file.filename}")
        process_file(path)
        logger.info(f"✅ File processed: {file.filename}")
        
        return {
            "filename": file.filename,
            "url": f"/uploads/{file.filename}",
            "status": "✅ File uploaded and indexed successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")


# Ask document endpoint
@app.post("/ask_pdf")
def ask_pdf(q: Question):
    try:
        logger.info(f"PDF Query: {q.query[:50]}...")
        answer = ask_question(q.query)
        
        if not answer:
            raise HTTPException(status_code=500, detail="No answer generated")
        
        logger.info("✅ PDF query answered")
        return {"answer": answer}
    
    except Exception as e:
        logger.error(f"❌ PDF error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# General AI endpoint
@app.post("/ask_ai")
def ask_ai(q: Question):
    try:
        logger.info(f"AI Query: {q.query[:50]}...")
        answer = general_ai(q.query)
        
        if not answer:
            raise HTTPException(status_code=500, detail="No answer generated")
        
        logger.info("✅ AI query answered")
        return {"answer": answer}
    
    except Exception as e:
        logger.error(f"❌ AI error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)