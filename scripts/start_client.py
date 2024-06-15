import os
import sys
import threading
import signal
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.client import Client

client = Client()

def signal_handler(sig, frame):
    print('Signal received, server is shutting down')
    client.shutdown()
    sys.exit()

signal.signal(signal.SIGINT, signal_handler)

t = threading.Thread(target=client.run)

t.start()

t.join()