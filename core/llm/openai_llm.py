from openai import OpenAI
from core.llm.base_llm import BaseLLM

class OpenAI_LLM(BaseLLM):
    """
    openai client, most llm service will support this.
    text modality only
    """
    def __init__(self, model_name, base_url=None, api_key=None):
        super().__init__(model_name)
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        
    def invoke(self, prompt, image_path=None):
        """
        Args:
            prompt (_type_): prompt to the llm
            image_path (_type_, optional): image path

        Returns:
            _type_: _description_
        """
        try:
            if image_path != None:
                raise RuntimeError("MultiModal request for OpenAI Client is Not implemented yet")

            else:
                # call llm through OpenAI SDK
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": prompt}],
                    temperature=0.5  # set temp, it will determine the response stability
                )
                return completion.choices[0].message.content
        
        except Exception as e:
            # catach error
            raise RuntimeError("Call LLM failed: " + str(e))