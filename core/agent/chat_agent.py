import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.llm.model_factory import create_model
from core.prompt.prompts import build_Prompt_chat, build_Prompt_greet

from utils.config import agent_config
from utils.log import logger


class ChatAgent:
    """
    responsible for small talks, support text and viusal modality
    """ 
    # core agent components
    history_conversations = []

    def __init__(self) -> None:    
        self.chat_llm = create_model(agent_config.get('chat_llm.platform'), 
                agent_config.get('chat_llm.model_name'),
                agent_config.get('chat_llm.end_point'),
                agent_config.get('chat_llm.api_key'))
        
        self.multimodal_llm = create_model(agent_config.get('multimodal_llm.platform'), 
                agent_config.get('multimodal_llm.model_name'),
                agent_config.get('multimodal_llm.end_point'),
                agent_config.get('multimodal_llm.api_key'))
    
        self.chat_prompt = build_Prompt_chat()
        
        return
    
    def shutdown(self):
        print("chat agent exit")
        
    

    # 主动向用户打招呼
    def greet(self):
        """
        greet to user
        """
        greeting_prompt = build_Prompt_greet()

        try:
            greeting_response = self.chat_llm.invoke(greeting_prompt)
            logger.log("Assistant", greeting_response)
            self.chat_prompt += ( "Assistant greets to User: " + greeting_response + "\n" )
            return greeting_response
        
        except Exception as e:
            logger.log("Error ", str(e))
            raise RuntimeError("chat agent greet failed")
    
    # 自然语言聊天
    def chat(self, memory: str, query: str, image = None) -> str:
        """
        chat with user, support text and viusal modality

        Args:
            memory (str): the memory retrievaled from a vector database
            query (str): user current query
            image (str, optional): image path for visual modality

        Returns:
            (str): the response to the user
        """
        self.history_conversations.append(query)

        # build chat prompt
        if memory == "none":
            self.chat_prompt += ( "User says: " + query + "\n" )
        else:
            self.chat_prompt += ( "User says: " + query + "\n" )
            self.chat_prompt += ( "Here are some history reference for this query. " + memory +"\n" )

        # call the model
        # LLM
        if image == None:
            try:
                chat_response = self.chat_llm.invoke(prompt=self.chat_prompt)
                logger.log("Assistant", chat_response)

            except Exception as e:
                logger.log("Error ", str(e))
                raise RuntimeError("chat agent chat failed")
            
        # VLM
        else:
            try:
                chat_response = self.multimodal_llm.invoke(prompt=self.chat_prompt, image_path=image)
                logger.log("Assistant", chat_response)
            except Exception as e:
                logger.log("Error ", str(e))
                raise RuntimeError("chat agent chat failed")

        self.chat_prompt +=  ("Assistant responses to User: " + chat_response + "\n")
        return chat_response
    
    
    def get_history_conversations(self):
        """
        Returns:
            (list): the history conversions with user in a chat session
        """
        return self.history_conversations
        
    

