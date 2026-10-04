"""DeepSeek Function Calling 入门示例：一个能"动手干活"的最小 Agent。

核心流程（Agent 循环）：
    用户提问 → 发给大模型 → 模型说"我需要调用工具X(参数)"
    → 我们执行工具（真正干活的是我们的代码）
    → 把工具结果回传给模型 → 模型基于结果组织最终回答

运行前：
    1. pip install -r requirements.txt
    2. 复制 .env.example 为 .env，填入你的 DeepSeek API Key
    3. python main.py
"""
import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from tools import TOOLS, TOOL_FUNCTIONS

load_dotenv()  # 读取 .env 文件里的环境变量

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
)

# 模型名也从 .env 读取，换服务商时不用改代码
MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
MAX_TOOL_ROUNDS = 5  # 安全阀：防止模型陷入"无限调工具"的死循环


def run_tool(name: str, arguments: str) -> str:
    """执行模型要求调用的工具，把结果转成 JSON 字符串。

    arguments 是模型生成的 JSON 字符串，例如 '{"city": "北京"}'。
    """
    print(f"  🔧 调用工具: {name}({arguments})")
    func = TOOL_FUNCTIONS[name]              # 查表找到真正的 Python 函数
    args = json.loads(arguments or "{}")     # 解析模型给的参数
    result = func(**args)                    # 真正执行！
    return json.dumps(result, ensure_ascii=False)


def chat_loop():
    messages = [
        {
            "role": "system",
            "content": """你是一个乐于助人的助手。
- 天气/汇率/时间等实时数据 → 用 get_real_weather / get_exchange_rate / get_current_time
- 涉及个人学习笔记、Agent开发、RAG等知识 → 用 rag_query
- 简单常识问题 → 直接回答，不要调用工具
不要凭空编造数据；不确定时调用工具获取。""",
        }
    ]
    print("🤖 Agent 已启动！输入你的问题（输入 exit 退出）")
    print("   试试：北京天气怎么样？ / 现在几点了？ / 计算 (3.5+2)*4 等于多少")
    print("   再来个组合拳：北京天气怎么样？顺便告诉我现在几点")
    print("-" * 50)

    while True:
        user_input = input("\n你: ").strip()
        if user_input in ("exit", "quit", "退出"):
            print("👋 再见！")
            break
        messages.append({"role": "user", "content": user_input})

        # ---- Agent 循环：模型可能需要多轮工具调用才能回答 ----
        for _ in range(MAX_TOOL_ROUNDS):
            resp = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOLS,
            )
            msg = resp.choices[0].message

            if msg.tool_calls:
                # 1. 把模型的"调用意图"加入对话历史（这步不能省！）
                messages.append(msg)
                # 2. 逐个执行工具，把结果以 role="tool" 回传
                for tc in msg.tool_calls:
                    result = run_tool(tc.function.name, tc.function.arguments)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,   # 必须原样回传，模型靠它对上号
                        "content": result,
                    })
                # 3. 带着工具结果继续问模型（进入下一轮循环）
                continue

            # 模型没有要工具 → 给出最终回答
            print(f"\n🤖 Agent: {msg.content}")
            messages.append(msg)
            break
        else:
            # for 循环正常走完（没 break）说明工具轮次用尽了
            print("\n⚠️ 工具调用轮次过多，已停止（可调大 MAX_TOOL_ROUNDS）")


if __name__ == "__main__":
    chat_loop()
