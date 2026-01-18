#!/usr/bin/env python3
"""
Book Chapter Ingestion Pipeline
"""

import asyncio
import logging
import os
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Reuse components if possible, or reimplement simplified versions
try:
    import tiktoken
    from litellm import aembedding
    import requests
except ImportError:
    print("Missing dependencies: tiktoken, litellm, requests")
    exit(1)

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Text Processing ---

class TextFileProcessor:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        
    async def extract_content(self) -> Dict[str, Any]:
        with open(self.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Simplified metadata
        return {
            "title": f"The Inner Architect - Chapter {self.file_path.stem}",
            "authors": ["Mani Saint-Victor, MD"],
            "year": datetime.now().year,
            "abstract": content[:500] + "...",
            "content": content,
            "keywords": ["Inner Architect", "Dionysus", "Book"]
        }

# --- Chunker (Simplified from ingest_paper) ---

class SimpleChunker:
    def __init__(self, max_tokens=512, overlap=50):
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.max_tokens = max_tokens
        self.overlap = overlap
        
    def chunk_text(self, text: str, metadata: Dict) -> List[Dict]:
        tokens = self.tokenizer.encode(text)
        chunks = []
        start = 0
        chunk_num = 0
        
        while start < len(tokens):
            end = min(start + self.max_tokens, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            
            chunks.append({
                "chunk_id": f"{metadata['title']}-{chunk_num:03d}",
                "text": chunk_text,
                "metadata": {
                    "source": metadata["title"],
                    "chapter": self.cleanup_title(metadata["title"])
                },
                "token_count": len(chunk_tokens)
            })
            chunk_num += 1
            start = end - self.overlap if end < len(tokens) else end
            
        return chunks
        
    def cleanup_title(self, title):
        import re
        return re.sub(r'[^\w\s-]', '', title).replace(' ', '-')

# --- Embedding ---

async def generate_embeddings(chunks: List[Dict]) -> List[Dict]:
    logger.info(f"embedding {len(chunks)} chunks...")
    texts = [c["text"] for c in chunks]
    # batching handled by litellm usually, or we can batch manually
    # manual batch 100
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        batch_texts = [c["text"] for c in batch]
        resp = await aembedding(model="text-embedding-3-small", input=batch_texts)
        for j, item in enumerate(batch):
            item["embedding"] = resp.data[j]["embedding"]
    return chunks

async def generate_meta_embedding(text: str) -> List[float]:
    resp = await aembedding(model="text-embedding-3-small", input=[text[:8000]]) # Limit for safety
    return resp.data[0]["embedding"]

# --- Storage (Graphiti) ---

async def store_graphiti(metadata, chunks):
    from api.services.graphiti_service import get_graphiti_service
    service = await get_graphiti_service()
    
    group_id = f"book-inner-architect-ch{metadata['title'].split()[-1]}"
    
    # Store chunks as messages
    for chunk in chunks:
        await service.ingest_message(
            content=chunk["text"],
            source_description=f"{metadata['title']}",
            group_id=group_id,
            valid_at=datetime.now()
        )
    logger.info(f"Stored {len(chunks)} chunks in Graphiti group {group_id}")

# --- Main ---

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file_paths", nargs='+', type=Path, help="Paths to .txt files")
    args = parser.parse_args()
    
    for path in args.file_paths:
        logger.info(f"Processing {path}...")
        processor = TextFileProcessor(path)
        data = await processor.extract_content()
        
        chunker = SimpleChunker()
        chunks = chunker.chunk_text(data["content"], data)
        
        chunks = await generate_embeddings(chunks)
        # metadata_embedding = await generate_meta_embedding(data["abstract"]) 
        # (Graphiti ingestion uses chunks primarily, metadata embedding is for n8n/vector db, 
        # but here we follow the Graphiti path for alignment)
        
        await store_graphiti(data, chunks)
        print(f"✅ Ingested {path.name} ({len(chunks)} chunks)")

if __name__ == "__main__":
    asyncio.run(main())
