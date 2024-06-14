import os
import sys
import threading
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.config import agent_config
from utils.parse import parser
from utils.log import  logger

from core.llm.model_factory import create_model
from core.tool.tool_utils import action
from core.prompt.prompts import build_Prompt_task

from queue import Queue
        

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

    tasks_queue = Queue(maxsize=5) # the task queue
    task_progress = Queue() # the task progress queue

    stop_event_task = threading.Event()

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

         # a thread keeps accepting the task query from the task queue
        self.t_task = threading.Thread(target=self._accept_task)
        self.t_task.start()

    def shutdown(self):
        self.stop_event_task.set()
        self.t_task.join()
        print("task agent exit")
        
    
    def append_task(self, type: str, memory=None, query=None, image=None):
        """
        append the task to the task queue
        Args:
            type (str): text query or text and visual query
            memory (str, optional): memory retrieval
            query (str, optional): current user query
            image (str, optional): the image path

        Returns:
            bool: if the task is appended successfully
        """
        print("Receive a task" + query + "\n")

        if memory != "none":
            query += ( " Here are some history reference for this query" + memory +"\n" )

        # append task to the queue
        if type == "task_text":
            try:
                self.tasks_queue.put([type, query])
                return True
            # If task queue is full
            except:
                return False
            
        elif type == "task_visual":
            try:
                self.tasks_queue.put([type, query, image])
                return True
            # If task queue is full
            except:
                return False
        
    
    def _accept_task(self):
        """
        a thread keeps accepting the task from the task queue util task agent shutdown
        """

        print("task agent ready to receive task")
        while not self.stop_event_task.is_set():
            if self.tasks_queue.empty() or self.task_processing:
                continue
            else:
                task = self.tasks_queue.get()
                type = task[0]
                # check the task type, if it has a image, then use a VLM to process the query, otherwise LLM
                if type == 'task_text':
                    self._inference(task_content = task[1])
                elif type == 'task_visual':
                    self._inference(task_content = task[1], image = task[2])
        print("task agent stops receive task")
            

    def _inference(self, task_content=None, image=None):
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
        self.task_prompt = build_Prompt_task(task=task_content)

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
                logger.log("Error ", str(e))
                raise RuntimeError("task agent parse task response failed" + str(e))

            # If agent has the answer, finish the task
            if action_tool == "Finish_task":
                answer = parameters['answer']
                self.task_progress.put(["Finish", answer])
                self.task_processing = False
                return
            
            #Action and get onservation
            try:
                observation = action(tool_name=action_tool, parameters=parameters)
                self.task_progress.put(["Observation", observation])
            except Exception as e:
                raise RuntimeError("task agent calls tools failed" + str(e))

            #tell llm to continue based on previous t&o
            self.task_prompt += f'''Thought : {thought} \n '''
            self.task_prompt += f'''Observation : {observation} \n'''
    
    
    def get_task_progress(self):
        """
        return the task progress and observation
        Returns:
            [str, str]]: task_progress, observation
        """
        if self.task_progress.empty():
            return "None", "None"
        progress = self.task_progress.get()
        return progress[0], progress[1]
    