import ollama
from core.llm.base_llm import BaseLLM

class Ollama_LLM(BaseLLM):
    """
    ollama platform, support local llm
    text modality only
    """
    def __init__(self, model_name):
        super().__init__(model_name)

    def invoke(self, prompt, image_path = None):
        """call the llm

        Args:
            prompt (str): prompt to the model
        Returns:
            response(str): response from the llm
        """
        try:
            if image_path != None:
                vlm_response = ollama.generate(model=self.model, prompt=prompt, images=[image_path])
                return vlm_response['response']
            
            else:
                llm_response = ollama.generate(model=self.model, prompt=prompt)
                return llm_response['response']
        
        except Exception as e:
            raise RuntimeError("Call LLM failed: " + str(e))