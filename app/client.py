import asyncio
import websockets
import json


class Client:
    def __init__(self) -> None:
        self.mode = "chat"

    def run(self):
           
        print("🚀Go ahead:")
        print("💬/chat_mode: switch to chat mode")
        print("🔧/task_mode: switch to task mode")
        print("✅/ping: test connection\n")

        while(1):
            query = input("\n🧑User: ")

            if query.startswith("/chat_mode"):
                self.mode = "chat"
                print("✅switch to chat mode")
                continue
            elif query.startswith("/task_mode"):
                self.mode = "task"
                print("✅switch to task mode")
                continue
            elif query.startswith("/ping"):
                asyncio.run(self._send_ping())
                continue
            
            if self.mode == "chat":
                asyncio.run(self._send_chat(query=query))

            elif self.mode == "task":
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
                    # 如果接收到"FINISHED"，可以在这里处理
                    if message == "FINISHED":
                        break
                    print(f'''🤖Kabutack: {message}''', flush=True)

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
                # receive task progress JSON from websocket format:
                # {
                #     "status": FINISHED or ACTING,
                #     "success": True or False,
                #     "return_type": "text", "plot, "file",
                #     "result": message to user
                # }
                while True:
                    message = await websocket.recv()
                    response_JSON = self.__parse_task_response__(message)
                    # task finished, success or failed
                    if response_JSON['status'] == "FINISHED":
                        if response_JSON['success']:
                            # task success
                            if response_JSON['return_type'] == "text":  
                                print(f'''🤖Kabutack: {response_JSON['result']}''', flush=True)
                            break
                        else:
                            # task failed
                            print(f'''🤖Kabutack: {response_JSON['result']}''', flush=True)
                            break
                    
                    # task is progressing
                    if response_JSON['return_type'] == "text":  
                            print(f'''🤖Kabutack: {response_JSON['result']}''', flush=True)
                

            except websockets.exceptions.ConnectionClosed:
                print("Connection closed")


    async def _send_ping(self):
        uri = "ws://0.0.0.0:8003/ping"
        async with websockets.connect(uri) as websocket:
            # 准备要发送的查询数据
            data = {"query": "ping"}
            
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
                    print(f'''✅: {message}''', flush=True)
                

            except websockets.exceptions.ConnectionClosed:
                print("Connection closed")
            except Exception as e:
                print(f"An error occurred: {e}")
    

    def shutdown(self):
        print("client closed")

    
    def __parse_task_response__(self, response) -> dict:
        """
        response_dict = {
            "status": status,
            "success": success,
            "return_type": return_type,
            "result": result
        }
        Args:
            response (str): JSON string

        Returns:
            dict: JSON
        """
        response_JSON = json.loads(response)
        return response_JSON
    

            
            