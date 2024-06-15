import asyncio
from fastapi import WebSocket
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
        
    def invoke(self, prompt: str, image_path=None) -> str:
        """
        non stream llm calling
        Args:
            prompt (_type_): prompt to the llm
            image_path (_type_, optional): image path
        """
        try:
            if image_path != None:
                raise RuntimeError("MultiModal request for OpenAI Client is Not implemented yet")

            else:
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system", 
                            "content": prompt
                        }
                    ],
                    temperature=0.5,  # set temp, it will determine the response stability
                    stream=False
                )
                return completion.choices[0].message.content
        
        except Exception as e:
            # catach error
            raise RuntimeError("Call LLM failed: " + str(e))
        
        
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
        try:
            if image_path != None:
                raise RuntimeError("MultiModal request for OpenAI SDK is Not implemented yet")

            else:
                stream_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system", 
                            "content": prompt
                        }
                    ],
                    temperature=0.5,  # set temp, it will determine the response stability
                    stream=True
                )
                
                full_response = "" # the complete response
                full_sentence = "" # sentence to be streamed to client
                
                for _, chunk in enumerate(stream_response): # Receive chunk from stream
                    chunk_message = chunk.choices[0].delta
                    if not chunk_message.content:
                        continue

                    full_response += chunk_message.content
                    full_sentence += chunk_message.content

                    if '。' in chunk_message.content:
                        await websocket.send_text(full_sentence)
                        full_sentence = ""

                        # prevent messages from accumulating in the buffer, 
                        # otherwise the client may read all messages at once, causing a huge lag.
                        await asyncio.sleep(0.1)

                # Send the remaining sentence if any
                await websocket.send_text(full_sentence)
                # Notify client that the streaming is over
                await websocket.send_text("FINISHED")

            return full_response
        
        except Exception as e:
            # catach error
            raise RuntimeError("Call LLM failed: " + str(e))
    