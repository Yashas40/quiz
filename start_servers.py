import subprocess
import sys
import signal
import os

def run_servers():
    # Start Daphne ASGI server on port 8000
    daphne_cmd = [sys.executable, "-m", "daphne", "-b", "0.0.0.0", "-p", "8000", "smartquizarena.asgi:application"]
    # Start Django development server (WSGI) on port 8001 (or any other port)
    runserver_cmd = [sys.executable, "manage.py", "runserver", "0.0.0.0:8001"]
    try:
        print("Starting Daphne (ASGI) on port 8000 and Django runserver on port 8001...")
        daphne_proc = subprocess.Popen(daphne_cmd)
        runserver_proc = subprocess.Popen(runserver_cmd, cwd=os.getcwd())
        # Wait for both processes; handle termination
        def shutdown(signum, frame):
            print("Shutting down servers...")
            daphne_proc.terminate()
            runserver_proc.terminate()
        signal.signal(signal.SIGINT, shutdown)
        signal.signal(signal.SIGTERM, shutdown)
        daphne_proc.wait()
        runserver_proc.wait()
    except Exception as e:
        print(f"Error launching servers: {e}")
        daphne_proc.terminate()
        runserver_proc.terminate()

if __name__ == "__main__":
    run_servers()
