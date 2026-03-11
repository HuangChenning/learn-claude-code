#!/usr/bin/env python3
# Harness: the loop -- the model's first connection to the real world.
# cspell:ignore dotenv
"""
s01_agent_loop.py - The Agent Loop

The entire secret of an AI coding agent in one pattern:

    while stop_reason == "tool_use":
        response = LLM(messages, tools)
        execute tools
        append results

    +----------+      +-------+      +---------+
    |   User   | ---> |  LLM  | ---> |  Tool   |
    |  prompt  |      |       |      | execute |
    +----------+      +---+---+      +----+----+
                          ^               |
                          |   tool_result |
                          +---------------+
                          (loop continues)

This is the core loop: feed tool results back to the model
until the model decides to stop. Production agents layer
policy, hooks, and lifecycle controls on top.
"""

import os
import subprocess

try:
    import readline
    # #143 UTF-8 backspace fix for macOS libedit
    readline.parse_and_bind('set bind-tty-special-chars off')
    readline.parse_and_bind('set input-meta on')
    readline.parse_and_bind('set output-meta on')
    readline.parse_and_bind('set convert-meta off')
    readline.parse_and_bind('set enable-meta-keybindings on')
except ImportError:
    pass

from anthropic import Anthropic
from anthropic.types import ToolParam
from dotenv import load_dotenv

load_dotenv(override=True)

if os.getenv("ANTHROPIC_BASE_URL"):
    # print(os.getenv("ANTHROPIC_AUTH_TOKEN"))
    os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)
    print(os.getenv("ANTHROPIC_BASE_URL"))
    print(os.getenv("ANTHROPIC_AUTH_TOKEN"))

client = Anthropic(base_url=os.getenv("ANTHROPIC_BASE_URL"))
MODEL = os.environ["MODEL_ID"]

SYSTEM = f"You are a coding agent at {os.getcwd()}. Use bash to solve tasks. Act, don't explain."

# ### 它是如何工作的？（Agent 流程）
# 1. 用户输入 ：你对 AI 说：“请列出当前目录下的文件”。
# 2. 模型思考 ：AI 接收到你的请求，同时看到了这个 TOOLS 定义。
# 它会想：“用户的需求是列出文件，我看了一下我的工具箱，发现 bash 工具的描述是‘运行 Shell 命令’，这正好能解决用户的问题。”
# 3. 模型输出 ：AI 不会 直接执行代码（它只是个在大脑里运行的文本生成器），而是返回一个特殊的结构化数据（Tool Use Request），类似于：
# {
#   "type": "tool_use",
#   "name": "bash",
#   "input": {
#     "command": "ls -la"
#   }
# }
# 
# 4. 代码执行 ：你的 Python 脚本（ agent_loop 函数）会捕获到这个请求，提取出 ls -la ，然后调用真正的 subprocess.run 去执行它，最后把执行结果返还给 AI。
# 5. 结果返回 ：AI 会收到执行结果（例如：当前目录下的文件列表），并继续思考。
# 6. 循环继续 ：如果用户还有其他需求（例如：“请删除所有 .py 文件”），AI 会重复这个流程。
# 7. 模型停止 ：当用户不再需要 AI 帮助时，AI 会返回一个普通的文本回复（例如：“好的，我会尽力帮助你”），而不是继续调用工具。
#
# 总结 ：这段代码是连接 AI 大脑 和 计算机操作系统 的桥梁。没有它，AI 只能陪你聊天；有了它，AI 就能操作电脑。
#


TOOLS: list[ToolParam] = [
    {  # 定义工具列表
        "name": "bash",  # 工具名称：模型在调用时会返回这个名字
        "description": "Run a shell command.",  # 工具描述：非常重要！模型通过理解这句话来决定“何时”使用这个工具
        "input_schema": {  #  参数格式（JSON Schema 标准）
            "type": "object",  # 规定参数是一个对象
            "properties": {"command": {"type": "string"}},  # 规定参数名是 command，类型是字符串
            "required": ["command"],  # 规定 command 参数是必填的
        },
    }
]

# run_bash 函数：执行 bash 命令并返回输出
def run_bash(command: str) -> str:
    dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
    if any(d in command for d in dangerous):
        return "Error: Dangerous command blocked"
    try:
        r = subprocess.run(command, shell=True, cwd=os.getcwd(),
                           capture_output=True, text=True, timeout=120)
        out = (r.stdout + r.stderr).strip()
        return out[:50000] if out else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Timeout (120s)"


# -- The core pattern: a while loop that calls tools until the model stops --
# agent_loop 函数：主循环，处理用户输入和模型响应
def agent_loop(messages: list):
    while True:
        # Call the model，tools 是一个列表，包含了所有可用的工具，比如这里只有 bash 工具
        response = client.messages.create(
            model=MODEL, system=SYSTEM, messages=messages,
            tools=TOOLS, max_tokens=8000,
        ) 
        # Append assistant turn
        messages.append({"role": "assistant", "content": response.content})
        # If the model didn't call a tool, we're done
        if response.stop_reason != "tool_use":
            return
        # Execute each tool call, collect results
        results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"\033[33m$ {block.input['command']}\033[0m")
                output = run_bash(str(block.input["command"]))
                print(output[:200])
                results.append({"type": "tool_result", "tool_use_id": block.id,
                                "content": output})
        messages.append({"role": "user", "content": results})


if __name__ == "__main__":
    history = []  # 初始化消息历史记录列表
    while True:
        try:
            query = input(
                "\033[36ms01 >> \033[0m"
            )  # 提示用户输入 ，\033[ : 这是转义序列的开始标记（Escape字符），36m : 这是设置文本颜色的转义序列，0m : 这是重置文本颜色的转义序列
        except (EOFError, KeyboardInterrupt):
            break
        # Exit on empty input, "q", or "exit"
        if query.strip().lower() in ("q", "exit", ""):
            break
        history.append({"role": "user", "content": query})
        agent_loop(history)  # 调用 agent_loop 函数处理用户输入和模型响应
        response_content = history[-1]["content"]  # 获取模型最后一次响应的内容
        if isinstance(response_content, list):  # 如果模型响应是一个列表（包含多个内容块）
            for block in response_content:
                if hasattr(block, "text"):
                    print(block.text)
        print()
