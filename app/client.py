import asyncio
import websockets
import json


class Client:
    def __init__(self) -> None:
        self.mode = "chat"

    def run(self):
           
        print("🚀Go ahead:")
        print("💬/chat_mode: switch to chat mode")
        print("🔧/task_mode: switch to task mode\n")
        while(1):
            query = input("🧑User: ")

            if query.startswith("/chat_mode"):
                self.mode = "chat"
                print("✅switch to chat mode")
                continue
            elif query.startswith("/task_mode"):
                self.mode = "task"
                print("✅switch to task mode")
                continue
            
            if self.mode == "chat":
                print("🤖Kabutack: ", end='')
                asyncio.run(self._send_chat(query=query))

            elif self.mode == "task":
                print("🤖Kabutack: ", end='')
                asyncio.run(self._send_task(query=query))


    async def _send_chat(self, query):
        uri = "ws://0.0.0.0:8003/chat"
        async with websockets.connect(uri) as websocket:
            # 准备要发送的查询数据
            data = {"query": query}
            
            # 将数据转换为JSON格式的字符串
            json_data = json.dumps(data)
            
            # 发送JSON数据
            await websocket.send(json_data)
            
            try:
                while True:
                    message = await websocket.recv()                
                    # 如果接收到"STOP"，可以在这里处理
                    if message == "FINISHED":
                        break
                    print(message, end='', flush=True)

            except websockets.exceptions.ConnectionClosed:
                print("Connection closed")
            except Exception as e:
                print(f"An error occurred: {e}")
    

    async def _send_task(self, query):
        uri = "ws://0.0.0.0:8003/task"
        async with websockets.connect(uri) as websocket:
            # 准备要发送的查询数据
            data = {"query": query}
            
            # 将数据转换为JSON格式的字符串
            json_data = json.dumps(data)
            
            # 发送JSON数据
            await websocket.send(json_data)
            
            try:
                while True:
                    message = await websocket.recv()
                    # 如果接收到"FINISHED"，任务结束
                    if message == "FINISHED":
                        break
                    print(f'''🤖Kabutack: {message}''', flush=True)
                

            except websockets.exceptions.ConnectionClosed:
                print("Connection closed")
            except Exception as e:
                print(f"An error occurred: {e}")
    

    def shutdown(self):
        print("client closed")


# if __name__ == "__main__":
#     c = Client()
#     c.run()
    

            
            