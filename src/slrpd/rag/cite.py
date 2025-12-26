from typing import List, Dict, Any, Tuple

def build_citations(results: List[Tuple[float, Dict[str, Any]]], max_snip: int = 240):
    citations = []
    for score, doc in results:
        text = (doc.get("text") or "")[:max_snip].replace("\n", " ").strip()
        citations.append({
            "doc_id": doc.get("id"),
            "title": doc.get("title"),
            "score": score,
            "snippet": text
        })
    return citations

def evidence_sufficient(results, min_score: float) -> bool:
    if not results:
        return False
    return results[0][0] >= min_score
