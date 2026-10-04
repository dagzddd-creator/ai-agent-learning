# 下一步学习计划（含 Python 基础补强）

> 写在 2026-10-01 学习之后。随时可以翻回来看"我学到哪了、下一步做什么"。

---

## 一、当前成果盘点

| 主题 | 成果 | 文件 |
|---|---|---|
| **Function Calling** | 7 个工具（含真实天气/汇率 API）、description 防乱编 | `agent-basics/tools.py` |
| **RAG** | 两段式检索（embedding 粗筛 + rerank 精排）、清洗/切分调优 | `rag-demo/` |
| **Reflection 范式** | 四轮护栏调优实验（凑数 → 放水 → 精准） | `agent-basics/reflection_demo.py` |
| **LangGraph** | 概念 + 重写 Agent + Checkpointer 记忆 + 自己修 bug | `langgraph-demo/`、`main_langgraph*.py` |
| **学习笔记** | 10 篇实战总结 | `docs/` |

**能讲出来的项目故事（面试素材）**：
1. 描述"封印"能力：改了函数忘改菜单 → 模型只能查 3 种货币
2. RAG 清洗过度误删代码块知识 → 诊断脚本定位 → 修好
3. 临界区误判（0.878 vs 1.003）→ 用真实数据定阈值 → 引入 rerank
4. Reflection critic 的"凑数"与"放水" → 给方法而非态度
5. LangGraph checkpointer 的 `route` 崩溃 → `getattr` 防御性修复

---

## 二、Python 基础补强：**在项目代码里补，不要啃教程**

你项目里已经出现过几乎所有需要的语法点。**对着真实代码补，比看教程快 10 倍。**

| 语法点 | 你项目里哪里出现过 | 目标 |
|---|---|---|
| 字典读写非对称（读 `.get()` / 写 `[]`） | `count_words`、`TOOL_FUNCTIONS` | ✅ 已掌握（还懂为什么） |
| `.get(key, 默认值)` | 今天的练习 | ✅ 已掌握 |
| **关键字参数**（`content=xxx`） | `HumanMessage(content=...)` ← 今天踩过坑 | 要能分清"参数名"和"变量名" |
| f-string | 到处都是 | ✅ 会用 |
| `try / except` | `get_real_weather`、`calculator` | ✅ 会用 |
| 字符串方法 `split / join / strip / replace` | 清洗 Markdown、`''.join(...)` | 会用 |
| **列表推导式**（`[x for x in ... if ...]`） | `''.join(c.lower() for c in s if c.isalnum())` | 看懂 + 会写简单的 |
| 类型注解（`x: str -> dict`） | 每个工具函数 | 会看会写 |
| `import` 语句 | 今天写 `SqliteSaver` 那个 | ✅ 已掌握 |
| 类与继承 | `class State(TypedDict)` | 看懂即可，暂不深究 |
| `for` + `enumerate` / `break` / `continue` | Agent 循环 | break 会用；enumerate 要学 |

---

## 三、练法：三轨制（重点在第三条）

| 轨道 | 做法 | 频率 |
|---|---|---|
| **填空轨** | 我给带 `# TODO` 的骨架，你补关键行 | 学新功能时 |
| **改错轨** | 我给有 bug 的代码，你找出来修 | 巩固时 |
| **从零轨** | 我出小题（10~20 行），你独立写 | **每天 1 题，10~15 分钟** |

**从零轨是补"产出能力"的唯一办法**——读一百遍代码也长不出这个肌肉。

练习文件放：`D:\study-practice\python-practice\dayNN_xxx.py`（能看见积累）

---

## 四、每日一题清单（由易到难，做过的打勾）

- [x] **day01** 统计列表里每个词出现的次数（字典计数套路）✅ 已完成
- [ ] **day02** 统计一句话里每个词出现次数（新技巧：`text.split()`）
- [ ] **day03** 找出出现次数最多的词
- [ ] **day04** 求列表里所有偶数的和
- [ ] **day05** 把列表里小于 0 的数变成 0（原地修改）
- [ ] **day06** 判断回文（忽略大小写和标点）
- [ ] **day07** 反转字典的键和值
- [ ] **day08** 两个列表合成一个字典（keys + values → dict）
- [ ] **day09** 统计字符串里出现过哪些字符（去重后排序）
- [ ] **day10** 读一个文件，打印它的行数和字符数
- [ ] **day11** 把长文本按句号切成句子列表
- [ ] **day12** 用 try/except 安全地把字符串转成数字（转不了返回 None）
- [ ] **day13** 用列表推导式：从列表里筛出长度 > 3 的词并转大写
- [ ] **day14** 写一个最简单的类（有属性 + 一个方法）
- [ ] **day15** 综合：读 `docs/` 目录，统计每个文件有多少字

**规则**：
- 自己先想，卡住可以问，但**我只给提示、不直接给答案**
- 写完一定自己跑一遍验证
- 做完一题就在上面打勾

---

## 五、学习主题路线（技术线）

### 近期（LangGraph 收尾）
- [ ] **Interrupt**：调用危险工具前暂停，等人工确认
- [ ] **Time travel**：回到某一步重跑（调试利器）
- [ ] 把 LangGraph 版 Agent 也接上 `rag_query`（已验证可用）

### 中期（补齐面试知识点）
- [ ] **Agent 记忆机制**：短期（对话历史）vs 长期（向量库）
- [ ] **上下文工程**：怎么管理不断变长的上下文
- [ ] **MCP / A2A 协议**：2025 面试热点
- [ ] **RAG 评估**：怎么衡量 RAG 好不好（RAGAS 等）
- [ ] **多 Agent 协作**：什么场景需要，做个 demo

### 求职准备
- [x] **把项目推 GitHub** ✅ 已完成（2026-10-01）
      **https://github.com/dagzddd-creator/ai-agent-learning**
      32 个文件 / 2934 行；`.env`、1.1GB 模型、sqlite 本地数据均已确认排除；
      提交已归属到自己账号（`dagzddd-creator`）
- [ ] 读 Hello-Agents 的 **Extra01 面试题 + 参考答案**，自查哪些答不上
- [ ] 把"8 道已会的题"写成**自己的答案**（不要背原文）
      → **从 RAG 第一题开始**（"RAG 原理 + 相比微调的优势"），用 5 段骨架填
- [ ] 练习"3 分钟讲清一个项目"

---

## 六、恢复点（下次从这里继续）

**优先级最高：面试答案**（技术材料够了，现在差"会讲"）
1. **填 RAG 第一题的 5 段骨架**（最高频开场题）← 首选
2. **做 day02 小题**（10 分钟热身，保持"每天一题"）
3. **学 Interrupt**（LangGraph 继续，填空轨）
4. 写 LangGraph 学习笔记（把概念→重写→checkpointer→debug 那条线沉淀）

**日常维护 GitHub**（每次学习完）：
```powershell
cd D:\study-practice
git add .
git commit -m "what you did today"
git push
```

**环境状态**（不用重装）：
- Python 包都在（langgraph 在 `D:\新建文件夹 (5)\Lib\site-packages`）
- `.env` 配好了基元律动（真 key 只在这个文件，已被 gitignore）
- 模型缓存在 `D:\study-practice\rag-demo\models`（1.1GB，不提交）
- Git 仓库已初始化，remote 指向自己的 GitHub

---

*今天的核心收获不是"学会了 LangGraph 的 API"，而是明白了：**框架样板不用背（会认会改就行），业务逻辑必须能自己写（每天一题练）**。*
