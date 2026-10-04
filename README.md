# Agent 开发学习项目（Function Calling + RAG）

> 一个从零实践的 AI Agent 学习项目：手写工具调用 Agent + 基于个人笔记的 RAG 问答系统。
> 核心思路：**重理解、轻追新、动手做项目、亲自踩坑**。

## 📁 项目结构

```
study-practice/
├── README.md                     # 本文件
├── minimal-rag.py                # 手写的 30 行最小 RAG（理解 RAG 本质用）
├── agent-basics/                 # 项目一：Function Calling Agent（7个工具）
│   ├── main.py                   # Agent 主循环（ReAct 范式）
│   ├── tools.py                  # 工具定义（模型的手）
│   ├── rag_client.py             # RAG 检索封装（两段式：embedding + rerank）
│   ├── reflection_demo.py        # Reflection 范式演示（生成→批评→改进）
│   └── .env.example              # 环境变量模板
├── rag-demo/                     # 项目二：RAG 问答系统（独立演示 + 调优）
│   ├── build_index.py            # 建索引：清洗→切分→向量化→入库
│   ├── ask.py                    # 查询：检索→拼prompt→生成
│   ├── inspect_chunks.py         # 诊断：查看 chunk + 检索排序
│   └── check_distances.py        # 校准：测距离分布定阈值
└── docs/                         # 学习笔记（也是 RAG 的资料库）
    ├── function-calling-notes.md # Function Calling 完整笔记
    ├── real-api-4steps.md        # 接真实 API 的 4 步链
    ├── rag-tuning-notes.md       # RAG 基础 + "清洗误删知识"教训
    ├── rag-rerank-notes.md       # 两段式检索 + 临界区处理
    ├── reflection-notes.md       # Reflection 范式 + critic 四轮调优实验
    └── learning-summary.md       # 阶段总结（面试自我介绍素材）
```

## 🎯 项目一：Function Calling Agent（`agent-basics/`）

一个会"动手干活"的 Agent，通过 Function Calling 让模型自主调用工具：

**7 个工具**：查实时天气、查时间、查汇率、推荐穿搭、城市攻略推荐、RAG 笔记问答、计算器

**技术亮点**：
- 全部工具走「三步法」：写函数 → 写 JSON Schema → 注册映射
- 天气、汇率接**真实 API**（wttr.in / open.er-api），带 `try/except` 双保险
- 模型能自动**串联多个工具**（如"北京穿什么" → 自动查天气→拿温度→推荐穿搭）
- description 防乱编：通过精确描述"支持范围/参数格式"控制模型不乱传参
- 实践了两种经典 Agent 范式：**ReAct**（main.py 的工具循环）+ **Reflection**（reflection_demo.py）

**运行**：
```bash
cd agent-basics
pip install -r requirements.txt
copy .env.example .env   # 填入你的 OpenAI 兼容 key（默认基元律动）
python main.py
```

## 🔍 项目二：RAG 笔记问答（`rag-demo/`）

让 Agent 能"读你的笔记回答问题"，支持私有知识 + 防幻觉：

**核心流程**：文档清洗 → 按标题切分 → 向量化(bge-small-zh) → 存入 Chroma → 检索 → 生成

**技术进阶**（真实调优，非 demo）：
- **两段式检索**：embedding 粗筛 top8 → cross-encoder(bge-reranker-base) 精排
- 用 **rerank 分数**替代"距离阈值"，解决"临界区误判"（三步法 0.878 vs RAG清洗 1.003）
- 完整踩坑：清洗过度会误删代码块内的知识、Markdown 表格噪音等

**运行**：
```bash
cd rag-demo
pip install -r requirements.txt
python build_index.py        # 建索引（首次会下载 embedding 模型）
python ask.py "三步法是什么？"
```

## 📚 学习笔记（docs/）

全部为**实战总结**，每篇都记录真实踩过的坑：

| 笔记 | 主题 |
|---|---|
| function-calling-notes.md | 三步法、菜单四字段、防乱编 Checklist |
| real-api-4steps.md | 拼URL→发请求→解析→取值 + try/except |
| rag-tuning-notes.md | RAG 全流程 + "清洗误删知识"教训 |
| rag-rerank-notes.md | 两段式检索 + 临界区 + 工程细节 |
| reflection-notes.md | Reflection 范式 + critic 四轮调优（态度 vs 方法） |
| understand-agent-code.md | main.py / tools.py 零基础拆解 |
| learning-summary.md | 阶段学习总结（面试自我介绍素材） |
| week1-checklist.md / day6-challenge.md | 第一周每日清单 + 加工具挑战书 |

## 🛠️ 技术栈

- **模型**：基元律动（TokenRhythm，OpenAI 兼容接口）
- **RAG**：sentence-transformers（bge-small-zh + bge-reranker-base）、ChromaDB
- **语言**：Python 3.13

## ⚠️ 踩过的坑（面试常被问）

1. Function Calling：改了函数忘改菜单 → 模型的"能力"被旧描述封印
2. RAG：清洗过度会误删代码块里的知识
3. 阈值不能拍脑袋 → 用 `check_distances.py` 实测距离分布再定
4. HF 在国内连不上 → 用 `HF_ENDPOINT=https://hf-mirror.com` 镜像
5. Reflection：critic 会"凑数"编造缺陷（把 2 行改成 150 行），也会"放水"漏真 bug
   → 必须给它**方法**（强制用具体输入逐步演算），而不只是**态度**（"严格一点"）