import os, json
from src.slrpd.config import settings

os.makedirs(settings.corpus_dir, exist_ok=True)

docs = [
  {
    "id": "doc-001",
    "title": "Silicon photonics overview",
    "text": "Silicon photonics integrates optical components on silicon to enable high-bandwidth, energy-efficient optical interconnects for data centers and high-performance computing."
  },
  {
    "id": "doc-002",
    "title": "Co-packaged optics motivation",
    "text": "Co-packaged optics aims to reduce electrical I/O bottlenecks by bringing optics closer to switching and compute, improving bandwidth density and power efficiency."
  },
  {
    "id": "doc-003",
    "title": "Quantum networking concept",
    "text": "Quantum networking focuses on distributing quantum states or entanglement across distance, enabling networked quantum systems and potentially distributed quantum computing."
  }
]

for d in docs:
  path = os.path.join(settings.corpus_dir, f"{d['id']}.json")
  with open(path, "w", encoding="utf-8") as f:
    json.dump(d, f, indent=2)

print(f"Seeded {len(docs)} docs into {settings.corpus_dir}")
