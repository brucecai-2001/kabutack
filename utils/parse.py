import re
import json

# TODO: The output from the LLM is unstable, consider all edges ...
class Parser:
    """
    parse the llm response
    """
    def __init__(self) -> None:
        pass

    # def parse_chat_and_task_response(self, chat_response):
    #     json_match = re.search(r'\{[^}]+\}', chat_response)
    #     if json_match:
    #         # Extract the JSON substring
    #         json_str = json_match.group(0)
    #         # Parse the JSON string
    #         parsed_json = json.loads(json_str)
            
    #         # Access the parsed data
    #         task_intend = parsed_json.get("task_intend")
    #         chat_response = parsed_json.get("chat_response")
    #         return task_intend, chat_response

    #     else:
    #         print("No JSON found in the text.")
    #         return None, None
        
    def parse_task_response(self, thought_and_action):

        # 定义Thought正则表达式模式
        thought_pattern = re.compile(r'Thought:(.*?)\n', re.DOTALL)
        # 在字符串中查找第一个匹配的Thought和Action
        thought_match = thought_pattern.search(thought_and_action)
        # 提取匹配的内容
        if thought_match:
            thought = thought_match.group(1)
        else:
            thought = ""

        # 定义正则表达式来匹配Action:后面的内容
        action_regex = re.compile(r'Action:\s*(\{.*?\})', re.DOTALL)
        # 使用正则表达式找到匹配的部分
        match = action_regex.search(thought_and_action)
        # 如果找到匹配的部分，使用json.loads()加载为JSON对象
        if match:
            action_json_str = match.group(1)  # 获取匹配的括号内的内容
            try:
                action_json = json.loads(action_json_str)  # 将字符串加载为JSON对象
            except:
                action_json = json.loads(action_json_str + "}")  # 将字符串加载为JSON对象

        return thought, action_json.get('action'), action_json.get('action_input')
    
    
parser = Parser()
    