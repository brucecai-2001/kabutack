import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi import WebSocket

from core.llm.model_factory import create_model
from core.prompt.chat_prompt import (CHAT, GREET)

from utils.config import agent_config
from utils.log import logger
from utils.func import *

class ChatAgent:
    """
    responsible for small talks, support text and viusal modality
    """ 

    def __init__(self) -> None:
        self.history_conversations = []
        self.full_response = ""

        self.chat_llm = create_model(agent_config.get('chat_llm.platform'), 
                agent_config.get('chat_llm.model_name'),
                agent_config.get('chat_llm.end_point'),
                agent_config.get('chat_llm.api_key'))
        
        self.multimodal_llm = create_model(agent_config.get('multimodal_llm.platform'), 
                agent_config.get('multimodal_llm.model_name'),
                agent_config.get('multimodal_llm.end_point'),
                agent_config.get('multimodal_llm.api_key'))
        return
    
    def shutdown(self):
        print("chat agent exit")
        
    
    # 主动向用户打招呼
    def greet(self):
        """
        greet to user
        """

        # build greeting prompt
        time_now = get_time()
        greeting_prompt = GREET.format(time=time_now)

        try:
            greeting_response = self.chat_llm.invoke(greeting_prompt)
            logger.log("Assistant", greeting_response)
            self.chat_prompt += ( "Assistant greets to User: " + greeting_response + "\n" )
            return greeting_response
        
        except Exception as e:
            logger.log("Error ", str(e))
            raise RuntimeError("chat agent greet failed")
    
    
    # 流式聊天
    async def chat(self, 
                   websocket: WebSocket,
                   memory: str, 
                   query: str, 
                   image=None):
        """
        chat with user

        Args:
            memory (str): the memory retrievaled from a vector database
            query (str): user current query
            image (str, optional): image path for visual modality

        Returns:
            None: Data is added to the shared response buffer.
        """
        self.full_response = ""
        self.history_conversations.append("User says: " + query)

        # build chat prompt
        time_now = get_time()
        history_conversations = "\n".join(self.history_conversations)
        self.chat_prompt = CHAT.format(time=time_now, conversations=history_conversations)
        
        if memory == "none":
            pass
        else:
            self.chat_prompt += ("Here are some history reference for this query: " + memory + "\n")

        # call large model
        try:
            if image is None:
                self.full_response = await self.chat_llm.invoke_stream(
                                                websocket=websocket,
                                                prompt=self.chat_prompt
                                            )
                
            else:
                self.full_response = await self.multimodal_llm.invoke_stream(
                                                  websocket=websocket,
                                                  prompt=self.chat_prompt, 
                                                  image_path=image
                                                )
                
        except Exception as e:
            logger.log("Error ", str(e))
            raise RuntimeError("chat agent chat failed")

        self.history_conversations.append("Assistant responses to User: " + self.full_response)
        logger.log("Assistant", self.full_response)
    

    def get_history_conversations(self):
        """
        Returns:
            (list): the history conversions with user in a chat session
        """
        return self.history_conversations

