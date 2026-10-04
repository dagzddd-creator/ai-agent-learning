# 第 1 周学习清单：Python 补基础 + 跑通 Function Calling

> 目标：到周末时，你能**独立看懂并改造** `agent-basics` 项目，给它加一个自己的新工具。
> 每天 1~2 小时即可，重点是"动手"，不是"看完"。

## 检查点（周末自测）

- [ ] 能说出 Function Calling 的完整流程：模型怎么"决定"调工具？谁真正执行工具？
- [ ] 能独立给 `tools.py` 加一个工具（比如"查汇率"），并让 Agent 用起来
- [ ] 能解释：为什么模型返回的 `tool_call_id` 要原样传回？
- [ ] 明白 `装饰器` 是什么（不要求精通，看懂 `@` 语法即可）

---

## Day 1｜环境搭建 + 跑通第一个 Agent

**任务：**
1. 在 https://platform.deepseek.com 注册账号，创建 API Key（新用户有免费额度）
2. 在项目根目录创建 `.env` 文件（复制 `.env.example`），填入 Key
3. `pip install -r requirements.txt`
4. `python main.py`，跑通上面 4 个示例问题

**理解重点：** 整体看一遍 `main.py`，画出它的执行流程图——不用看懂每行，先有"循环"的概念。

**产出：** 终端里跑通一次多工具调用（最后一个问题）。

## Day 2｜Python 补基础：装饰器（重点）

**任务：**
1. 学习装饰器：廖雪峰教程「装饰器」章节，或搜索"Python 装饰器 通俗理解"
2. 动手写 3 个小例子：
   - 打印函数执行时间的装饰器
   - 登录校验装饰器（伪代码即可）
   - 一个带参数的装饰器
3. 思考：为什么 Agent 框架（如 LangChain）里到处都是装饰器？

**产出：** `practice/decorators.py`，写满你的 3 个例子。

## Day 3｜Python 补基础：async + requests

**任务：**
1. 学习 `async/await` 的**概念**即可（不用深入 asyncio 细节）
2. 学习 `requests` 库：GET/POST、超时、异常处理
3. 练习：用 requests 调用一个免费 API（如 https://api.github.com/users/你的用户名）
4. 思考：为什么 Agent 调多个工具时，异步/并发能省时间和钱？

**产出：** `practice/requests_demo.py`，能打印 GitHub 用户名和粉丝数。

## Day 4｜深入 Function Calling（工具定义）

**任务：**
1. 重新仔细读 `tools.py` 里 `TOOLS` 列表的 JSON Schema 结构
2. 回答：
   - `description` 为什么重要？（模型靠它决定何时调用工具）
   - `required` 字段是什么作用？
   - 参数类型写错会怎样？（自己改错试试！）
3. 看 DeepSeek 官方文档的 Function Calling 章节：https://api-docs.deepseek.com/zh-cn/guides/function_calling

**产出：** 在 `tools.py` 里**故意**写错一个参数类型，观察 Agent 报什么错，然后改回来。

## Day 5｜深入 Function Calling（多工具 + 错误处理）

**任务：**
1. 复述 Agent 循环每一步在 `main.py` 中的对应代码
2. 实验：
   - 让模型调用一个**不存在的工具名**，观察行为
   - 给工具传错误的参数类型，看模型怎么应对
   - 问一个工具解决不了的问题（如"今天股票涨了吗"），看模型的兜底行为
3. 理解 `MAX_TOOL_ROUNDS` 为什么存在

**产出：** 记录 3 个实验现象，写进 `practice/notes.md`。

## Day 6｜实战：给 Agent 加一个新工具

**任务（本周核心）：**
1. 给 `tools.py` 新增一个工具，任选：
   - **查汇率**：写死一个简单汇率表（USD→CNY 等）
   - **随机笑话**：内置几个笑话随机返回
   - **英语翻译**：接一个免费翻译 API
2. 步骤：写函数 → 在 `TOOLS` 里加描述 → 在 `TOOL_FUNCTIONS` 里注册 → 测试
3. 进阶：让它支持"批量查询多个城市天气"（提示：参数改成城市列表）

**产出：** 你的 Agent 能用上你自己的新工具！这是你 Agent 开发的第一块里程碑。

## Day 7｜总结输出

**任务：**
1. 写一篇学习笔记（公众号 / 博客 / 本地笔记皆可），主题任选：
   - 《从零理解 Function Calling》
   - 《我做的第一个 AI Agent》
2. 把本周所有 `practice/` 代码整理好，提交到 GitHub（如果还没有账号，注册一个）
3. 预习下周：搜索"RAG 是什么"，建立初步概念

**产出：** 一篇笔记 + 一个 GitHub 仓库。下周见！

---

## 📌 卡住了怎么办？

1. 把报错信息**原样**复制给 DeepSeek / Claude，让它们解释并给修复方案
2. 回看 `main.py` 的注释，逐行对照
3. 记住：**模型不是你，工具执行才是你**——出问题时先想"这行代码是谁在跑"
