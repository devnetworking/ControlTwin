from __future__ import annotations

from typing import Any

import chromadb
from langchain_ollama import OllamaEmbeddings

from app.core.config import get_settings


class RAGRetriever:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = chromadb.PersistentClient(path=self.settings.chroma_persist_dir)
        self.collection = self.client.get_or_create_collection(name=self.settings.chroma_collection)
        self.embeddings = OllamaEmbeddings(
            model=self.settings.ollama_model_embed,
            base_url=self.settings.ollama_base_url,
        )

    @staticmethod
    def _chunk_text(content: str, size: int = 512, overlap: int = 50) -> list[str]:
        tokens = content.split()
        chunks = []
        start = 0
        while start < len(tokens):
            end = min(len(tokens), start + size)
            chunks.append(" ".join(tokens[start:end]))
            if end == len(tokens):
                break
            start = max(0, end - overlap)
        return chunks

    async def index_document(self, content: str, metadata: dict[str, Any], doc_id: str) -> int:
        chunks = self._chunk_text(content, size=512, overlap=50)
        ids = [f"{doc_id}:{i}" for i in range(len(chunks))]
        metadatas = [{**metadata, "doc_id": doc_id, "chunk_idx": i} for i in range(len(chunks))]
        embs = self.embeddings.embed_documents(chunks)
        self.collection.upsert(ids=ids, documents=chunks, metadatas=metadatas, embeddings=embs)
        return len(chunks)

    async def retrieve(self, query: str, n_results: int = 5) -> list[dict[str, Any]]:
        emb = self.embeddings.embed_query(query)
        res = self.collection.query(query_embeddings=[emb], n_results=n_results)
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        distances = res.get("distances", [[]])[0] if "distances" in res else [None] * len(docs)
        out = []
        for d, m, dist in zip(docs, metas, distances):
            out.append({"content": d, "metadata": m, "distance": dist})
        return out
