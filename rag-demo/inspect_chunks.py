# -*- coding: utf-8 -*-
"""诊断工具：查看向量库里存的所有 chunk，以及检索某一问题时的排序。

用法：
    python inspect_chunks.py                       # 列出所有 chunk（前几十个字）
    python inspect_chunks.py "三步法是什么？"       # 顺便看检索排序 + 距离
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
_MODELS_DIR = PROJECT_ROOT / "models"
os.environ["HF_HOME"] = str(_MODELS_DIR)
os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(_MODELS_DIR)
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

import sys
sys.path.insert(0, str(PROJECT_ROOT))

import config
import chromadb
from sentence_transformers import SentenceTransformer


def main():
    client = chromadb.PersistentClient(path=str(config.VECTOR_DB_DIR))
    col = client.get_or_create_collection("study_notes")

    # 取出全部条目
    all_data = col.get(include=["documents", "metadatas"])
    ids = all_data["ids"]
    docs = all_data["documents"]
    metas = all_data["metadatas"]
    print(f"[向量库] 共 {len(ids)} 个 chunk\n")

    # 1) 列出所有 chunk 的内容预览 + 来源
    print("== 全部 chunk（按序号）==")
    for i, (doc, meta) in enumerate(zip(docs, metas)):
        preview = doc.replace("\n", " ")[:60]
        print(f"  #{i:3d} [{meta.get('source','?'):>30}] {preview}...")

    # 2) 如果传了问题，做检索，展示相似度排序
    if len(sys.argv) >= 2:
        question = sys.argv[1]
        print(f"\n== 检索 '{question}' ==")
        model = SentenceTransformer(config.EMBEDDING_MODEL)
        q_vec = model.encode([question], normalize_embeddings=True).tolist()
        res = col.query(query_embeddings=q_vec, n_results=len(ids),
                        include=["documents", "metadatas", "distances"])
        for rank, (doc, meta, dist) in enumerate(
            zip(res["documents"][0], res["metadatas"][0], res["distances"][0]), 1
        ):
            preview = doc.replace("\n", " ")[:70]
            print(f"  [{rank}] 距离={dist:.4f} [{meta.get('source','?'):>25}] {preview}...")


if __name__ == "__main__":
    main()