import requests

from utils.config import agent_config
from core.tool.tool_utils import register_tool
from core.llm.model_factory import create_model

@register_tool('search_engine')
def search_engine(parameters: dict) -> str:
    """Search the internet for timeliness information related to the task"""

    search_query = parameters["query"]
    
    # Azure Bing Search API 
    # Construct a request
    mkt = 'en-US'
    params = { 'q': search_query, 'mkt': mkt }
    headers = { 'Ocp-Apim-Subscription-Key': agent_config.get("tools.search_engine.subscription_key") }
    # Call the API

    snippets = []
    try:
        # check https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/reference/response-objects#webpage 
        response = requests.get(agent_config.get("tools.search_engine.end_point"), headers=headers, params=params)
        response.raise_for_status()
        response_json = response.json()
        web_pages = response_json["webPages"]["value"]
        
        # extract snippet from the web pages
        for web_page in web_pages:
            snippets.append(web_page.get("snippet"))
        internet_snippets = '. '.join(snippets)

    except Exception as e:
        raise RuntimeError("bing search failed: " + str(e))
    
    # summary the internet_snippets
    try:
        _llm = create_model(agent_config.get('task_llm.platform'), 
                    agent_config.get('task_llm.model_name'),
                    agent_config.get('task_llm.end_point'),
                    agent_config.get('task_llm.api_key'))
        _summary_prompt = "I need to solve a task: {query} \
                            The following are some information I found through search engine: \
                            {snippets} \
                            Give the answer to the task in a sentence."
        _summary_prompt = _summary_prompt.replace('{snippets}', internet_snippets)
        _summary_prompt = _summary_prompt.replace('{query}', search_query)
        summary_llm_response = _llm.invoke(_summary_prompt)
        return summary_llm_response

    except Exception as e:
        raise RuntimeError("Call search engine failed: " + str(e))