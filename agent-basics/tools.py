"""工具定义：这是 Agent 的"手"。

每个工具 = 一个 Python 函数 + 一份给模型看的 JSON Schema 描述。

关键认知：
- 模型【不会】真的执行代码，它只负责"决定"调用哪个工具、传什么参数
- 真正执行的是本文件里的 Python 函数
- 描述写得好不好，直接决定模型何时调用、怎么调用
"""
import ast
import operator
from datetime import datetime
import requests

import rag_client  # RAG 检索工具封装（读取 docs 笔记库回答问题）

# ---------- 1. 查询天气（演示用模拟数据） ----------


def get_real_weather(city: str) -> dict:
    """查询真实的实时天气（使用免费接口 wttr.in，无需 key）。"""
    url = f"https://wttr.in/{city}?format=j1"
    try:
        resp = requests.get(url, timeout=5)          # ① 发请求（5秒超时）
        data = resp.json()                            # ② 解析返回的 JSON

        current = data["current_condition"][0]        # ③ 取当前天气
        temp = current["temp_C"]                      # ④ 取温度（⚠️字符串）
        desc = current["weatherDesc"][0]["value"]     # ⑤ 取天气描述（英文）
        temp = int(temp)                              # ⑥ 转成整数（字符串→数字）

        return {
            "city": city,
            "temperature_c": temp,
            "condition": "热" if temp >= 20 else "冷",  # ⑦ 你自己处理描述
            "desc_en": desc,                         # ⑧ 原始英文也给模型看
        }
    except requests.RequestException as e:            # ⑨ 网络出错 → 返回 error，不崩溃！
        return {"city": city, "error": f"请求天气失败：{e}"}
    except (KeyError, ValueError) as e:               # ⑩ 返回结构不对 → 也返回 error
        return {"city": city, "error": f"天气数据解析失败：{e}"}


# ---------- 2. 当前时间 ----------
def get_current_time() -> dict:
    """返回当前的日期和时间。"""
    now = datetime.now()
    weekday = "周" + "一二三四五六日"[now.weekday()]
    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "weekday": weekday,
    }


# ---------- 3. 安全计算器（不用 eval，用 AST 解析，只放行四则运算） ----------
_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _safe_eval(node):
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("只支持简单的四则运算表达式")


def get_exchange_rate(currency: str) -> dict:
    """把指定外币换算成人民币（返回汇率），支持 USD、EUR、JPY。"""
    url = "https://open.er-api.com/v6/latest/USD"
    try:
        data = requests.get(url, timeout=5).json()
        rates = data["rates"]
        cny = rates.get("CNY")
        rate = rates.get(currency)
        if cny is None or rate is None:
            return {"currency": currency, "error": f"不支持的货币：{currency}，请用国际货币代码，例如 USD、EUR、JPY、GBP"}
        result = cny / rate
        return {
            "currency": currency,
            "rate": round(result,4),
            "base": "CNY"
        }
    except requests.RequestException as e: return {"currency": currency, "error": f"请求失败{e}"}
    except (KeyError, ValueError) as e: return {"currency": currency, "error": f"解析失败{e}"}




def get_dress_suggestion(temperature: int) -> dict:
    if temperature >= 25:
        suggestion = "推荐短袖、短裤、凉鞋"
    elif temperature >= 15:
        suggestion = "推荐长袖T恤 + 薄外套"
    elif temperature >= 5:
        suggestion = "推荐毛衣 + 厚外套"
    else:
        suggestion = "推荐羽绒服 + 围巾 + 手套"
    return {
        "temperature": temperature,
        "suggestion": suggestion
    }

def get_city_recommendation(city: str,activity: str) -> dict:
    _CITY_FUN = {
        "北京": {"景点": "故宫、长城", "吃饭": "烤鸭、涮肉", "购物": "王府井、三里屯", "运动": "奥森公园跑步"},
        "上海": {"景点": "外滩、迪士尼", "吃饭": "小笼包、生煎", "购物": "南京路、淮海路", "运动": "滨江骑行"},
        "成都": {"景点": "熊猫动物园", "吃饭": "火锅和冒菜", "购物": "火锅路", "运动": "健身"},
        "杭州": {"景点": "西湖", "吃饭": "西湖醋鱼", "购物": "杭州路", "运动": "散步"},
        # 成都、广州、杭州 任选 1-2 个也加点，给模型多点选择
    }
    if _CITY_FUN.get(city) is None:
        return {
            "city": city,
            "error": f"目前没有{city}这个城市的资料,只有{list(_CITY_FUN.keys())}"
        }
    else:
        choice = _CITY_FUN.get(city)
        if choice.get(activity) is None:
            return {
                "city": city,
                "activity": activity,
                "error": f"不知道该城市关于 {activity} 的推荐，只有{list(choice.keys())}"
            }
        else:
            return {
                "city": city,
                "activity": activity,
                "suggestion": f"在{city},你可以去{activity}"
            }


def rag_query(question: str) -> dict:
    """从「学习笔记」向量库检索相关内容，并让模型基于笔记回答。

    这是 RAG 工具：先检索笔记库(docs 目录的向量)，再让模型基于检索结果作答。
    若笔记里没相关内容，返回的结果会如实说明「没有」。
    """
    try:
        answer = rag_client.rag_query(question)
        return {"question": question, "answer": answer}
    except Exception as e:
        # 工具不崩溃：把错误回传给模型
        return {"question": question, "error": f"检索/回答失败：{e}"}


def calculator(expression: str) -> dict:
    """计算简单的数学表达式，如 '3.5 * (2 + 4)'。"""
    try:
        result = _safe_eval(ast.parse(expression, mode="eval"))
        return {"expression": expression, "result": result}
    except Exception as e:  # 工具出错不能崩，要把错误回传给模型
        return {"expression": expression, "error": str(e)}


# ---------- 工具注册表：给模型看的 JSON Schema 描述 ----------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_real_weather",
            "description": "查询指定城市的真实实时天气（温度、天气状况）。支持全球主要城市（中英文城市名均可），例如：北京 / Beijing / 东京",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名，例如：北京"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前的日期、时间和星期",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_exchange_rate",
            "description": "把任意国际法定货币换算成人民币（返回实时汇率）。支持全球主流法定货币，如 USD、EUR、JPY、GBP、CAD、AUD 等（不含加密货币）",
            "parameters": {
                "type": "object",
                "properties": {
                    "currency": {"type": "string", "description": "货币代码（ISO 三位码），例如 USD 表示美元"},
                },
                "required": ["currency"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_dress_suggestion",
            "description": "当用户问穿什么衣服时，根据温度推荐用户穿什么衣服，温度范围大概在-30摄氏度到40摄氏度，可结合天气温度使用",
            "parameters": {
                "type": "object",
                "properties": {
                    "temperature": {"type": "integer", "description": "摄氏温度（整数），例如 25"},
                },
                "required": ["temperature"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_city_recommendation",
            "description": "当用户问关于某个城市的某种推荐时回答，比如询问景点，吃饭，购物，运动等活动",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市，比如北京"},
                    "activity": {"type": "string", "description": "活动，比如吃饭"},
                },
                "required": ["city","activity"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算简单的数学表达式，例如 '3.5 * (2 + 4)'，返回计算结果",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "要计算的数学表达式，只支持 + - * / % ** 和括号"},
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rag_query",
            "description": "从用户的「学习笔记」知识库中检索并回答问题。当问题与 Function Calling、Agent 开发、API、RAG 等技术笔记相关时使用它",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "要查询的问题，例如：三步法是什么？"},
                },
                "required": ["question"],
            },
        },
    },
]

# 名字 -> 实际函数 的映射表（模型说调谁，我们就执行谁）
TOOL_FUNCTIONS = {
    "get_real_weather": get_real_weather,
    "get_current_time": get_current_time,
    "calculator": calculator,
    "get_exchange_rate": get_exchange_rate,
    "get_dress_suggestion": get_dress_suggestion,
    "get_city_recommendation": get_city_recommendation,
    "rag_query": rag_query,
}
