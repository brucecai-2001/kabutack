import dashscope
import random
from core.llm.base_llm import BaseLLM

class DashScope_LLM(BaseLLM):
    """
    Ali DashScope platform
    support multi modality
    Args:
        BaseLLM (_type_): _description_
    """
    def __init__(self, model_name, base_url=None, api_key=None):
        super().__init__(model_name)
        self.api_key = api_key
    
    def invoke(self, prompt, image_path=None, temp=0.5):
        """call the llm

        Args:
            prompt (str): prompt to the model
            image_path (str, optional): image path

        Returns:
            response(str): response from the llm
        """
        try:
            if image_path != None:
                messages = [
                {
                    "role": "user",
                    "content": [
                        {"image": image_path},
                        {"text": prompt}
                    ]
                }]
                vlm_response = dashscope.MultiModalConversation.call(model=self.model,
                                                                messages=messages,
                                                                api_key = self.api_key)
                
                return vlm_response['output']['choices'][0]['message']['content'][0].get('text')
            
            else:
                messages = [
                {'role': 'user', 'content': prompt}
                ]
                llm_response = dashscope.Generation.call(model=self.model,
                                        messages=messages,
                                        seed=random.randint(1, 10000),
                                        result_format='message',
                                        api_key=self.api_key)
                return  llm_response['output']['choices'][0]['message']['content']
                    
        except Exception as e:
            # catach error
            raise RuntimeError("Call LLM failed: " + str(e))
        

