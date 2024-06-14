from core.llm.ollama_llm import Ollama_LLM
from core.llm.openai_llm import OpenAI_LLM
from core.llm.dashscope_llm import DashScope_LLM

def create_model(platform, model_name, url=None, key=None):
    """_summary_
    modal factory, create the model based on the platform in the configuration
    support ollama, openai, dashscope
    Args:
        platform (str): platform chosen
        model_name (_type_): model name
        url (_type_, optional): endpoint
        key (_type_, optional): api key

    Raises:
        ValueError: _description_

    Returns:
        _type_: _description_
    """
    if platform == 'ollama':
        return Ollama_LLM(model_name)
    elif platform == 'openai':
        return OpenAI_LLM(model_name, base_url=url, api_key=key)
    elif platform == 'dashscope':
        return DashScope_LLM(model_name, api_key=key)
    else:
        raise ValueError("Unsupported platform")