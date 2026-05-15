import subprocess
import asyncio
import time
import sys
import httpx

# Start the uvicorn server in a subprocess
print("Starting uvicorn server...")
server_process = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

# Wait for server to be ready by checking if it responds to health check
max_wait = 15  # seconds
waited = 0
server_ready = False

print(f"Waiting up to {max_wait} seconds for server to start...")
while waited < max_wait:
    try:
        resp = httpx.get("http://localhost:8000/api/health", timeout=1)
        print(f"Server is ready! Health check returned {resp.status_code}")
        server_ready = True
        break
    except:
        pass
    time.sleep(1)
    waited += 1
    if waited % 3 == 0:
        print(f"  Still waiting... ({waited}s)")

if not server_ready:
    print("Server did not respond within timeout. Checking process...")
    if server_process.poll() is not None:
        stdout, stderr = server_process.communicate()
        print("Server crashed. STDOUT:", stdout[:500])
        print("STDERR:", stderr[:500])
    sys.exit(1)

try:
    # Now run the test
    print("\nRunning test...")
    test_result = subprocess.run(
        [sys.executable, "test_matching_status.py"],
        timeout=60
    )
    print(f"\nTest completed with exit code: {test_result.returncode}")
    sys.exit(test_result.returncode)
finally:
    # Clean up: terminate the server
    print("\nShutting down server...")
    server_process.terminate()
    try:
        server_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        server_process.kill()
        server_process.wait()
    print("Server stopped.")
