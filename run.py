import subprocess
import sys
import time
import requests

def wait_for_backend(url, retries=10, delay=0.5):
    for _ in range(retries):
        try:
            requests.get(url)
            return True
        except:
            time.sleep(delay)
    return False

# Start FastAPI backend in background
backend = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "backend:app", "--host", "127.0.0.1", "--port", "8000"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

print("⏳ Starting backend...")
if wait_for_backend("http://127.0.0.1:8000"):
    print("✅ Backend ready.")
else:
    print("⚠️  Backend slow to start, continuing anyway...")

# Start Streamlit (this blocks until you close it)
try:
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", "app.py"],
    )
finally:
    # When Streamlit exits, kill the backend too
    backend.terminate()
    print("🛑 Backend stopped.")
