import requests

from core.tool.tool_utils import register_tool
from core.llm.model_factory import create_model
from utils.config import agent_config
from utils.parse import parser

from typing import Union

@register_tool(func_name='search_engine',
               func_desc="Search the internet for timeliness information related to the task. It will return a summary related to the query in a text string or a number depends on the downstream applications. **Instruction**: The search engine can not handle Vague query, for query like finding data across several years, places, things, you should search them one by one, split the query into many small queries and call this function multiple times.",
               func_import="from core.tool.tools.search_engine import search_engine",
               func_args="""search_query (str): the query sent to the search engine\nreturn_type (str): the expected return type, one of 'text' or 'number' """,
               func_return="summary (Union[str, float]): a inforamtion collects from the internet, could be a float number or a string of text",
               func_example="'Beijing is the capital of China' = search_engine(query='what is the capital of China?', return_type: 'text')\nor\n333.0 = search_engine(query='what is the height of tokyo tower in meters?', return_type: 'number')")
def search_engine(search_query: str = None, 
                  return_type: str = None, 
                  react_params: dict = None) -> Union[str, float]:
    """Search the internet for timeliness information related to the task"""

    # called by a react agent, so the return should be a text string
    if react_params is not None:
        search_query = react_params['search_query']
        return_type = "text"

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
    return summary_internet(search_query, return_type, internet_snippets)


def summary_internet(search_query: str, return_type: str, internet_snippets: str) -> Union[str, float]:
    """
    Summary the internet snippets collects from the search engine
    """
    try:
        _llm = create_model(agent_config.get('task_llm.platform'), 
                    agent_config.get('task_llm.model_name'),
                    agent_config.get('task_llm.end_point'),
                    agent_config.get('task_llm.api_key'))
        if return_type == "text":
            _summary_prompt = """I need to summary a  a task: {query} \
                                The following are some information I found through search engine: \
                                {snippets} \
                                Give the answer in a JSON.
                                ```json
                                    {
                                        "text": summary of the internet snippets in a sentence
                                    }
                                ```
                            """
        elif return_type == "number":
            _summary_prompt = """I need to extract a key number related to a task: {query} \
                                The following are some information I found through search engine: \
                                {snippets} \
                                Give the answer in a JSON.
                                ```json
                                    {
                                        "number": extract the key number required in the query.
                                    }
                                ```
                            """
            
        _summary_prompt = _summary_prompt.replace('{snippets}', internet_snippets)
        _summary_prompt = _summary_prompt.replace('{query}', search_query)

        summary_llm_response = _llm.invoke(_summary_prompt)
        summary_llm_response = parser.extract_json(summary_llm_response)

        if return_type == "text":
            return summary_llm_response['text']
        elif return_type == "number":
            return float(summary_llm_response['number'])

    except Exception as e:
        raise RuntimeError("Call search engine failed: " + str(e))