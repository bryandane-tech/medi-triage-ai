from typing import List, Dict
import math

class ClinicalRAGEngine:
    """Lightweight vector/similarity retrieval engine for medical guidelines."""

    def __init__(self):
        # In-memory medical protocol vector database
        self.knowledge_base: List[Dict[str, str]] = [
            {
                "protocol_id": "PROTO-CARD-01",
                "title": "Acute Coronary Syndrome Protocol",
                "keywords": ["chest pain", "shortness of breath", "diaphoresis", "radiation to arm"],
                "action": "Immediate ECG within 10 minutes. High priority triage."
            },
            {
                "protocol_id": "PROTO-RESP-02",
                "title": "Severe Acute Respiratory Distress",
                "keywords": ["shortness of breath", "wheezing", "cyanosis", "stridor"],
                "action": "Administer high-flow supplemental O2 and continuous SpO2 monitoring."
            },
            {
                "protocol_id": "PROTO-NEURO-03",
                "title": "Stroke Triage Protocol (FAST)",
                "keywords": ["facial drooping", "arm weakness", "slurred speech", "sudden headache"],
                "action": "Initiate immediate Stroke Code / Emergency CT Head."
            }
        ]

    def _tokenize(self, text: str) -> set:
        return set(text.lower().replace(",", "").replace(".", "").split())

    def retrieve_guidelines(self, clinical_notes: str, top_k: int = 2) -> List[Dict]:
        """Calculates Jaccard similarity scores across knowledge base protocols."""
        note_tokens = self._tokenize(clinical_notes)
        if not note_tokens:
            return []

        results = []
        for doc in self.knowledge_base:
            doc_tokens = set(doc["keywords"])
            intersection = note_tokens.intersection(doc_tokens)
            union = note_tokens.union(doc_tokens)
            score = len(intersection) / len(union) if union else 0.0

            if score > 0 or any(kw in clinical_notes.lower() for kw in doc["keywords"]):
                results.append({
                    "protocol_id": doc["protocol_id"],
                    "title": doc["title"],
                    "recommended_action": doc["action"],
                    "relevance_score": round(score, 3)
                })

        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:top_k]
