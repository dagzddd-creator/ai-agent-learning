# -*- coding: utf-8 -*-
"""Reflection（反思）范式演示：生成 → 批评 → 改进

这是 Agent 三大经典范式之一：
- ReAct：走一步看一步（你的 main.py 就是这种）
- Plan-and-Execute：先列完整计划，再逐步执行
- Reflection：先做一版 → 自我批评 → 再改一版  ← 本文件演示这个

核心思想：模型一次生成往往有瑕疵，让它「以审查者的身份」挑自己的毛病，
再基于批评重做，产出质量会明显提升。

运行（必须在 agent-basics 目录下，因为要读同目录的 .env）：
    cd D:\\study-practice\\agent-basics
    python reflection_demo.py
"""
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()   # 读取同目录的 .env（LLM_API_KEY / LLM_BASE_URL / LLM_MODEL）
client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL", "https://tokenrhythm.studio/v1"),
)
MODEL = os.getenv("LLM_MODEL", "deepseek-v4-flash-0731")


def ask(prompt: str) -> str:
    """把一段话发给模型，拿回它的文本回答（你会用的样板代码）。"""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


def main():
    task = "写一个 Python 函数，判断一个字符串是不是回文（忽略大小写和非字母数字字符）"

    # ---------- 第 1 步：生成初稿（Generator）----------
    # draft = ask(f"请{task}。只给代码，不要解释。")
    draft = '''```python
    def is_palindrome(s: str) -> bool:
        clean = ''.join(c.lower() for c in s if c.isalnum())
        for i in range(len(clean) // 2):
            if clean[i] != clean[-i]:
                return False
        return True
    ```'''
    print("=" * 25, "① 初稿", "=" * 25)
    print(draft)

    # ---------- 第 2 步：自我批评（Critic）----------
    # 关键点：要求「指出具体缺陷」，越具体，第 3 步改得越好
    critique = ask(
        "你是一位严格的代码审查员。请审查下面这段代码，逐条指出它的具体缺陷"
        "（缺陷是指导致程序结果出错的那种例如：边界情况没处理、缺少异常处理等，而不是性能问题、命名不清等这种）。"
        '''必须用至少 3 个具体输入（一个真回文如 racecar、一个非回文如 abab、一个边界如空串 ""）逐行演算代码的执行过程，写出每步变量的取值
严禁只凭代码外观判断——没演算过就不能说"没问题"
演算出的结果与预期不符 = 缺陷'''
        "不要客套话，直接列问题，若无问题，就说未发现影响正确性的问题。\n\n"
        f"代码：\n{draft}"
    )
    print("\n" + "=" * 25, "② 批评", "=" * 25)
    print(critique)

    # ---------- 第 3 步：根据批评改进（Refiner）----------
    final = ask(
        "请根据下面的【批评意见】改进这段代码，输出改进后的完整代码。（先逐条判断批评是否合理，只采纳影响正确性的，代码简洁，能不改就不改）\n\n"
        f"【原代码】\n{draft}\n\n"
        f"【批评意见】\n{critique}\n\n"
        "【改进后的代码】"
    )
    print("\n" + "=" * 25, "③ 改进后", "=" * 25)
    print(final)


if __name__ == "__main__":
    main()
