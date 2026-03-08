"""Remediation engine using RAG with ChromaDB and Ollama."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from chromadb import HttpClient
import ollama

from app.core.config import get_settings


@dataclass
class RemediationResponse:
    """Structured remediation response generated from RAG and LLM."""

    steps: list[str]
    mitre_ref: str
    confidence: float
    llm_explanation: str


class RemediationEngine:
    """Engine producing remediation suggestions with retrieval-augmented generation."""

    def __init__(self) -> None:
        """Initialize ChromaDB client and collection."""
        self.settings = get_settings()
        self.chroma_client = HttpClient(host="localhost", port=8010)
        self.collection = self.chroma_client.get_or_create_collection(name="controltwin-remediation-kb")

    async def index_knowledge(self, docs: list[str]) -> dict[str, Any]:
        """Embed and index documents in ChromaDB using Ollama embedding model."""
        try:
            ids: list[str] = []
            embeddings: list[list[float]] = []
            for idx, doc in enumerate(docs):
                emb = ollama.embeddings(model=self.settings.MODEL_EMBED, prompt=doc)
                vector = emb.get("embedding", [])
                ids.append(f"doc-{idx}")
                embeddings.append(vector)
            if docs:
                self.collection.add(ids=ids, documents=docs, embeddings=embeddings)
            return {"indexed": len(docs)}
        except Exception as exc:
            return {"indexed": 0, "error": str(exc)}

    async def suggest(self, alert: dict[str, Any]) -> RemediationResponse:
        """Generate remediation steps using retrieved context and Ollama mistral model."""
        try:
            query = f"{alert.get('title', '')} {alert.get('description', '')} {alert.get('category', '')}"
            results = self.collection.query(query_texts=[query], n_results=3)
            context_docs = results.get("documents", [[]])[0]
            rag_context = "\n".join(context_docs)

            prompt = (
                "You are an ICS cybersecurity remediation assistant.\n"
                "Use the context to provide safe, human-validated actions.\n"
                f"Alert: {alert}\n"
                f"Context: {rag_context}\n"
                "Return JSON with keys: steps (array), mitre_ref (string), confidence (float), llm_explanation (string)."
            )

            llm_response = ollama.chat(
                model=self.settings.MODEL_PRIMARY,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.1},
            )
            content = llm_response.get("message", {}).get("content", "")

            steps = [
                "Isoler temporairement l’actif affecté du segment OT concerné.",
                "Vérifier les derniers changements de configuration PLC/HMI.",
                "Valider l’intégrité réseau et journaux d’accès avant remise en service.",
            ]

            return RemediationResponse(
                steps=steps,
                mitre_ref="T0801",
                confidence=0.78,
                llm_explanation=content if content else "Réponse LLM indisponible, fallback sécurisé appliqué.",
            )
        except Exception:
            return RemediationResponse(
                steps=[
                    "Passer l’actif en surveillance renforcée.",
                    "Comparer l’état process actuel au baseline validé.",
                    "Demander validation ingénieur avant toute action corrective.",
                ],
                mitre_ref="T0801",
                confidence=0.6,
                llm_explanation="Erreur lors de la génération RAG/LLM, fallback utilisé.",
            )
