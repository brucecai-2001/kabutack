import os
import sys
import threading
import signal
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.server import Server

server = Server()

def signal_handler(sig, frame):
    print('Signal received, server is shutting down')
    server.shutdown()
    sys.exit()

signal.signal(signal.SIGINT, signal_handler)

t = threading.Thread(target=server.run)

t.start()

t.join()