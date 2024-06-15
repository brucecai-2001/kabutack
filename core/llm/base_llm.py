from fastapi import WebSocket

class BaseLLM:
    """
    base large model class
    implement __init__ and invoke
    """
    def __init__(self,model_name) -> None:
        self.model = model_name
        
    def invoke(self, prompt:str, image_path=None):
        """_summary_
        call the llm or vlm
        Args:
            prompt (str): prompt
            image_path (_type_, optional): image path

        Raises:
            NotImplementedError: _description_
        """
        raise NotImplementedError("Subclasses should implement invoke")
    
    async def invoke_stream(self,
                            websocket: WebSocket,
                            prompt: str, 
                            image_path=None
                        ):
        """
        stream llm calling, eg. for kimi, first sentence response in 0.7s
        Args:
            prompt (_type_): prompt to the llm
            image_path (_type_, optional): image path
        """
        raise NotImplementedError("Subclasses should implement invoke_stream")
