import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
import json
import time
from fastapi import WebSocket

from core.llm.model_factory import create_model
from core.tool.tool_utils import getTool, getToolsDesc, getDefaultLibs, getToolImport, retrieve_tool
from core.prompt.react_prompt import REACT
from core.prompt.code_prompt import PLAN, CODE, FIX_BUG

from utils.config import agent_config
from utils.parse import parser
from utils.log import  logger
from utils.code_interpreter import LocalCodeInterpreter



class ReActAgent:
    """
    This agent is responsible for the user's task query.
    It follows ReAct approach: 
    Projet page with code: https://react-lm.github.io/. 
    arXiv:2210.03629v3

    * Support websocket stream task progress response
    """
    def __init__(self) -> None:
        """
        init the task agent, text and visual llm 
        and create a thread accepting the task 
        """
        # core agent components
        self.task_processing = False
        self.task_content = None
        self.image = None

        self.text_llm = create_model(agent_config.get('task_llm.platform'), 
                agent_config.get('task_llm.model_name'),
                agent_config.get('task_llm.end_point'),
                agent_config.get('task_llm.api_key'))
        
        self.multimodal_llm = create_model(agent_config.get('multimodal_llm.platform'), 
                agent_config.get('multimodal_llm.model_name'),
                agent_config.get('multimodal_llm.end_point'),
                agent_config.get('multimodal_llm.api_key'))


    def shutdown(self):
        print("task agent exit")
            

    async def task(self, websocket: WebSocket, task_content: str, image=None):
        """
        handle the task, ReAct implementation
        Args:
            task_content (str, optional): the task query
            image (str, optional): image path
        """
        self.task_processing = True
        self.task_content = task_content
        if image != None:
            self.image = image
        
        # build task prompt
        tools_desc = getToolsDesc()
        self.task_prompt = REACT.format(task=task_content, tools=tools_desc)

        # perform the task, each 3 steps, monitor the progress
        for i in range(0, 8):
            # generate a thought and an action
            try:
                # parse llm Response
                thought_and_action = self.text_llm.invoke(self.task_prompt)
                thought_and_action_JSON = parser.extract_json(thought_and_action)
                finished = thought_and_action_JSON['finished']
                thought = thought_and_action_JSON['thought']
                action_name = thought_and_action_JSON['action']
                action_input = thought_and_action_JSON['action_input']

                logger.log("Assistant", thought_and_action)
            except Exception as e:
                logger.log("Error ", str(e))
                progress = build_task_response_JSON(status="FINISHED", 
                                                        success=False,
                                                        return_type="text", 
                                                        result=str(e))
                await websocket.send_text(progress)
                await asyncio.sleep(0.1)
                raise RuntimeError("task agent inference or parse JSON failed" + str(e))

            # If agent has the answer, finish the task
            if finished == True:
                answer = thought
                progress = build_task_response_JSON(status="FINISHED", 
                                                        success=True,
                                                        return_type="text", 
                                                        result=answer)
                await websocket.send_text(progress)
                await asyncio.sleep(0.1)
                await websocket.send_text("FINISHED")
                await asyncio.sleep(0.1)
                self.task_processing = False
                return
            
            #Action and get onservation
            try:
                observation = self.action(tool_name=action_name, parameters=action_input)
                progress = build_task_response_JSON(status="ACTING", 
                                                        success=True,
                                                        return_type="text", 
                                                        result=observation)
                await websocket.send_text(progress)
                await asyncio.sleep(0.1)

            except Exception as e:
                progress = build_task_response_JSON(status="FINISHED", 
                                                        success=False,
                                                        return_type="text", 
                                                        result="action faled" + str(e))
                raise RuntimeError("task agent calls tools failed" + str(e))

            #tell llm to continue based on previous t&o
            self.task_prompt += f'''Thought : {thought} \n '''
            self.task_prompt += f'''Observation : {observation} \n'''

    def action(self, tool_name: str, parameters: dict) -> str:
        # Get tool from a tool_name:tool dictionary 
        tool = getTool(tool_name)
        # get response from tool
        observation = tool(react_params=parameters)
        return str(observation)





#TODO: DEBUG
class CodeAgent:
    """
    fork from andrew NG's vision agent
    """
    def __init__(self, debug = False) -> None:
        self.plan_llm = create_model(agent_config.get('task_llm.platform'), 
                agent_config.get('task_llm.model_name'),
                agent_config.get('task_llm.end_point'),
                agent_config.get('task_llm.api_key'))
        
        self.code_llm = create_model(agent_config.get('code_llm.platform'), 
                agent_config.get('code_llm.model_name'),
                agent_config.get('code_llm.end_point'),
                agent_config.get('code_llm.api_key'))
        
        # If debug is needed
        self.need_debug = debug
        if self.need_debug:
            self.debug_llm = create_model(agent_config.get('code_llm.platform'), 
                    agent_config.get('code_llm.model_name'),
                    agent_config.get('code_llm.end_point'),
                    agent_config.get('code_llm.api_key'))
        
        # jupyter kernel
        self.code_interpreter = LocalCodeInterpreter()

        self.max_retries = 3


    def shutdown(self):
        if self.code_interpreter is not None:
            self.code_interpreter.close()
        print("code agent closed")
    

    def task(self, task_content: str):
        """
        PLAN -> RETRIEVE TOOLS -> WRITE CODE -> TEST CODE -> RETURN OR DEBUG
        Args:
            task_content (str): User query
        """
        code = None

        try:
            # plan the task, generate related tools document
            tool_docs = self._plan(task_content)

            # genrate code
            code = self._write_code(task_content=task_content, tool_docs=tool_docs)
            
        except Exception as e:
            raise RuntimeError(e)

        # execute code in code interpreter
        retry = 0
        exe_success = False
        return_type = "text"
        exe_result = ""
        while not exe_success and retry < self.max_retries:
            retry += 1
            # execute
            result = self._run_code(code)
            if result.success:
                exe_result = result.text(include_logs=True)
                exe_success = True
            else:
                error = result.logs.stderr
                if self.need_debug == False:
                    break

                #reflect and debug
                debugged_code = self._debug(code=code, error=error)
                code = debugged_code


        # close interpreter and return
        self.code_interpreter.close()
        return build_task_response_JSON(status="FINISHED", success=exe_success, return_type=return_type, result=exe_result)


    def _plan(self, task_content) -> str:
        """
        Generate a list of subplans baseed on the given task and tool descriptions(tool name + tool's function)
        and search the related tools for each subplan.
        """
        # build plan prompt
        tools_desc = getToolsDesc()
        plan_prompt = PLAN.format(user_request=task_content, tools_desc=tools_desc)

        # call plan llm to get the subplans
        plan_response = self.plan_llm.invoke(prompt=plan_prompt)
        plans = parser.extract_json(plan_response)["plan"]
        
        # retrieve the related tools
        retrieved_tools_docs = []
        for subplan in plans:
            tool_docs = retrieve_tool(subplan['instructions'])
            for doc in tool_docs:
                retrieved_tools_docs.append(doc)
        
        # filter and return
        tool_docs = set(retrieved_tools_docs)
        return "\n\n".join(tool_docs)
        
    
    def _write_code(self, task_content: str, tool_docs: str) -> str:
        """
        Write the code

        Args:
            task_content (str): the user request
            tool_docs (str): the documents of related tools

        Returns:
            code (str): generated code
        """
        default_libs = getDefaultLibs()
        code_prompt = CODE.format(user_request=task_content, libs=default_libs, docs=tool_docs)
        code = self.code_llm.invoke(prompt=code_prompt,temp=0.0)
        code = parser.extract_code(code)
        return code
    

    def _run_code(self, code: str):
        """
        Run the code in code interpreter

        Args:
            code (str): generated code
        """
        tools_import = getToolImport()
        print(f"{tools_import}\n{code}\n")
        result = self.code_interpreter.exec_isolation(
            f"{tools_import}\n{code}\n"
        )
        return result


    def _debug(self, code, error):
        # build debug prompt
        debug_prompt = FIX_BUG.format(code=code, error=error)

        # debug code
        debug_response = self.code_llm.invoke(prompt=debug_prompt,temp=0.0)
        debugged_code = parser.extract_code(debug_response)
        return debugged_code

    

# Both ReAct and Code use this return format
def build_task_response_JSON(status: str, 
                                 success: bool, 
                                 return_type: str, 
                                 result: str) -> str:
    """
    construct a task response for ReAct and Code agent.

    Args:
        status (str): the progress of the task
        success (bool): if the operation success or not
        return_type (str): the type of the task's response
        result (str): the logs and text output of the task.s

    Returns:
        str: JSON format response
    """

    response_dict = {
        "status": status,
        "success": success,
        "return_type": return_type,
        "result": result
    }
    response_str = json.dumps(response_dict)
    return response_str