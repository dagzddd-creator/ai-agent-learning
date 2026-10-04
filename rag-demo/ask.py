# -*- coding: utf-8 -*-
"""第②步 查询：提问 → 向量化 → 从向量库检索相关段落 → 让模型基于资料回答。

用法：
    python ask.py "三步法是什么？"
    python ask.py "接真实API的4步链是什么？"
"""

import os
from pathlib import Path

# 同样先把模型缓存指到 D 盘
PROJECT_ROOT = Path(__file__).resolve().parent
_MODELS_DIR = PROJECT_ROOT / "models"
os.environ["HF_HOME"] = str(_MODELS_DIR)
os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(_MODELS_DIR)
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"   # 国内镜像，加速模型下载

import sys
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT.parent))   # 让父目录可用（读 agent-basics 的配置思路）

import config
from sentence_transformers import SentenceTransformer
import chromadb

def get_client():
    """复用基元律动的 key 做"生成"，读取 agent-basics/.env。"""
    # 读取 agent-basics 下的 .env
    from dotenv import load_dotenv
    env_path = PROJECT_ROOT.parent / "agent-basics" / ".env"
    load_dotenv(env_path)
    from openai import OpenAI
    return OpenAI(
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL", "https://tokenrhythm.studio/v1"),
    ), os.getenv("LLM_MODEL", "deepseek-v4-flash-0731")


def retrieve(question, model, col, top_k=None):
    """检索与问题最相关的 top_k 段笔记。"""
    top_k = top_k or config.TOP_K
    q_vec = model.encode([question], normalize_embeddings=True).tolist()
    res = col.query(query_embeddings=q_vec, n_results=top_k,
                    include=["documents", "metadatas", "distances"])
    docs = res["documents"][0]
    metas = res["metadatas"][0]
    return list(zip(docs, metas))


def main():
    if len(sys.argv) < 2:
        print("用法: python ask.py \"你的问题\"")
        return

    question = sys.argv[1]
    print(f"[问题] {question}")

    # 1. 加载 embedding 模型（已下载则直接加载，很快）
    model = SentenceTransformer(config.EMBEDDING_MODEL)

    # 2. 打开向量库
    client = chromadb.PersistentClient(path=str(config.VECTOR_DB_DIR))
    col = client.get_or_create_collection("study_notes")

    # 3. 检索相关段落
    hits = retrieve(question, model, col)
    print(f"[检索] 找到 {len(hits)} 段相关笔记：")

    # 4. 把检索结果拼进 prompt，让模型"基于资料"回答
    context = "\n\n".join(
        f"【来源:{meta.get('source','')}】\n{doc}" for doc, meta in hits
    )
    prompt = f"""请基于下面【参考资料】回答问题。
如果参考资料里没有相关信息，请直接说"笔记里没有相关内容"，不要编造。

【参考资料】
{context}

【问题】
{question}

请给出简洁、准确的回答："""

    # 5. 调用基元律动生成回答
    llm_client, model_name = get_client()
    resp = llm_client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
    )
    print("\n" + "=" * 50)
    print("[回答]")
    print(resp.choices[0].message.content)

    # 6. 附上检索来源，方便你检验"是不是真的基于笔记"
    print("\n" + "=" * 50)
    print("[检索到的笔记来源]")
    for doc, meta in hits:
        print(f"  - {meta.get('source','?')} (片段{meta.get('index','?')})")


if __name__ == "__main__":
    main()