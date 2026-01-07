#!/usr/bin/env python3
"""Test and show service stderr output"""

import subprocess
import json
import struct
import time
import threading

SERVICE_PATH = r"automation_service\build\bin\Release\automation_service.exe"

def read_stderr(process):
    """Read stderr in a separate thread"""
    for line in iter(process.stderr.readline, b''):
        print(f"[SERVICE LOG] {line.decode('utf-8', errors='ignore').strip()}")

def send_action(process, action):
    encoded = json.dumps(action).encode('utf-8')
    length = struct.pack('@I', len(encoded))
    
    process.stdin.write(length)
    process.stdin.write(encoded)
    process.stdin.flush()
    
    raw_length = process.stdout.read(4)
    if not raw_length:
        return None
    
    msg_length = struct.unpack('@I', raw_length)[0]
    response = process.stdout.read(msg_length)
    
    return json.loads(response.decode('utf-8'))

print("Starting service with stderr logging...")
process = subprocess.Popen(
    [SERVICE_PATH],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    bufsize=0
)

# Start stderr reader thread
stderr_thread = threading.Thread(target=read_stderr, args=(process,), daemon=True)
stderr_thread.start()

time.sleep(0.5)

try:
    print("\nTesting Win+R...")
    result = send_action(process, {
        "action": "execute_action",
        "params": {
            "action": "press_keys",
            "params": {"keys": ["LWin", "R"]}
        }
    })
    print(f"Result: {json.dumps(result, indent=2)}")
    
    time.sleep(1)
    
finally:
    print("\nStopping service...")
    process.terminate()
    time.sleep(0.5)
    
print("Done")

