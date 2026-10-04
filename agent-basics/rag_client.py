# -*- coding: utf-8 -*-
"""复用 rag-demo 的 RAG 检索，封装成一个可被 tools.py 调用的函数。

设计要点：
- embedding 模型 + rerank 模型 + 向量库 都是重量级对象，用「懒加载 + 缓存」只加载一次。
- 检索采用「两段式」：
    ① embedding 粗筛：从向量库取 top_k 候选（快、粗）
    ② rerank 精排：用交叉编码器对候选逐个精打分（准、慢，但只对少量候选）
  这比单纯用"向量距离阈值"可靠——rerank 逐对精判，能解决"临界区误判"。
- rag_query 内部完成「检索+让模型基于笔记生成回答」，返回给外层 Agent。
"""

import os
from pathlib import Path

# 让模型缓存/镜像先在脚本级设置
PROJECT_ROOT = Path(__file__).resolve().parent.parent   # D:\study-practice
_RAG_DIR = PROJECT_ROOT / "rag-demo"
_MODELS_DIR = PROJECT_ROOT / "rag-demo" / "models"
os.environ["HF_HOME"] = str(_MODELS_DIR)
os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(_MODELS_DIR)
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# 全局缓存，避免重复加载
_embed_model = None
_rerank_model = None
_vector_col = None


def _get_models():
    """懒加载 embedding 模型 + rerank 模型 + 向量库，只加载一次。"""
    global _embed_model, _rerank_model, _vector_col
    if _embed_model is not None and _rerank_model is not None and _vector_col is not None:
        return _embed_model, _rerank_model, _vector_col

    import sys
    if str(_RAG_DIR) not in sys.path:
        sys.path.insert(0, str(_RAG_DIR))
    import config                      # rag-demo/config.py

    from sentence_transformers import SentenceTransformer
    from sentence_transformers.cross_encoder import CrossEncoder
    import chromadb

    _embed_model = SentenceTransformer(config.EMBEDDING_MODEL)
    _rerank_model = CrossEncoder(config.RERANK_MODEL)
    _client = chromadb.PersistentClient(path=str(config.VECTOR_DB_DIR))
    _vector_col = _client.get_or_create_collection("study_notes")
    return _embed_model, _rerank_model, _vector_col


def _retrieve_and_rerank(question, embed_model, rerank_model, col,
                         recall_k=8, rerank_top_n=2):
    """两段式检索：embedding 粗筛 → rerank 精排。

    返回按 rerank 分数降序的 [(doc, meta, rerank_score), ...]，只留 top_n。
    """
    # ---- 阶段一：embedding 粗筛（多取候选，给 rerank 素材）----
    q_vec = embed_model.encode([question], normalize_embeddings=True).tolist()
    res = col.query(query_embeddings=q_vec, n_results=recall_k,
                    include=["documents", "metadatas"])
    docs = res["documents"][0]
    metas = res["metadatas"][0]

    # ---- 阶段二：rerank 精排 ----
    # 注意：CrossEncoder 要一对一对地判 (question, candidate)
    pairs = [[question, doc] for doc in docs]
    scores = rerank_model.predict(pairs)          # 每个 doc 一个相关分
    # 打包并按分数降序
    ranked = sorted(
        zip(docs, metas, scores),
        key=lambda x: x[2],
        reverse=True,
    )
    return ranked[:rerank_top_n]


def rag_query(question: str) -> str:
    """从学习笔记向量库检索相关内容，并让模型基于检索结果回答问题。

    流程：embedding 粗筛 → rerank 精排 → 基于精排后的片段让模型回答。
    若 rerank 最高分也低于阈值，说明笔记库确实没有相关内容。
    """
    embed_model, rerank_model, col = _get_models()

    recall_k = 8
    rerank_top_n = 2
    ranked = _retrieve_and_rerank(
        question, embed_model, rerank_model, col,
        recall_k=recall_k, rerank_top_n=rerank_top_n,
    )

    # 用 rerank 最高分判断"有没有相关内容"。
    # bge-reranker 输出大致在 [-4, 4] 量级；分数越高越相关。负分/接近0通常=不相关。
    # 这里先取一个偏保守的阈值 0（即"必须整体判为正相关"才认为有内容）。
    MIN_RERANK_SCORE = 0.0
    best_score = ranked[0][2] if ranked else -999.0
    if best_score < MIN_RERANK_SCORE:
        return (
            f"[笔记库检索结果] 对于问题「{question}」，rerank 精排后最高相关分仅 "
            f"{best_score:.2f}(<{MIN_RERANK_SCORE})，说明用户笔记里【没有】这块内容。"
            f"\n请不要再次调用本工具尝试其他措辞——重复搜索不会有结果。"
            f"\n（如果你仍然想回答，请明确标注『这是我的通用知识，不是来自笔记录』再作答。）"
        )

    # 拼 prompt：基于精排后的片段回答
    context = "\n\n".join(
        f"【来源:{meta.get('source','')}】(相关分={score:.2f})\n{doc}"
        for doc, meta, score in ranked
    )
    prompt = (
        "你是基于用户学习笔记的问答助手。请只依据下面【参考资料】回答问题；"
        "如果参考资料里没有该信息，直接回答『笔记里没有相关内容』，不要编造。\n\n"
        "【参考资料】\n"
        f"{context}\n\n"
        f"【问题】\n{question}\n\n"
        "【回答】"
    )

    # 调用基元律动生成回答（读取 agent-basics/.env）
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / "agent-basics" / ".env")
    from openai import OpenAI
    client = OpenAI(
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL", "https://tokenrhythm.studio/v1"),
    )
    resp = client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "deepseek-v4-flash-0731"),
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content