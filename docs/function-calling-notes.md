# Agent 开发入门：Function Calling 完整笔记

> 这是你实战总结的笔记，围绕"如何让大模型调用工具"展开。
> 对应代码：`agent-basics/tools.py` + `main.py`（6 个工具，自己写的）

---

## 一、一句话理解 Function Calling

**让大模型不只"动嘴"（生成文字），还能"动手"（调用你的代码拿数据、执行动作）。**

模型不会真的执行代码——它只负责"决定调哪个工具、传什么参数"，真正执行的是我们自己写的 Python 函数。

```
用户提问 → 模型看菜单(TOOLS) → 决定调 get_weather(city="北京")
→ 我们的代码执行 → 结果回传 → 模型组织回答
```

## 二、三步法：加一个工具的完整流程

```
第 1 步  写 Python 函数       → 真正干活的部分
第 2 步  在 TOOLS 加菜单项     → 让模型"知道"这个工具、何时用、怎么用
第 3 步  在 TOOL_FUNCTIONS 注册 → 模型说要调用时，代码能找到函数
```

**每次改工具都自查一遍**（你实战踩过的坑）：

```
① 函数改了吗？(def)  ② 菜单改了吗？(TOOLS)  ③ 注册改了吗？(TOOL_FUNCTIONS)
```

- 改了函数没改菜单 → 模型不知道新能力（描述"封印"了能力）
- 改了菜单没注册 → 模型调用了但代码 KeyError 崩溃

## 三、菜单（TOOLS）的四个关键字段

```python
{
    "type": "function",
    "function": {
        "name": "get_weather",          # 必须和函数名一致
        "description": "...",           # 给模型看的"说明书"，决定它何时/如何使用
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名"},
            },
            "required": ["city"],       # 必填参数
        },
    },
}
```

**口令**：properties 是参数清单，键名对参数名，type 对类型，required 说谁不能缺。

**类型对照表**（JSON Schema 和 Python 不一样！）：

| Python | JSON Schema |
|---|---|
| `str` | `"string"` |
| `int` | `"integer"` |
| `float` | `"number"` |
| `bool` | `"boolean"` |

## 四、防乱编 description（Checklist）

写 description 就问自己 4 个问题：

| 检查项 | 问自己 | 例子 |
|---|---|---|
| ① 何时用 | 什么时候该调这个工具？ | "当用户问外币换算人民币时" |
| ② 支持范围 | 支持哪些取值？ | "支持全球主流法定货币（不含加密货币）" |
| ③ 参数格式 | 参数填什么格式？ | "ISO 三位货币代码，如 USD" |
| ④ 边界 | 什么情况做不到？ | "不支持的货币返回 error，如实告知" |

**核心认知：模型的世界 = 它从 description 里看到的世界，不是你的代码。**
描述写得含糊 → 模型乱传参数/编造；描述精确 → 模型用得准。

## 五、工具开发的铁律

1. **工具永远返回字典，绝不崩溃**
   - 查不到数据 → `return {"error": ...}`（不是抛异常）
   - 网络出错 → `except` → `return {"error": ...}`
   - 崩溃 = 整个 Agent 死掉；error 字典 = 模型能转述、能补救
2. **职责分离：工具给真相，模型给表达**
   - 工具返回原始数据（如英文 `desc_en`），别在工具里硬翻译
   - 模型负责翻译、美化、组织语言——它的本行
3. **参数化设计，不用全局变量**
   - Agent 调用工具顺序不可控，每个工具必须"给参数就出结果"
   - 靠 description 引导模型"先查天气 → 再拿温度调穿搭"

## 六、接真实 API 的 4 步链

```
① 拼 URL        f"https://wttr.in/{city}?format=j1"
② 发请求        requests.get(url, timeout=5)
③ 解析 JSON     data = resp.json()
④ 取值 + 返回    data["current_condition"][0]["temp_C"]
```

**先打开 URL 看返回结构**（怎么剥洋葱取值），再写代码——这是标准流程。

**try/except 双保险**：

```python
try:
    data = requests.get(url, timeout=5).json()
except requests.RequestException as e:
    return {"error": f"请求失败：{e}"}        # 拦网络错
except (KeyError, ValueError) as e:
    return {"error": f"解析失败：{e}"}        # 拦数据不对
```

## 七、常见坑汇总（全是实战踩的）

| 坑 | 错 | 对 |
|---|---|---|
| JSON 类型 | `"type": "str"` | `"type": "string"` |
| 接口返回字符串 | `temp_C` 直接用 | `int(temp_C)` 转数字 |
| 数组取值 | 直接取 | `[0]` 取第一个 |
| 条件逻辑 | `>=20` 写"多云" | `>=20` 写"晴"（高温=晴） |
| 改了函数忘改菜单 | 模型还是旧行为 | 三处同步改 |
| error 文案是模板 | `"...支持..."` | 写完整真实文案 |

## 八、悟到的工程观

1. **"菜单=模型的世界"**：函数能力再强，描述不更新，模型就用不了新能力
2. **错误信息也是数据**：好的 error 里带上"支持哪些"（`list(keys())`），让模型能自我修正
3. **模型会自己编排**：多工具配合（天气→穿搭→计算器），你只要描述清晰，它自己串联
4. **工具增加 = 能力增加**：每个工具就是 Agent 的一个"新技能"，向模型注册即可

---
*下一步：RAG——让 Agent 能"检索你自己的资料库"再回答（给模型喂它没学过的知识）。*