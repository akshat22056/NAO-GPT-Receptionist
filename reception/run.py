import multiprocessing
import subprocess
import signal
import sys
import os

#Define paths
ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT, "src")

process1 = None
process2 = None

def run_python2_script():
    global process1
    process1 = subprocess.Popen(
        ["python2", "body.py"],
        cwd=SRC_DIR
    )

def run_python3_script():
    global process2
    process2 = subprocess.Popen(
        ["python3", "sidecar.py"],
        cwd=SRC_DIR
    )

def terminate_processes(signal_received, frame):
    """Handles termination when Ctrl+C is pressed."""
    print("\nTerminating processes...")

    if process1:
        process1.terminate()  # Terminate Python 2 process
        process1.wait()

    if process2:
        process2.terminate()  # Terminate Python 3 process
        process2.wait()

    sys.exit(0)  # Exit cleanly

if __name__ == "__main__":
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, terminate_processes)

    p1 = multiprocessing.Process(target=run_python2_script)
    p2 = multiprocessing.Process(target=run_python3_script)

    p1.start()
    p2.start()

    try:
        p1.join()
        p2.join()

    except KeyboardInterrupt:
        terminate_processes(None, None)
