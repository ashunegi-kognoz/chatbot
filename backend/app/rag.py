from typing import List
import re
from .llm_service import generate_embedding

def simple_chunk(text: str, max_tokens_chars: int = 1200) -> List[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, buf = [], ""
    for p in paras:
        if len(buf) + len(p) + 1 > max_tokens_chars:
            if buf:
                chunks.append(buf.strip())
                buf = ""
        buf += (("\n" if buf else "") + p)
    if buf:
        chunks.append(buf.strip())
    return chunks

def build_context(matches) -> str:
    """Build context from vector db matches"""
    parts = []
    for m in matches:
        meta = m.get("metadata", {}) or {}
        filename = meta.get("filename", "unknown-filename")
        text = meta.get("text", "")
        if text:
            parts.append(f"[Source : {filename}] {text}")
    return "\n\n".join(parts)

def embed_texts(texts: List[str], embed_func=generate_embedding):
    return [embed_func(t) for t in texts]