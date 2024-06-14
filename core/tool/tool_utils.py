import os
import importlib
from core.tool import *
from utils.config import agent_config

# a dictionary collects the tools
# tool_name : tool
_TOOLBOX = {}

# 定义装饰器
def register_tool(func_name):
    """
    a decorator, label a tool
    Args:
        func_name (str): the name of the tool
    """
    def decorator(func):
        _TOOLBOX[func_name] = func
        return func
    return decorator

def register_all_tools(tool_directory='core/tool'):
    """
    register the tools to the _TOOLBOX
    Args:
        tool_directory (str, optional): _description_. Defaults to 'core/tool'.
    """
    for filename in os.listdir(tool_directory):
        if filename.endswith('.py') and filename != 'tool_manager.py':
            module_name = f'core.tool.{filename[:-3]}'
            _ = importlib.import_module(module_name)

def getToolsPrompt() -> str:
    """
    return the tools description, used in task prompt
    Returns:
        str: tools description
    """
    tools_desc = []
    tools_desc.append(f'''1. Finish_task: finish_task(answer) -  You must use it if observation arrive at the final answer, return the answer to user''')
    tools_names = []
    tools_num = 2
    # iterate the tools in the configuration file
    for tool_name, tool_info in agent_config.config.get('tools', {}).items():
        # check if the tool can be used
        if tool_info.get('use') == 'positive':
            # add the tool to the tools list
            tools_desc.append(f'''{tools_num}. {tool_name}: {tool_name}({tool_info.get('input')}) -  {tool_info.get('description')}''')
            tools_names.append(tool_name)
            tools_num += 1

    return '\n'.join(tools_desc), ','.join(tools_names)
    
def action(tool_name: str, parameters: dict) -> str:
    """
    call the tool based on the tool name chosen
    Args:
        tool_name (str): the name of the tool
        parameters (dict): parameters from the task agent

    Raises:
        ValueError: _description_

    Returns:
        observation: observation from the tool
    """
    if tool_name in _TOOLBOX:
        return _TOOLBOX[tool_name](parameters)
    else:
        raise ValueError(f"No tool found with name: {tool_name}")

# register the tools
register_all_tools()