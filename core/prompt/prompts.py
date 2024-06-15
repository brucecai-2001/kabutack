import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.tool.tool_utils import getToolsPrompt
from utils.func import get_time, readFile


def build_Prompt_greet():
    """
    build greeting prompt
    Returns:
        greeting_prompt(str): built prompt
    """
    greeting_prompt = readFile('greeting')
    time_of_day = get_time()
    greeting_prompt = greeting_prompt.replace('{time}', time_of_day)
    return greeting_prompt

def build_Prompt_chat():
    """
    build chat prompt
    Returns:
        chat_prompt: built chat prompt
    """
    # get the current time
    chat_prompt = readFile('chat')
    time_of_day = get_time()
    chat_prompt = chat_prompt.replace('{time}', time_of_day)
    chat_prompt += '\n'
    return chat_prompt

def build_Prompt_task(task=None, memory=None):
    """
    build task prompt
    Returns:
        task_prompt: built task prompt
    """
    desc, names = getToolsPrompt()
    task_prompt = readFile('task')
    task_prompt = task_prompt.replace('{tools}', desc)
    task_prompt = task_prompt.replace('{tool_names}', names)
    task_prompt = task_prompt.replace('{task}', task)
    if memory is not None:
        task_prompt += f'''Related Context: {memory} \n'''
    return task_prompt

def build_Prompt_summary_conversations(conversations):
    """
    build summary prompt
    Returns:
        summary_conversation_prompt: built summary_conversation_prompt prompt
    """
    summary_conversation_prompt= readFile('summary_conversations')
    summary_conversation_prompt = summary_conversation_prompt.replace('{conversations}', conversations)
    return summary_conversation_prompt

    

