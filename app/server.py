import os
import sys
import time
import asyncio
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

from core.agent.chat_agent import ChatAgent
from core.agent.task_agent import ReActAgent
from core.agent.memory_agent import MemoAgent

# from utils.func import save_img

class Server:
    def __init__(self):
        # 初始化 FastAPI 应用
        self.app = FastAPI()
        
        # 初始化 Agents
        self._use_memory = False
        self._memory_agent = MemoAgent()
        self._chat_agent = ChatAgent()
        self._task_agent = ReActAgent()
        
        # 注册路由
        self._register_routes()
        
        print("System init")

    def run(self):
        uvicorn.run(self.app, host="0.0.0.0", port=8003)

    def _register_routes(self):
        @self.app.websocket("/chat")
        async def handle_chat(websocket: WebSocket):
            await websocket.accept()
            try:
                while True:
                    data = await websocket.receive_json()
                    query = data.get("query")
                    # out_language = data.get("output_lanaguage", "English")

                    # do memory retrieval
                    memory = "none"
                    if self._use_memory:
                        memory = self._memory_agent.retrieval(user_query=query)

                    try:
                        # call chat agent
                        await self._chat_agent.chat(websocket=websocket, memory=memory, query=query)

                    except Exception as e:
                        print(f"Error: {e}")
                        await websocket.send_text(f"Error: {str(e)}")

            except WebSocketDisconnect:
                print("Client disconnected")
        

        @self.app.websocket("/task")
        async def handle_task(websocket: WebSocket):
            await websocket.accept()
            try:
                while True:
                    data = await websocket.receive_json()
                    query = data.get("query")
                    # out_language = data.get("output_lanaguage", "English")

                    # do memory retrieval
                    # memory = "none"
                    # if self._use_memory:
                    #     memory = self._memory_agent.retrieval(user_query=query)

                    try:
                        # call task agent
                        await self._task_agent.task(websocket=websocket, task_content=query)

                    except Exception as e:
                        print(f"Error: {e}")
                        await websocket.send_text(f"Error: {str(e)}")

            except WebSocketDisconnect:
                print("Client disconnected")

        @self.app.websocket("/ping")
        async def handle_ping(websocket: WebSocket):
            await websocket.accept()
            data = await websocket.receive_json()
            print(data)
            
            try:
                for i in range(5):
                    await websocket.send_text("Ping: Server running")
                    await asyncio.sleep(0.1)
                await websocket.send_text("FINISHED")
            except WebSocketDisconnect:
                print("Client disconnected")

    def shutdown(self):
        self._memory_agent.shutdown()
        self._chat_agent.shutdown()
        self._task_agent.shutdown()
