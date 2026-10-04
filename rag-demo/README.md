# RAG 项目说明

基于你已有的 Function Calling 基础，做一个"**学习笔记问答机**"：
把 `docs\` 里的笔记变成资料库，问它"三步法是什么"它能基于笔记回答。

## 目录结构

```
rag-demo/
├── config.py            ← 所有配置（模型/向量库/资料库位置）
├── requirements.txt     ← 依赖
├── build_index.py       ← ①建索引：读资料→切分→向量化→存向量库
├── ask.py               ← ②查询：提问→检索→拼prompt→模型回答
└── models/              ← 存放下载的 embedding 模型（D盘，创建后生成）
└── chroma_db/           ← 向量数据库文件（创建后生成）
```

## 使用流程

**第一次：建索引**（读笔记+向量化+存库，模型会自动下载到 `models/`）
```bash
pip install -r requirements.txt
python build_index.py
```

**查询**（每次问问题）
```bash
python ask.py "三步法是什么？"
python ask.py "接真实API的4步链是什么？"
```

## 环境变量注意

- embedding 模型默认下到 C 盘；本项目在脚本开头强制设了 __HF_HOME__ 到 `models/`，保证下载到 D 盘。
- 生成/答疑用的模型继续用你的基元律动 key（在 `agent-basics/.env`）。