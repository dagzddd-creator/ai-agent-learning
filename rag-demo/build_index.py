# -*- coding: utf-8 -*-
"""第①步 建索引：读取 docs 笔记 → 切成小块 → 向量化 → 存入向量库。

只需运行一次（或每次改了 docs 里的笔记后重跑）。
"""

# 先把模型缓存指到 D 盘（必须放在 import sentence_transformers 之前）
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
_MODELS_DIR = PROJECT_ROOT / "models"
os.environ["HF_HOME"] = str(_MODELS_DIR)          # huggingface 下载根 → D盘
os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(_MODELS_DIR)
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"   # 国内镜像，加速模型下载（huggingface.co 在国内常连不上）

import sys
sys.path.insert(0, str(PROJECT_ROOT))          # 让 config 可导入

import config
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils import embedding_functions  # 下面其实用我们自己算的向量，这里主要演示


def load_documents(docs_dir):
    """读取 docs 目录下所有 .md 笔记，返回 (来源文件, 清洗后文本) 列表。"""
    docs = []
    for f in sorted(docs_dir.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        text = clean_markdown(text)   # ★ 新增：清洗，去噪音
        docs.append((f.name, text))
    print(f"[加载] 找到 {len(docs)} 篇笔记")
    return docs


def clean_markdown(text):
    """清洗 Markdown，减少向量噪音，但【不会】丢真正的知识内容。

    处理原则：
    - 去掉 ``` 围栏、反引号、表格、分隔线等"噪音符号"
    - 但代码块里的文字要【保留】——因为你的笔记里大量知识就写在代码块里
      （例如 day6-challenge 的"三步法"就放在 ``` 代码块中，直接丢掉会连知识一起丢）
    这是 RAG 常见权衡：一风味追求"去噪"可能误删"内容"，先保内容、后去噪。
    """
    lines = text.split("\n")
    out = []
    in_code = False
    for line in lines:
        # 代码块围栏：只去掉 ``` 记号本身，内容行保留
        if line.strip().startswith("```"):
            in_code = not in_code
            continue          # 丢弃 ``` 这行，但保留后续代码/正文行
        # 表格行(含 | )整体跳过（表格对 embedding 噪声大）
        stripped = line.strip()
        if stripped.startswith("|"):
            continue
        if set(stripped) <= set("-") and stripped:   # 纯 --- 分隔线
            continue
        # 只保留以 ## 开头的标题作"分隔标记"，其余标题去掉
        if stripped.startswith("## "):
            out.append(stripped)
            continue
        if stripped.startswith("# "):
            continue
        # 行内反引号去掉
        line = line.replace("`", "")
        # 去掉多余空行，保留有效内容
        if line.strip():
            out.append(line)
    return "\n".join(out)


def chunk_by_headings(text, max_size=None):
    """按 `## 小节标题` 切块：每个 chunk 是一个完整的 Markdown 小节。

    比"按固定字数硬切"好——小节内知识相对完整，"三步法"不会被拆散。
    若某小节太长（超 max_size），再按字数兜底切。返回 (小标题, 内容) 列表。
    """
    max_size = max_size or config.CHUNK_SIZE
    lines = text.split("\n")
    sections = []          # [(小标题, [内容行])]
    cur_title = ""
    cur_body = []
    for line in lines:
        if line.startswith("## "):
            if cur_title or cur_body:
                sections.append((cur_title, cur_body))
            cur_title = line[3:].strip()  # 去掉 "## "
            cur_body = []
        else:
            cur_body.append(line)
    if cur_title or cur_body:
        sections.append((cur_title, cur_body))

    # 把每个 section 拼成"标题 + 内容"，超过 max_size 的按字数兜底切
    chunks = []
    for title, body_lines in sections:
        section_text = title + "\n" + "\n".join(body_lines)
        section_text = section_text.strip()
        if not section_text:
            continue
        if len(section_text) <= max_size:
            chunks.append(section_text)
        else:
            # 兜底：按字数硬切
            for i in range(0, len(section_text), max_size):
                chunks.append(section_text[i:i + max_size])
    return chunks


def chunk_text(text, size=None, overlap=None):
    """按标题切分为主，固定字数切分为兜底。返回纯文本块列表（不带标题前缀，供嵌入）。"""
    size = size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP
    # 先尝试按标题切
    sections = chunk_by_headings(text, max_size=size)
    if len(sections) > 1:
        return [s for s in sections if s.strip()]
    # 没有标题时，回退到固定字数硬切
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = end - overlap
    return chunks


def main():
    # 1. 加载笔记
    docs = load_documents(config.DOCS_DIR)

    # 2. 切分：每篇 → 多个 chunk，记录它来自哪篇
    all_chunks, all_sources = [], []
    for name, text in docs:
        chunks = chunk_text(text)
        all_chunks.extend(chunks)
        all_sources.extend([name] * len(chunks))
    print(f"[切分] 共切成 {len(all_chunks)} 段")

    # 3. 加载 embedding 模型（首次会自动下载到 models/ 目录）
    print(f"[模型] 加载 {config.EMBEDDING_MODEL} ...（首次会下载，约100MB，请耐心）")
    model = SentenceTransformer(config.EMBEDDING_MODEL)
    print("[模型] 加载完成")

    # 4. 向量化：把每段文字转成向量
    print("[向量化] 正在把每段笔记转成向量 ...")
    vectors = model.encode(all_chunks, normalize_embeddings=True).tolist()

    # 5. 存入向量库
    client = chromadb.PersistentClient(path=str(config.VECTOR_DB_DIR))
    # 重新建库：先删掉旧的 collection 再新建，避免脏数据
    try:
        client.delete_collection("study_notes")
    except Exception:
        pass  # 第一次还没有这个 collection，忽略
    col = client.get_or_create_collection("study_notes")

    # 给每段一个唯一 id
    ids = [f"doc_{i}" for i in range(len(all_chunks))]
    col.add(
        ids=ids,
        embeddings=vectors,
        documents=all_chunks,
        metadatas=[{"source": s, "index": i} for i, s in enumerate(all_sources)],
    )
    print(f"[完成] 已把 {len(all_chunks)} 段笔记存入向量库: {config.VECTOR_DB_DIR}")


if __name__ == "__main__":
    main()