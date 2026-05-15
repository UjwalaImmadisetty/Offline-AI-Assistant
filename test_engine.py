from rag_engine import load_pdf, chunk_text, create_vector_store

text = load_pdf("sample.pdf")
chunks = chunk_text(text)
create_vector_store(chunks)
