import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.llm.ollama_llm import Ollama_LLM

llm = Ollama_LLM(model_name="llava:13b")

print(llm.invoke("describe this image", "app/tmp/current_image.png"))