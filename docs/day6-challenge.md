# Day 6 挑战：给 Agent 加一个新工具（查汇率）

> 目标：让 Agent 能回答"100 美元等于多少人民币？"
> 这是你第一次完整走"造工具"流程。**先自己写，卡住了再看下面的提示。**

---

## 三步法（所有 Agent 工具都是这个套路，记住它）

```
第 1 步：写一个 Python 函数      → 真正干活的是它
第 2 步：在 TOOLS 里加 JSON Schema → 让模型"知道"有这个工具、什么情况用它
第 3 步：在 TOOL_FUNCTIONS 里注册  → 模型"说要调用它"时，代码能找到函数
```

对照 `tools.py` 里的 `get_weather`，把这三步在代码里指出来，确认看懂了再动手。

---

## 任务：在 tools.py 里加 `get_exchange_rate` 工具

### 第 1 步：写函数（放在 `calculator` 函数上方）

```python
def get_exchange_rate(currency: str) -> dict:
    """把指定外币换算成人民币（汇率）。"""
    RATES = {"USD": 7.2, "EUR": 7.8, "JPY": 0.048}
    # TODO: 查 RATES 表
    #   - 货币在表里 → 返回 {"currency": xxx, "rate": xxx}
    #   - 货币不在表里 → 返回 {"currency": xxx, "error": "不支持的货币：...，支持 USD/EUR/JPY"}
    # 提示：完全照着 get_weather 的结构写，只是数据不同
```

### 第 2 步：加 Schema（在 `TOOLS` 列表里加一项）

复制 `get_weather` 那一段模板，改成：

```python
    {
        "type": "function",
        "function": {
            "name": "get_exchange_rate",
            "description": "把指定外币换算成人民币（返回汇率），支持 USD、EUR、JPY",
            "parameters": {
                "type": "object",
                "properties": {
                    "currency": {"type": "string", "description": "货币代码，例如 USD"},
                },
                "required": ["currency"],
            },
        },
    },
```

### 第 3 步：注册（在 `TOOL_FUNCTIONS` 字典里加一行）

```python
TOOL_FUNCTIONS = {
    "get_weather": get_weather,
    "get_current_time": get_current_time,
    "calculator": calculator,
    "get_exchange_rate": get_exchange_rate,   # ← 加这一行
}
```

---

## 验证（分两步，先函数后 Agent）

**第 1 步：单独测函数**（不经过模型，直接测你的代码）：

```powershell
cd D:\study-practice\agent-basics
python -c "from tools import get_exchange_rate; print(get_exchange_rate('USD')); print(get_exchange_rate('BTC'))"
```

期望看到：`{'currency': 'USD', 'rate': 7.2}` 和一条 error 信息（不是报错崩溃）。

**第 2 步：测 Agent**：

```powershell
python main.py
```

依次问：
1. `100 美元等于多少人民币？`
2. `5000 日元呢？`
3. `1 个比特币值多少人民币？` ← 观察 Agent 怎么处理"工具做不到"的情况

---

## 常见坑（都是真实面试考点）

| 坑 | 现象 | 原因 |
|---|---|---|
| 忘了第 3 步注册 | 模型调用了工具，代码报 `KeyError` | 模型知道工具，但代码找不到函数 |
| 函数抛异常 | 整个 Agent 崩溃 | 工具函数必须自己捕获错误并返回 error 信息 |
| description 写太含糊 | 模型死活不调用这个工具 | 模型靠 description 决定"何时用" |
| 表里没有的货币 | Agent 说"查不到"或编造汇率 | 你的函数正确返回了 error，模型如实转达——**这是正确行为！** |

---

## 通关标准

- [ ] 单独测试通过（USD 有汇率、BTC 返回 error 不崩溃）
- [ ] Agent 能回答"美元/日元换算人民币"
- [ ] 问比特币时，Agent 如实说"不支持"，而不是编造一个数字
- [ ] 你不需要看这篇文档，也能给 Agent 加第 4 个工具（比如"随机笑话"）

全部通过 → 你的 Day 6 里程碑达成！🎉
