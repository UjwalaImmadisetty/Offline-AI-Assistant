from fastapi import FastAPI, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import os

from rag_engine import process_file, ask_question, general_ai, load_vector_store

app = FastAPI(title="Offline AI Assistant")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates
templates = Jinja2Templates(directory="templates")

# Static files
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Load FAISS index
load_vector_store()

# Request model
class Question(BaseModel):
    query: str


# UI
@app.get("/", response_class=HTMLResponse)
def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})


# Upload file
@app.post("/upload_file")
async def upload_file(file: UploadFile = File(...)):

    path = f"uploads/{file.filename}"

    contents = await file.read()

    with open(path, "wb") as f:
        f.write(contents)

    process_file(path)

    return {
        "filename": file.filename,
        "url": f"/uploads/{file.filename}"
    }


# Ask document
@app.post("/ask_pdf")
def ask_pdf(q: Question):

    answer = ask_question(q.query)

    return {"answer": answer}


# General AI
@app.post("/ask_ai")
def ask_ai(q: Question):

    answer = general_ai(q.query)

    return {"answer": answer}