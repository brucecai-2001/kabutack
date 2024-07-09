import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.tool.tool_utils import *
from core.agent.task_agent import CodeAgent

code_agent = CodeAgent(debug=False)
# print(code_agent.task("搜索2020和2021年上海市的GDP保存到一个csv文件中，单位人民币，地址: /Users/caixinyu/Desktop"))
# print(code_agent.task("2023年日本人均GDP减去同期韩国人均GDP等于多少，以美元为单位，把结果发我邮箱"))