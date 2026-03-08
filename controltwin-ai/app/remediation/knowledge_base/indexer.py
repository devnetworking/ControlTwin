from __future__ import annotations

from app.remediation.knowledge_base.mitre_ics import MITRE_ICS_TECHNIQUES
from app.remediation.rag import RAGRetriever


class KBIndexer:
    def __init__(self) -> None:
        self.rag = RAGRetriever()

    async def index_mitre_ics(self) -> int:
        total = 0
        for tid, item in MITRE_ICS_TECHNIQUES.items():
            content = (
                f"{item['id']} {item['name']}\n"
                f"Tactic: {item['tactic']}\n"
                f"Description: {item['description']}\n"
                f"Platforms: {', '.join(item['platforms'])}\n"
                f"Data Sources: {', '.join(item['data_sources'])}"
            )
            metadata = {"type": "mitre_ics", "technique_id": tid, "name": item["name"]}
            total += await self.rag.index_document(content=content, metadata=metadata, doc_id=tid)
        return total
