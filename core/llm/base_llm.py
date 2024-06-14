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
        raise NotImplementedError("Subclasses should implement this method")
