"""Launch the local HackerCoderAI UI as a Windows desktop app."""
import threading
import time
import webbrowser
import uvicorn
from .main import app

HOST = "127.0.0.1"
PORT = 8001

def open_browser():
    time.sleep(1.2)
    webbrowser.open(f"http://{HOST}:{PORT}")

if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
