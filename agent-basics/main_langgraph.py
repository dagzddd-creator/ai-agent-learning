# -*- coding: utf-8 -*-
"""用 LangGraph 重写你的 Agent —— 和手写版 main.py 逐项对照。

★ 对照表（左边是你手写的，右边是 LangGraph 版的）：
  ┌────────────────────────────────────────┬──────────────────────────────────────┐
  │ 手写版 main.py                          │ 本文件（LangGraph）                   │
  ├────────────────────────────────────────┼──────────────────────────────────────┤
  │ messages 列表（自己 append）             │ State（框架按 add_messages 规则追加）  │
  │ client.chat.completions.create(...)     │ agent_node                            │
  │ if msg.tool_calls: ... else: break      │ 条件边 route()                        │
  │ for tc in msg.tool_calls: run_tool(...) │ tools_node                            │
  │ for _ in range(MAX_TOOL_ROUNDS) 循环     │ add_edge("tools","agent") 这条环      │
  │                                         │ + recursion_limit（框架的轮次上限）    │
  └────────────────────────────────────────┴──────────────────────────────────────┘

★ 最大的区别：手写版你手动管理 messages、手动写循环；
  这里你只声明"图长什么样"，循环由框架按边来跑。

运行（在 agent-basics 目录下）：
    python main_langgraph.py
"""
import json
import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph

from tools import TOOLS, TOOL_FUNCTIONS

load_dotenv()   # 读同目录的 .env

# ---------- 模型：用 ChatOpenAI 接基元律动，并绑定你 tools.py 里的 7 个工具 ----------
llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL", "deepseek-v4-flash-0731"),
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL", "https://tokenrhythm.studio/v1"),
    temperature=0,
).bind_tools(TOOLS)      # ★ 你写的 TOOLS 菜单，直接交给模型（一个字没改）

# 你在手写版里写的那段 system prompt，原样搬过来
SYSTEM_PROMPT = """你是一个乐于助人的助手。
- 天气/汇率/时间等实时数据 → 用 get_real_weather / get_exchange_rate / get_current_time
- 涉及个人学习笔记、Agent开发、RAG等知识 → 用 rag_query
- 简单常识问题 → 直接回答，不要调用工具
不要凭空编造数据；不确定时调用工具获取。"""


# ---------- 节点①：问模型（= 手写版里的 create(...) 那一段）----------
def agent_node(state: MessagesState):
    """收 State → 问模型 → 返回新消息（框架会追加到 messages）"""
    return {"messages": [llm.invoke(state["messages"])]}


# ---------- 节点②：执行工具（= 手写版里的 run_tool + for 循环）----------
def tools_node(state: MessagesState):
    """执行模型要求的所有工具，把结果作为 ToolMessage 返回"""
    last = state["messages"][-1]        # 最后一条是模型刚回的（含 tool_calls）
    outputs = []
    for tc in last.tool_calls:          # tc = {"name":..., "args":{...}, "id":...}
        # ★ 注意一个区别：手写版里 tc.function.arguments 是 JSON 字符串，要 json.loads；
        #   这里 tc["args"] 已经是 dict 了，不用解析。
        print(f"  🔧 调用工具: {tc['name']}({json.dumps(tc['args'], ensure_ascii=False)})")
        result = TOOL_FUNCTIONS[tc["name"]](**tc["args"])
        outputs.append(ToolMessage(
            content=json.dumps(result, ensure_ascii=False),
            tool_call_id=tc["id"],      # 必须对上号（你手写版里也是这个道理）
        ))
    return {"messages": outputs}


# ---------- 条件边：决定下一步去哪（= 手写版的 if msg.tool_calls）----------
def route(state: MessagesState):
    """模型还要调工具 → 去 tools；否则 → 结束"""
    last = state["messages"][-1]
    return "tools" if last.tool_calls else END


# ---------- 组装图 ----------
builder = StateGraph(MessagesState)         # State 用官方预置的 MessagesState
builder.add_node("agent", agent_node)       # （它就等于"messages + add_messages"）
builder.add_node("tools", tools_node)

builder.add_edge(START, "agent")            # 入口 → agent
builder.add_conditional_edges("agent", route)   # agent 之后由 route 决定
builder.add_edge("tools", "agent")          # ★ 环：工具执行完回到 agent
                                            #   （这就是手写版的 for 循环）

graph = builder.compile()


# ---------- 命令行循环（这部分和手写版几乎一样）----------
def main():
    print("🤖 LangGraph 版 Agent 已启动！（输入 exit 退出）")
    print("   试试：北京天气怎么样？ / 我的笔记里三步法是什么？ / 15度穿什么？")
    print("-" * 55)

    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    while True:
        user_input = input("\n你: ").strip()
        if user_input in ("exit", "quit", "退出"):
            print("👋 再见！")
            break

        messages.append(HumanMessage(content=user_input))

        # 手写版是 for _ in range(MAX_TOOL_ROUNDS)，
        # 这里用 recursion_limit 限制最多走多少步，防止无限循环
        result = graph.invoke({"messages": messages}, {"recursion_limit": 10})

        messages = result["messages"]        # 取回完整历史（含 AI 消息、工具结果）
        print(f"\n🤖 Agent: {messages[-1].content}")


if __name__ == "__main__":
    main()
