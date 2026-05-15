from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle
import os
import pypdf
import docx
from pptx import Presentation
import ollama

model = SentenceTransformer("all-MiniLM-L6-v2")

documents = []
index = None
memory = []


def extract_text(file):

    if file.endswith(".pdf"):
        reader = pypdf.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text

    if file.endswith(".txt"):
        return open(file).read()

    if file.endswith(".docx"):
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs])

    if file.endswith(".pptx"):
        prs = Presentation(file)
        text = ""
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text += shape.text
        return text

    return ""


def chunk_text(text, size=500):

    chunks = []

    for i in range(0, len(text), size):
        chunks.append(text[i:i+size])

    return chunks


def create_vector_store(chunks):

    global index, documents

    documents.extend(chunks)

    embeddings = model.encode(chunks)

    if index is None:

        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)

    index.add(np.array(embeddings))

    os.makedirs("faiss_index", exist_ok=True)

    faiss.write_index(index, "faiss_index/index.faiss")

    with open("faiss_index/chunks.pkl", "wb") as f:
        pickle.dump(documents, f)


def load_vector_store():

    global index, documents

    if os.path.exists("faiss_index/index.faiss"):

        index = faiss.read_index("faiss_index/index.faiss")

        with open("faiss_index/chunks.pkl", "rb") as f:
            documents = pickle.load(f)


def process_file(path):

    text = extract_text(path)

    if text:

        chunks = chunk_text(text)

        create_vector_store(chunks)


def ask_question(question):

    global memory

    if index is None:
        return "No documents indexed yet."

    query_embedding = model.encode([question])

    distances, indices = index.search(np.array(query_embedding), k=3)

    context = ""

    for i in indices[0]:
        context += documents[i] + "\n"

    prompt = f"""
Answer clearly using headings and bullet points.

Context:
{context}

Conversation history:
{memory}

Question:
{question}
"""

    response = ollama.chat(
        model="phi3",
        messages=[{"role": "user", "content": prompt}]
    )

    answer = response["message"]["content"]

    memory.append((question, answer))

    return answer


def general_ai(question):

    global memory

    prompt = f"""
Conversation history:
{memory}

User question:
{question}
"""

    response = ollama.chat(
        model="phi3",
        messages=[{"role": "user", "content": prompt}]
    )

    answer = response["message"]["content"]

    memory.append((question, answer))

    return answer