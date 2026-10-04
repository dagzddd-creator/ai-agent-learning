# RAG 进阶笔记：重排序（rerank）与两段式检索

> 解决"embedding 距离临界区误判"的正解，也是工业级 RAG 的标准一环。
> 对应代码：`agent-basics/rag_client.py` 里的 `_retrieve_and_rerank`。

---

## 一、它解决什么问题：临界区误判

之前只靠 embedding 距离 + 一个固定阈值判断"有没有相关内容"：

```
提问 → embedding 检索 top3 → 距离阈值(0.90) → 通过/拒绝
```

真实测量的痛点（`check_distances.py` 输出）：

| 问题 | 最优距离 | 真相 |
|---|---|---|
| 三步法是什么 | 0.878 | 相关 |
| RAG清洗注意什么 | 1.003 | 不相关 |

**两个只差 0.125**——缓冲太薄，阈值一抖就误判。根源：embedding 向量距离"区分度不够锐"。

## 二、核心思想：多一步"精判"

**原来一步判生死，改成两步：粗筛 + 精排。**

```
① embedding 粗筛：从全部文档快速取 top-k 候选（快、粗、适合海量）
② rerank 精排：  用交叉编码器对少量候选逐个精打分（准、慢、只对少量）
```

**一句话：embedding 负责"海选到几十个"，rerank 负责"精挑到几个"。**

## 三、为什么 rerank 比调阈值可靠

| | embedding（双塔） | rerank（交叉编码器） |
|---|---|---|
| 原理 | 两段各自压缩成语义向量，再算距离 | 把"提问+候选"一起编码、交叉注意力 |
| 判断 | 整体像不像，会丢细节、被长文稀释 | 逐个精配，能捕捉"关键词在不在" |
| 精度 | 粗 | 细 |
| 速度 | 快 | 慢（只能对少量候选） |

**所以二者组合，兼顾速度与精度：先 embedding 海选，再 rerank 精判。**

## 四、改造后的流程（代码里做了什么）

```
提问
  → embedding 检索：取 top8 候选（recall_k=8，给 rerank 留素材）
  → rerank 精排：CrossEncoder 对 8 个候选逐个 predict 打分
  → 按分数降序，取 top2
  → 用"最高分"判断有没有相关内容（替换原来的"距离阈值"）
  → 基于 top2 片段让模型回答
```

## 五、关键实现点（踩过的坑）

### 1. CrossEncoder 的 import 路径（新版 sentence-transformers）
```python
from sentence_transformers.cross_encoder import CrossEncoder  # ✅ 正确
# 旧版的 from sentence_transformers import CrossEncoder 已失效
```

### 2. 用法是"一对一对"打分
```python
pairs = [[question, doc] for doc in candidates]
scores = rerank_model.predict(pairs)   # 每个 (问题,候选) 一个分数
```

### 3. rerank 分数尺度
- `bge-reranker-base` 输出约在 [-4, 4]，越大越相关，负分/接近0 通常=不相关
- 判断阈值可取 0（"必须整体判为正相关才认为有内容"）

### 4. 懒加载 + 缓存两个模型
embedding + rerank 都是重量级（rerank 模型 1.1G），必须全局缓存只加载一次。

## 六、实际踩到的工程细节

### 模型体积
- `bge-reranker-base` 实际 **1.11G**（不是几百M），下载到 `rag-demo/models`（D盘）

### symlink 降级警告（无害）
```
huggingface_hub cache-system uses symlinks ... your machine does not support them
```
- **原因**：Windows 没开"开发者模式"或非管理员，无法建符号链接
- **影响**：模型照常用，只是多占磁盘（不去重）
- **解决**：忽略；或开 Windows 开发者模式；或设 `HF_HUB_DISABLE_SYMLINKS_WARNING=1` 消警告

### cache_dir 弃用警告（无害）
```
The Transformer cache_dir argument is deprecated.
```
- 新版 sentence-transformers 改了缓存传参方式，不影响功能

## 七、验证结果（真实测试）

| 测试 | 结果 |
|---|---|
| "三步法是什么" | rerank 给高分 → 正常答，且比之前更准 |
| "RAG清洗注意什么" | rerank 判低分 → 诚实说"笔记没有"，**不二次追问** |

## 八、给面试的完整叙事

现在你能讲一条完整的技术线：

> "我做了个学习笔记的 RAG 问答。一开始用 embedding 距离+阈值，发现'三步法'(0.878)和'RAG清洗'(1.003)只差0.125，临界区误判。于是我改成两段式：embedding 粗筛 top8 候选，再用 cross-encoder(bge-reranker-base) 精排打分，用 rerank 分数替代固定阈值判断，解决了临界区问题。"

**这一段讲完，面试官就知道你不是"跑通demo"级别，而是真的调试过 RAG 检索质量。**

---

*进阶方向：rerank 模型再大一号(如 bge-reranker-v2-m3)、或对多语言/更长上下文做微调。*