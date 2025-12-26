from .cite import build_citations, evidence_sufficient

def rag_answer(index, question: str, min_score: float):
    results = index.search(question, k=3)
    citations = build_citations(results)

    if not evidence_sufficient(results, min_score=min_score):
        return {"ok": False, "answer": None, "citations": citations, "reason": "insufficient_evidence"}

    answer = "Based on retrieved sources: " + " ".join([c["snippet"] for c in citations[:2]])
    return {"ok": True, "answer": answer, "citations": citations, "reason": "evidence_ok"}
