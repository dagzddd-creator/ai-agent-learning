# -*- coding: utf-8 -*-
"""RAG 项目统一配置。

所有全局设置集中在这里，方便调整。
"""

from pathlib import Path

# --- 模型缓存目录：强制放到 D 盘工作区，不写 C 盘 ---
# 注意：本文件应该用 rag_demo 里写一个 run 入口来设置 env；简单起见，
# 我们在这里也暴露常量，但真正的环境变量设置放在 build_index.py / ask.py 开头。

PROJECT_ROOT = Path(__file__).resolve().parent          # D:\study-practice\rag-demo
MODELS_DIR = PROJECT_ROOT / "models"                    # 模型下载到 D:\study-practice\rag-demo\models
VECTOR_DB_DIR = PROJECT_ROOT / "chroma_db"              # 向量库存储位置
DOCS_DIR = PROJECT_ROOT.parent / "docs"                 # 资料库：D:\study-practice\docs（你的学习笔记）

# --- 模型选择（中文效果好的轻量模型）---
# BAAI/bge-small-zh-v1.5  ~ 100MB，中文效果好，轻量，适合学习
EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
# 备选（更大但更准）：BAAI/bge-base-zh-v1.5 ~ 400MB

# --- rerank（重排序）模型：cross-encoder，对候选片段精打分 ---
RERANK_MODEL = "BAAI/bge-reranker-base"
RERANK_TOP_N = 2         # 精排后保留的最高分片段数
RERANK_MIN_SCORE = 0.0   # 低于此分数的片段视为"不相关"（可配合调优）

# --- 切分参数 ---
CHUNK_SIZE = 500       # 每段文本最多约 500 字
CHUNK_OVERLAP = 80     # 两段之间重叠 80 字（防止把一句话截断）

# --- 检索参数 ---
TOP_K = 2              # 检索时返回最相关的几段资料