import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
from fastapi import WebSocket

from utils.config import agent_config
from utils.parse import parser
from utils.log import  logger

from core.llm.model_factory import create_model
from core.tool.tool_utils import action
from core.prompt.prompts import build_Prompt_task
        

class ReActAgent:
    """
    The task agent responsible for the user task query.
    This one follows ReAct approach: 
    Projet page with code: https://react-lm.github.io/. 
    arXiv:2210.03629v3

    Returns:
        It returns nothing, the client will request the task progress
    """
    # core agent components
    task_prompt = None

    task_processing = False
    task_content = None
    image = None

    def __init__(self) -> None:
        """
        init the task agent, text and visual llm 
        and create a thread accepting the task 
        """
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
            

    async def task(self, websocket: WebSocket, memory=None, task_content=None, image=None):
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
        self.task_prompt = build_Prompt_task(task=task_content, memory=memory)

        # perform the task, each 3 steps, monitor the progress
        for i in range(0, 8):
            # generate a thought and an action
            try:
                thought_and_action = self.text_llm.invoke(self.task_prompt)
                logger.log("Assistant", thought_and_action)
            except Exception as e:
                logger.log("Error ", str(e))
                raise RuntimeError("task agent inference failed" + str(e))
            
            # parse the thought_and_action to get thought, action and action's parameters
            try:
                thought, action_tool, parameters = parser.parse_task_response(thought_and_action)
            except Exception as e:
                await websocket.send_text("FAILED")
                await asyncio.sleep(0.1)
                logger.log("Error ", str(e))
                raise RuntimeError("task agent parse task response failed" + str(e))

            # If agent has the answer, finish the task
            if action_tool == "Finish_task":
                answer = parameters['answer']
                await websocket.send_text(answer)
                await asyncio.sleep(0.1)
                await websocket.send_text("FINISHED")
                await asyncio.sleep(0.1)
                self.task_processing = False
                return
            
            #Action and get onservation
            try:
                observation = action(tool_name=action_tool, parameters=parameters)
                await websocket.send_text(observation)
                await asyncio.sleep(0.1)

            except Exception as e:
                raise RuntimeError("task agent calls tools failed" + str(e))

            #tell llm to continue based on previous t&o
            self.task_prompt += f'''Thought : {thought} \n '''
            self.task_prompt += f'''Observation : {observation} \n'''
    