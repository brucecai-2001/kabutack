import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.tool.tool_utils import *
from core.agent.task_agent import CodeAgent

code_agent = CodeAgent()
code_agent.task("邮件发我上海明天的天气")
