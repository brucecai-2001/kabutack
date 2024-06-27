import os
import importlib
from typing import Callable

from core.tool.tools import *
from core.tool.tool_retrieve import ToolRetriever

from utils.func import check_and_save_to_csv

# retrieve tool and save tool document
__tool_retriever__ = ToolRetriever(topk=2)

# a dictionary collects the tools to call
__TOOLBOX__ = {}
# a dictionary collects the tool's document
__TOOLDOCS__ = {}
#  a list collects tools name only
__TOOLNAMES__ = []
#  a list collects tools' brief description
__TOOLDESC__ = []
# a list collects the tool's import
__TOOLIMPORTS__ = []


DefaultImport = ["import os", 
                 "import sys"]

# define a decorator to register a tool
def register_tool(func_name: str, # name of the function
                  func_desc: str, # a detailed description of the function
                  func_import: str,
                  func_args: str, 
                  func_return: str, 
                  func_example: str = None # one or two use case
                ):
    """
    a decorator to register tool
    Args:
        func_name (str): the name of the tool
    """
    def decorator(func):
        __TOOLBOX__[func_name] = func

        __TOOLNAMES__.append(func_name)
        
        __TOOLIMPORTS__.append(func_import)

        tool_description = "{name}: {description}\n Args: {args}"
        __TOOLDESC__.append(tool_description.format(name=func_name, description=func_desc, args=func_args))

        tool_doc = """Tool Name:{name}\n{description}\nParameters:\n{args}\nReturn:\n{returns}\nExample\n----------\n{example}"""
        tool_doc = tool_doc.format(name=func_name, description=func_desc, args=func_args, returns=func_return, example=func_example)
        __TOOLDOCS__[func_name] = tool_doc

        return func
    return decorator


def register_all_tools(tool_directory='core/tool/tools'):
    """
    register the tools to the _TOOLBOX
    Args:
        tool_directory (str, optional): _description_. Defaults to 'core/tool'.
    """
    # import every tool
    for filename in os.listdir(tool_directory):
        if filename.endswith('.py'):
            module_name = f'core.tool.tools.{filename[:-3]}'
            _ = importlib.import_module(module_name)

    doc_to_upload = []
    for name, doc in __TOOLDOCS__.items():
        # new tool to be saved to csv
        if check_and_save_to_csv(name, doc):
            doc_to_upload.append(doc)
    # upload to vector db
    __save_docs__(doc_to_upload)

def getTool(tool_name: str) -> Callable:
    return __TOOLBOX__[tool_name]


def getToolsName() -> str:
    return "\n".join(__TOOLNAMES__)

def getToolsDesc() -> str:
    return "\n".join(__TOOLDESC__)

def getDefaultImport() -> str:
    return "\n".join(DefaultImport)

def getToolImport() -> str:
    return "\n".join(__TOOLIMPORTS__)

def retrieve_tool(subplan):
    tools = __tool_retriever__.retrieve_tool(subplan)
    return tools

def __save_docs__(doc: list):
    __tool_retriever__.save_docs(doc)




# ---------------------------------------------------
# ---------------------------------------------------
# register the tools
register_all_tools()