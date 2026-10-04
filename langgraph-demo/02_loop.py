# -*- coding: utf-8 -*-
"""LangGraph 第二个例子：条件边 + 环（循环）。

第一个例子是"一条直线"：START → upper → count → END
这个例子是"带环"的：START → step → 判断 →（还没够 3 次）回到 step
                                      →（够了）→ END

★ 这个例子的结构，就是你 Agent 的骨架：
    step       ↔  agent（问模型）
    判断函数    ↔  tools_condition（有 tool_calls 就继续）
    回到 step   ↔  tools 执行完回到 agent

运行：python 02_loop.py
"""
from typing import TypedDict

from langgraph.graph import StateGraph, START, END


# ---------- State：盒子里装一个数字 ----------
class State(TypedDict):
    count: int


# ---------- Node：每跑一次，count 加 1 ----------
def node_step(state: State):
    print(f"  [step] 收到 count={state['count']}")
    return {"count": state["count"] + 1}


# ---------- 路由函数：决定下一步去哪个节点（返回"节点名"或 END）----------
def should_continue(state: State):
    """注意：这个函数返回的是【字符串】——下一个节点的名字。"""
    if state["count"] < 3:
        print(f"  [判断] count={state['count']} < 3 → 继续循环")
        return "step"          # 回到 step 工位（形成环）
    print(f"  [判断] count={state['count']} >= 3 → 结束")
    return END                 # 下班


# ---------- 组装图 ----------
builder = StateGraph(State)
builder.add_node("step", node_step)

builder.add_edge(START, "step")                              # 入口 → step
builder.add_conditional_edges("step", should_continue)       # ★ 条件边：让函数决定

graph = builder.compile()

# ---------- 跑 ----------
print("=== 开始 ===")
result = graph.invoke({"count": 0})
print("=== 结束 ===")
print("最终盒子内容：", result)
