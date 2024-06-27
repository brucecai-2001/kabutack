import re
import json
from typing import Dict, Any

# TODO: The output from the LLM is unstable, consider all edges ...
class Parser:
    """
    parse the llm response
    """
    def __init__(self) -> None:
        pass

        
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
    


    def extract_json(self, json_str: str) -> Dict[str, Any]:
        try:
            json_dict = json.loads(json_str)
        except json.JSONDecodeError:
            input_json_str = json_str
            if "```json" in json_str:
                json_str = json_str[json_str.find("```json") + len("```json") :]
                json_str = json_str[: json_str.find("```")]
            elif "```" in json_str:
                json_str = json_str[json_str.find("```") + len("```") :]
                # get the last ``` not one from an intermediate string
                json_str = json_str[: json_str.find("}```")]
            try:
                json_dict = json.loads(json_str)
            except json.JSONDecodeError as e:
                error_msg = f"Could not extract JSON from the given str: {json_str}.\nFunction input:\n{input_json_str}"
                raise ValueError(error_msg) from e
        return json_dict  # type: ignore
    
    def extract_code(self, code: str) -> str:
        if "\n```python" in code:
            start = "\n```python"
        elif "```python" in code:
            start = "```python"
        else:
            return code

        code = code[code.find(start) + len(start) :]
        code = code[: code.find("```")]
        if code.startswith("python\n"):
            code = code[len("python\n") :]
        return code

    
    
parser = Parser()
    