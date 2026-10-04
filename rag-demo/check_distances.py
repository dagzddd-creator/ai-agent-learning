# -*- coding: utf-8 -*-
"""验证：不同问题在向量库里的检索距离分布。

用来判断 rag_client.py 里的 LOW_RELEVANCE_THRESHOLD=0.8 是否合理。
   相关的问题  → 距离应 ≤0.8（正常触发 rag 回答）
   不相关的问题 → 距离应 >0.8（触发"笔记没有相关内容"）
跑法：python check_distances.py
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
os.environ["HF_HOME"] = str(PROJECT_ROOT / "models")
os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(PROJECT_ROOT / "models")
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

import config
import chromadb
from sentence_transformers import SentenceTransformer

model = SentenceTransformer(config.EMBEDDING_MODEL)
client = chromadb.PersistentClient(path=str(config.VECTOR_DB_DIR))
col = client.get_or_create_collection("study_notes")

# 相关问题的期望：距离小（有笔记内容）
related = ["三步法是什么？", "接真实API的4步链是什么？", "写description要注意什么"]
# 不相关问题的期望：距离大（笔记里没有）
unrelated = ["什么是量子引力？", "RAG数据清洗需要注意什么", "北京明天天气"]

print("== 相关问题（期望距离小）==")
for q in related:
    v = model.encode([q], normalize_embeddings=True).tolist()
    d = col.query(query_embeddings=v, n_results=3, include=["distances"])["distances"][0]
    print(f"  [{q[:20]}] 距离={[round(x, 3) for x in d]}")

print("== 不相关问题（期望距离大）==")
for q in unrelated:
    v = model.encode([q], normalize_embeddings=True).tolist()
    d = col.query(query_embeddings=v, n_results=3, include=["distances"])["distances"][0]
    print(f"  [{q[:20]}] 距离={[round(x, 3) for x in d]}")