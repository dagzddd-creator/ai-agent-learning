# agent-basics：你的第一个 Agent（Function Calling 入门）

一个基于 **DeepSeek API + Function Calling** 的最小 Agent。
它能"动手干活"：查天气、看时间、做计算，而不只是聊天。

## 核心概念：Agent 循环

```
你提问
  ↓
大模型思考："我需要查天气才能回答"
  ↓  （模型返回 tool_calls，而不是最终答案）
我们执行工具（真正干活的是我们的代码！）
  ↓  （把工具结果回传给模型）
大模型基于结果组织最终回答
  ↓
打印给你
```

**关键认知：模型不会真的执行任何代码。**
它只是根据工具描述"说"：我要调用 `get_weather(city="北京")`。
真正执行的是 `tools.py` 里的 Python 函数，结果再喂回给模型。

## 运行

```bash
pip install -r requirements.txt
copy .env.example .env    # 然后编辑 .env，填入你的 DeepSeek API Key
python main.py
```

## 代码结构

| 文件 | 作用 |
|---|---|
| `main.py` | Agent 主循环：发消息 → 收 tool_calls → 执行 → 回传 → 得答案 |
| `tools.py` | 工具实现（3 个）+ 给模型看的 JSON Schema 描述 |

## 动手练习（由易到难）

1. **改描述**：修改 `get_weather` 的 `description`，加一句"仅支持中国城市"，看看模型行为变化
2. **加工具**：新增一个"查汇率"工具（内置简单汇率表）
3. **加参数**：让 `get_weather` 支持 `unit` 参数（摄氏/华氏）
4. **批量查询**：把参数 `city` 改成 `cities`（数组），一次查多个城市
5. **进阶**：把模拟天气换成真实 API（如免费的 [wttr.in](https://wttr.in)）

## 常见坑（面试也爱问）

- ❌ **忘记把 assistant 的 tool_calls 消息加入历史** → 模型会"失忆"，报 tool_call_id 不匹配
- ❌ **工具执行抛异常不捕获** → 整个循环崩溃。应该把错误信息作为结果回传给模型，让它自己调整
- ❌ **参数解析失败**（模型返回了不合法的 JSON）→ 需要 try/except 兜底
- ❌ **没有轮次上限** → 模型可能陷入无限调工具（本项目的 `MAX_TOOL_ROUNDS` 就是干这个的）

## 为什么用 `openai` 库调 DeepSeek？

DeepSeek 的 API 与 OpenAI 完全兼容（同一个协议），所以直接用 `openai` 库、
把 `base_url` 换成 DeepSeek 的地址即可。**"一套代码，换 base_url 就能换模型"**
——这个生态事实对 Agent 开发者很重要。
