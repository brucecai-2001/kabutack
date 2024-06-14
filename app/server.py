import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, request, jsonify
from werkzeug.serving import make_server

#from core.agents.manager_agent import ManagerAgent
from core.agent.chat_agent import ChatAgent
from core.agent.task_agent import ReActAgent
from core.agent.memory_agent import MemoAgent

from utils.func import save_img

class Server:
    out_lanaguage = "English"
    
    def __init__(self):
        # 初始化 Flask 应用
        self.app = Flask(__name__)
        self.server = None

        # 初始化 Agents
        print("system init starts")
        self._use_memory = True
        self._memory_agent = MemoAgent()
        self._chat_agent = ChatAgent()
        self._task_agent = ReActAgent()
        
        # 注册路由
        self._register_routes()
        print("App Init")


    def _register_routes(self):        

        @self.app.route('/chat', methods=['POST'])
        def handle_chat():
            data = request.get_json()
            query = data.get('query')
            out_lanaguage = data.get('output_lanaguage')

            memory = "none"
            if self._use_memory:
                memory = self._memory_agent.retrieval(user_query=query)
            try:
                chat_response = self._chat_agent.chat(memory=memory, query=query)
                response = jsonify(
                    {
                        "chat_response": chat_response
                    }
                )
                # 返回处理结果给前端
                return response, 200
            except:
                response = jsonify(
                    {
                        "chat_response": ""
                    }
                )
                # 返回处理结果给前端
                return response, 500

        
        @self.app.route('/chat_visual', methods=['POST'])
        def handle_chat_visual():
            data = request.get_json()
            query = data.get('query')
            out_lanaguage = data.get('output_lanaguage')
            image_bytes = request.data
            image_path = save_img(image_bytes)

            memory = "none"
            if self._use_memory:
                memory = self._memory_agent.retrieval(user_query=query)

            try:
                chat_response = self._chat_agent.chat(memory=memory, query=query, image=image_path)
                response = jsonify(
                    {
                        "chat_response": chat_response
                    }
                )
                # 返回处理结果给前端
                return response, 200
            except:
                response = jsonify(
                    {
                        "chat_response": chat_response
                    }
                )
                # 返回处理结果给前端
                return response, 500
        
        @self.app.route('/task', methods=['POST'])
        def handle_task():
            data = request.get_json()
            query = data.get('query')
            out_lanaguage = data.get('output_lanaguage')

            memory = "none"
            if self._use_memory:
                memory = self._memory_agent.retrieval(user_query=query)
            append_result = self._task_agent.append_task(type="task_text", memory=memory, query=query)

            response = jsonify(
                {
                    "task_received": append_result
                }
            )
            return response, 200

        @self.app.route('/task_visual', methods=['POST'])
        def handle_task_visual():
            data = request.get_json()
            query = data.get('query')
            out_lanaguage = data.get('output_lanaguage')
            image_bytes = request.data
            image_path = save_img(image_bytes)


            memory = "none"
            if self._use_memory:
                memory = self._memory_agent.retrieval(user_query=query)
            append_result = self._task_agent.append_task(intent="task_visual", memory=memory, query=query, image=image_path)

            response = jsonify(
                {
                    "task_received": append_result
                }
            )
            return response, 200
        

        @self.app.route('/report_task', methods=['GET'])
        def handle_report_task():
            task_progress, observation = self._task_agent.get_task_progress()
            response = jsonify(
                {
                    "task_progress" : task_progress, 
                    "observation" :  observation
                }
            )
            # 返回处理结果给前端
            return response, 200
            

    def run(self, host='0.0.0.0', port=9000):
        # 运行 Flask 应用
        self.server = make_server(host, port, self.app)
        self.server.serve_forever()



    def shutdown(self):
        self._chat_agent.shutdown()
        self._task_agent.shutdown()
        self._memory_agent.shutdown()

        if self.server:
            self.server.shutdown()
        print("App exit")