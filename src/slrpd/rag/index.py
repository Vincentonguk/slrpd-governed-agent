import os, json
from typing import List, Dict, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class SimpleCorpusIndex:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.docs: List[Dict[str, Any]] = []
        self.matrix = None

    def load_from_dir(self, corpus_dir: str):
        self.docs = []
        os.makedirs(corpus_dir, exist_ok=True)
        for fn in sorted(os.listdir(corpus_dir)):
            if fn.endswith(".json"):
                with open(os.path.join(corpus_dir, fn), "r", encoding="utf-8") as f:
                    self.docs.append(json.load(f))
        texts = [d.get("text", "") for d in self.docs] or [""]
        self.matrix = self.vectorizer.fit_transform(texts)

    def search(self, query: str, k: int = 3) -> List[Tuple[float, Dict[str, Any]]]:
        if self.matrix is None:
            return []
        qv = self.vectorizer.transform([query])
        sims = cosine_similarity(qv, self.matrix)[0]
        ranked = sorted(list(enumerate(sims)), key=lambda x: x[1], reverse=True)[:k]
        return [(float(score), self.docs[i]) for i, score in ranked]
