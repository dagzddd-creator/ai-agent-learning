# -*- coding: utf-8 -*-
"""LangGraph 最小例子（和 Agent 无关，纯"流水线"）。

目的：先看懂 State / Node / Edge 三个概念，再回去改 Agent。

流水线：START → upper（转大写）→ count（数长度）→ END
盒子(State) 一路传下去，每个工位只往盒子里放"自己负责的那部分"。

运行：python 01_minimal.py
"""
from typing import TypedDict

from langgraph.graph import StateGraph, START, END


# ---------- ① State：盒子里装什么 ----------
# 相当于你的 messages 列表，只不过这里装了 text 和 length 两样东西
class State(TypedDict):
    text: str      # 一个字符串
    length: int    # 一个数字


# ---------- ② Node：工位（收盒子，返回"要放进盒子的东西"）----------
def node_upper(state: State):
    """工位1：把 text 变大写。注意：只返回 text，不返回 length。"""
    print(f"  [upper] 收到 text={state['text']!r}")
    return {"text": state["text"].upper()}          # ← 只是"更新"，不是整个盒子


def node_count(state: State):
    """工位2：数 text 的长度。注意：只返回 length，不返回 text。"""
    print(f"  [count] 收到 text={state['text']!r}")
    return {"length": len(state["text"])}           # ← 只更新 length


# ---------- ③ 组装图 ----------
builder = StateGraph(State)          # 用 State 的类型建一张图
builder.add_node("upper", node_upper)   # 放一个工位，起名 upper
builder.add_node("count", node_count)   # 放一个工位，起名 count

builder.add_edge(START, "upper")        # 传送带：入口 → upper
builder.add_edge("upper", "count")      # 传送带：upper → count
builder.add_edge("count", END)          # 传送带：count → 出口

graph = builder.compile()               # 编译成"可运行的东西"

# ---------- ④ 跑起来 ----------
print("=== 开始 ===")
result = graph.invoke({"text": "hello"})   # 往盒子里放初始内容，启动流水线
print("=== 结束 ===")
print("最终盒子内容：", result)
