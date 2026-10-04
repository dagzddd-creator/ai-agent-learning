# 读懂你的第一个 Agent（零基础版拆解）

> 阅读方式：打开 `agent-basics/tools.py` 和 `main.py`，对着本文档一段一段看。
> 看不懂的术语，文中都有大白话解释。

---

## 0. 大局观：一家餐厅 🍽️

把整个项目想成一家餐厅：

| 角色 | 对应代码 | 职责 |
|---|---|---|
| **前台服务员** | `main.py` | 接待你（收问题）、跑腿（传话、取菜）、上菜 |
| **菜单** | `tools.py` 里的 `TOOLS` | 让"大脑"知道店里有什么菜、什么菜配什么料 |
| **后厨** | `tools.py` 里的函数 | 真正做菜的地方（查天气、看时间、算数） |
| **点名册** | `tools.py` 里的 `TOOL_FUNCTIONS` | 菜单上的菜名 → 对应哪个厨师 |
| **总厨大脑** | 大模型（DeepSeek） | 只负责"想"：看菜单决定点什么菜，绝不亲自下厨 |

**最关键的一句话：模型永远不会真的执行代码。**
它只负责"决定"调哪个工具、传什么参数；执行永远是你的 Python 代码。

完整流程（你问"北京天气怎么样"）：

```
你提问 → 大脑看菜单（TOOLS）→ 决定点"get_weather(city=北京)"这道菜
→ 前台拿单子去后厨执行 → 端菜回来（工具结果）
→ 大脑看着菜组织语言 → 上菜（最终回答）
```

---

## 1. tools.py 拆解（三个部分）

### 1.1 函数区：每个工具 = 一个普通函数

看 `get_weather`，它和你学过的普通函数没有区别：

```python
_CITY_TEMP = {                      # 一个"查表"：北京 → 18度
    "北京": 18, "上海": 22, ...
}

def get_weather(city: str) -> dict:  # 函数名(参数: 类型) -> 返回类型
    temp = _CITY_TEMP.get(city)      # 查表。用 .get() 而不是 [city]
    if temp is None:                 # 查不到 → 返回错误信息（不崩溃！）
        return {"city": city, "error": f"没有 {city} 的天气数据，..."}
    condition = "晴" if temp >= 20 else "多云"   # 简化版 if-else
    return {"city": city, "temperature_c": temp, "condition": condition}
```

**三个你可能不懂的点：**

- **`.get(city)` 而不是 `[city]`**：`字典[键]` 查不到会**直接崩溃**（KeyError）；
  `.get(键)` 查不到返回 `None`，我们可以自己处理。工具函数**永远不能崩溃**，
  因为崩溃 = 整个 Agent 死掉。
- **`if temp is None:`**：None 表示"啥都没有"。查不到城市就走这个分支，
  返回一条**错误信息**——注意，错误也是"正常返回"，只是内容说明错了。
- **`"晴" if temp >= 20 else "多云"`**：一行 if-else，等价于：
  ```python
  if temp >= 20:
      condition = "晴"
  else:
      condition = "多云"
  ```

### 1.2 TOOLS 列表：给模型看的"菜单"

```python
TOOLS = [
    {
        "type": "function",        # 固定写法：这是"函数型工具"
        "function": {
            "name": "get_weather", # 菜名（必须和函数名完全一致）
            "description": "查询指定城市的天气...",   # 说明书：什么时候点这道菜
            "parameters": {        # 点菜需要的"配料表"
                "type": "object",
                "properties": {    # 配料明细
                    "city": {"type": "string", "description": "城市名，例如：北京"},
                },
                "required": ["city"],  # 必填配料
            },
        },
    },
    # ... 时间、计算器，结构一样
]
```

**理解要点：** 模型不认识 Python 代码，它只看这份"菜单"。
- `description` 写得越清楚，模型越知道"什么时候该用它"
- 模型会**照着 `properties` 填参数**——你说参数是 string，它就给字符串

### 1.3 TOOL_FUNCTIONS：点名册

```python
TOOL_FUNCTIONS = {
    "get_weather": get_weather,       # 菜单上的名字 → 真正的函数
    "get_current_time": get_current_time,
    "calculator": calculator,
}
```

**为什么需要它？** 模型说"我要 get_weather"，但代码里怎么找到 `get_weather`
这个函数？——靠这张"菜名 → 厨师"的对照表。main.py 拿到菜名，来这里一查，
就知道该执行哪个函数。

---

## 2. main.py 拆解（三个部分）

### 2.1 准备工作

```python
load_dotenv()          # 读 .env 文件里的 key（配置）
client = OpenAI(...)   # 建一条"电话线"：和基元律动服务器通话
MODEL = "deepseek-v4-flash-0731"   # 要叫哪个模型
MAX_TOOL_ROUNDS = 5    # 安全阀：最多让模型调 5 轮工具
```

### 2.2 run_tool：执行工具的"接线员"

```python
def run_tool(name, arguments):
    func = TOOL_FUNCTIONS[name]     # 点名册查表 → 找到真函数
    args = json.loads(arguments)    # 把"文本参数"变成 Python 字典
    result = func(**args)           # 调用函数（** 是把字典拆成参数）
    return json.dumps(result, ensure_ascii=False)  # 结果变回文本
```

**两个魔法知识点：**

- **`json.loads` / `json.dumps`**：模型和你的代码之间传的是**文本**。
  模型给的参数是字符串 `'{"city": "北京"}'`，`json.loads` 把它变成字典
  `{"city": "北京"}` 才能用；函数返回的字典要 `json.dumps` 变回字符串，
  才能放回对话记录发给模型。
- **`func(**args)`**：`**` 是"把字典拆开，按名字传给参数"。看例子：
  ```python
  args = {"city": "北京"}
  get_weather(**args)
  # 完全等价于：
  get_weather(city="北京")
  ```

### 2.3 chat_loop：主循环

```python
while True:                     # 一直循环，直到用户输入 exit
    user_input = input("你: ")  # 等你提问
    messages.append({"role": "user", "content": user_input})  # 记下你的问题

    for _ in range(MAX_TOOL_ROUNDS):        # 内层循环：可能要多轮
        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS)   # 问模型
        msg = resp.choices[0].message

        if msg.tool_calls:                  # 模型说"我要调工具"
            messages.append(msg)            # ① 把"点菜单"记进历史（不能省！）
            for tc in msg.tool_calls:       # ② 可能同时点好几道菜
                result = run_tool(tc.function.name, tc.function.arguments)
                messages.append({           # ③ 把"菜"端回来给模型
                    "role": "tool",
                    "tool_call_id": tc.id,  # 必须原样回传！模型靠它对上号
                    "content": result,
                })
            continue                        # ④ 带着菜继续问模型
        else:
            print(msg.content)              # 模型直接回答 → 上菜
            messages.append(msg)
            break
```

**核心认知：模型没有记忆。**
每次调用 `chat.completions.create`，`messages` 里**装着你从头到尾的所有对话**
（你的问题 + 模型调工具的记录 + 工具结果），模型靠这份完整记录才能"记得"
之前发生了什么。这就是为什么每一步都要 `messages.append(...)`。

---

## 3. 三个"第一次看不懂很正常"的知识点小结

| 知识点 | 一句话解释 |
|---|---|
| `**args` | 把字典拆开按名字传给函数参数 |
| `json.loads/dumps` | 文本 ⇄ 字典 的转换（模型只能收发文本） |
| 错误要 return 而不是 raise | 工具出问题要"告诉模型"，而不是让整个程序崩溃 |

---

## 4. 看懂之后：查汇率 = 套模板 🎁

看懂 `get_weather` 后你会发现，新工具就是**复制骨架、换三样东西**：

```
函数名     get_weather  → get_exchange_rate
查的表     _CITY_TEMP   → RATES = {"USD": 7.2, "EUR": 7.8, "JPY": 0.048}
描述/参数  天气/城市     → 汇率/货币代码
```

任何工具的通用模板：

```python
def 工具名(参数: 类型) -> dict:
    """说明书：给模型看的用途描述"""
    表 = {...} 或 自己的逻辑
    if 查不到:
        return {"...": "错误信息"}    # 不崩溃，告诉模型
    return {"...": 结果}

# 然后在 TOOLS 里加菜单项（复制 get_weather 那段改名字和描述）
# 然后在 TOOL_FUNCTIONS 里注册一行
```

**你现在的任务不是"发明"，是"模仿"。** 打开 `tools.py`，对照 get_weather，
把函数名、表、描述换掉，就是你的新工具。写不出来 = 还没看够，回去对着
`get_weather` 一行行念三遍，然后动手。
