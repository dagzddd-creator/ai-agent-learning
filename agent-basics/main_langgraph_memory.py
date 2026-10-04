# -*- coding: utf-8 -*-
"""给 LangGraph 版 Agent 加"记忆"（Checkpointer）—— 填空题，你来补 5 处 TODO。

目标：关掉程序重新启动，Agent 还记得刚才聊过什么。

原理（先读一遍再动手）：
  没有 checkpointer：state 只在内存里，程序一关就没了
                     → 所以手写版每次都要自己把全部历史 messages 传进去
  有 checkpointer：  框架在每一步之后把 state 存进 SQLite 文件，用 thread_id 区分会话
                     → 你只需要传【新消息】，历史由框架自动恢复

运行（在 agent-basics 目录下）：
    python main_langgraph_memory.py

验收标准：
    1) 问一句"我叫小明"  → 输入 exit 退出程序
    2) 重新运行，问"我叫什么？" → 它应该答出"小明"
"""
import json
import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph

# ==================================================================
# TODO 1（我来提示，你来写这一行）
#   导入 SQLite 版记忆存储：
#     模块路径： langgraph.checkpoint.sqlite
#     类名：     SqliteSaver
#   写成 import 语句 ↓（删掉 pass，写上你的导入）
# ==================================================================
from langgraph.checkpoint.sqlite import SqliteSaver


from tools import TOOLS, TOOL_FUNCTIONS

load_dotenv()

# ---------- 模型（和之前一样）----------
llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL", "deepseek-v4-flash-0731"),
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL", "https://tokenrhythm.studio/v1"),
    temperature=0,
).bind_tools(TOOLS)

SYSTEM_PROMPT = """你是一个乐于助人的助手。
- 天气/汇率/时间等实时数据 → 用 get_real_weather / get_exchange_rate / get_current_time
- 涉及个人学习笔记、Agent开发、RAG等知识 → 用 rag_query
- 简单常识问题 → 直接回答，不要调用工具
不要凭空编造数据；不确定时调用工具获取。"""


# ---------- 两个节点 + 条件边（和之前完全一样，不用改）----------
def agent_node(state: MessagesState):
    return {"messages": [llm.invoke(state["messages"])]}


def tools_node(state: MessagesState):
    last = state["messages"][-1]
    outputs = []
    for tc in last.tool_calls:
        print(f"  🔧 调用工具: {tc['name']}({json.dumps(tc['args'], ensure_ascii=False)})")
        result = TOOL_FUNCTIONS[tc["name"]](**tc["args"])
        outputs.append(ToolMessage(
            content=json.dumps(result, ensure_ascii=False),
            tool_call_id=tc["id"],
        ))
    return {"messages": outputs}


def route(state: MessagesState):
    last = state["messages"][-1]
    tc = getattr(last,  "tool_calls" , None)
    return "tools" if tc else END


# ---------- 组装图（和之前一样，不用改）----------
builder = StateGraph(MessagesState)
builder.add_node("agent", agent_node)
builder.add_node("tools", tools_node)
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", route)
builder.add_edge("tools", "agent")


# 注意：main 现在多了一个参数 graph（因为 graph 要在下面的 with 里才创建）
def main(graph):
    print("🤖 带记忆的 Agent 已启动！（输入 exit 退出，重开后它还认得你）")
    print("-" * 55)

    # ==============================================================
    # TODO 2：会话配置
    #   需要两样东西：
    #     thread_id        —— 会话编号（字符串，比如 "user-1"）
    #                         同一个编号 = 同一段对话；换编号就是新会话
    #     recursion_limit  —— 10（和之前一样，限制最多走几步）
    #   你来写这一行（把 ??? 换成内容）：
    # ==============================================================
    config = {
        "configurable": {"thread_id": "user-1"},     # ← 你起个会话名（字符串）
        "recursion_limit": 10,                  # ← 填数字 10
    }

    # 第一次运行时，把 system prompt 放进去；之后就不用再传了
    graph.update_state(config, {"messages": [SystemMessage(content=SYSTEM_PROMPT)]})

    while True:
        user_input = input("\n你: ").strip()
        if user_input in ("exit", "quit", "退出"):
            print("👋 再见！（记忆已存进 checkpoints.sqlite）")
            break

        # ==========================================================
        # TODO 3：★最关键★ 只传【这一条新消息】，不要再自己维护历史了
        #   第一个参数：一个 dict，里面装这一条 HumanMessage
        #   第二个参数：config（一定要传！不传记忆就不生效）
        #   你来写这一行：
        # ==========================================================
        result = graph.invoke({"messages": [HumanMessage(content=user_input)]}, config)

        print(f"\n🤖 Agent: {result['messages'][-1].content}")


# ==================================================================
# TODO 4：打开 SQLite 记忆文件并挂到图上
#   (a) 用 SqliteSaver.from_conn_string("checkpoints.sqlite") 打开记忆
#       写成：  with SqliteSaver.from_conn_string("checkpoints.sqlite") as memory:
#   (b) 编译图时把记忆挂上 —— compile() 的参数名叫 checkpointer
#       写成：  graph = builder.compile(checkpointer=memory)
#   (c) 最后调用 main(graph)
#
#   下面是答案的"形状"，把 ??? 补上：
# ==================================================================
if __name__ == "__main__":
    with SqliteSaver.from_conn_string("checkpoints.sqlite") as memory:
        graph = builder.compile(checkpointer=memory)
        main(graph)
