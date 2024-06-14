import requests
import time


class Ternimal_Client:
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
                response = self._send_chat(query)
                print("🤖Assistant: " + response)

            elif self.mode == "task":
                task_received = self._send_task(query)
                if task_received:
                    print("✅task sent")
                    self._get_task_progress()

    def _send_chat(self, query):
        header = {'Content-Type': 'application/json'}
        data = {
            "query": query,
            "lanaguage": "English"
        }
        response = requests.post('http://127.0.0.1:9000/chat', headers=header, json=data)

        r = response.json()
        chat_response = r.get('chat_response')
        return chat_response
    
    def _send_task(self, query):
        header = {'Content-Type': 'application/json'}
        data = {
            "query": query,
            "lanaguage": "English"
        }
        response = requests.post('http://127.0.0.1:9000/task', headers=header, json=data)

        r = response.json()
        task_received = r.get('task_received')
        return task_received
    
    def _get_task_progress(self):
        count=0
        while  count<120:
            time.sleep(1)
            count = count + 1
            
            response = requests.get('http://127.0.0.1:9000/report_task')
            json_data = response.json()
            task_progress = json_data.get('task_progress')
            observation = json_data.get('observation')
            if task_progress == "None":
                continue
            if task_progress == "Finish":
                break
            print("Assistant: " + observation)

    def shutdown(self):
        print("client closed")


            
            