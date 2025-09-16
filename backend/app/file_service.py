import io
import os
import uuid
import PyPDF2
from typing import List, Dict
from .rag import simple_chunk, embed_texts
from .vector_db import upsert_embeddings

def process_text_file(content: str, filename : str) -> List[Dict]:
    """Process a text file and return chunks for vector storage"""
    chunks = simple_chunk(content)
    embeddings = embed_texts(chunks)

    items = []
    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        items.append({
            "id" : f"{filename}-{i}-{uuid.uuid4().hex[:8]}",
            "values" : emb,
            "metadata" : {
                "filename" : filename,
                "file_type" : "text",
                "text" : chunk,
                "chunk_index" : i
            }
        })
    return items

def process_pdf_file(content: bytes, filename : str) -> List[Dict]:
    """Process a PDF file and return  chunks for vector storage"""
    try:
        # Read PDF content
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""

        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"

        if not text.strip():
            raise ValueError("No text content found in PDF")

        # Process the extracted text
        chunks = simple_chunk(text)
        embeddings = embed_texts(chunks)

        items = []
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            items.append({
                "id" : f"{filename}-{i}-{uuid.uuid4().hex[:8]}",
                "values" : emb,
                "metadata" : {
                    "filename" : filename,
                    "file_type" : "pdf",
                    "text" : chunk,
                    "chunk_index" : i
                }
            })

        return items
    except Exception as e:
        raise ValueError(f"Error processing pdf : {str(e)}")

def store_file_chunks(items : List[Dict]) -> int:
    """Store file chunks in vector db"""
    if items:
        upsert_embeddings(items)
        return len(items)
    return 0