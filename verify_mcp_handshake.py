import subprocess
import json
import os
import sys
import threading
import time
from dotenv import load_dotenv

load_dotenv()

# Configuration from settings.json
PYTHON_EXE = "/Volumes/Asylum/dev/dionysus3-core/.venv/bin/python"
SERVER_SCRIPT = "/Volumes/Asylum/dev/dionysus3-core/dionysus_mcp/server.py"

ENV = os.environ.copy()
ENV["PYTHONPATH"] = "/Volumes/Asylum/dev/dionysus3-core"
ENV["NEO4J_URI"] = os.getenv("NEO4J_URI", "bolt://localhost:7687")
ENV["NEO4J_USER"] = os.getenv("NEO4J_USER", "neo4j")
ENV["NEO4J_PASSWORD"] = os.getenv("NEO4J_PASSWORD")

def run_handshake():
    print(f"🚀 Launching server: {PYTHON_EXE} {SERVER_SCRIPT}")
    
    process = subprocess.Popen(
        [PYTHON_EXE, SERVER_SCRIPT],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=ENV,
        text=True,
        bufsize=0 # Unbuffered
    )

    # JSON-RPC Initialize Request
    init_request = {
        "jsonrpc": "2.0", 
        "method": "initialize", 
        "params": {
            "protocolVersion": "2024-11-05", 
            "capabilities": {}, 
            "clientInfo": {"name": "verifier", "version": "1.0"}
        }, 
        "id": 1
    }
    
    json_line = json.dumps(init_request) + "\n"
    print(f"📤 Sending: {json_line.strip()}")
    
    try:
        process.stdin.write(json_line)
        process.stdin.flush()
    except BrokenPipeError:
        print("❌ Broken Pipe writing to stdin (Process likely died immediately)")
        
    # Read stdout with a timeout mechanism (simple approach)
    print("kb Listening for response...")
    
    response_line = process.stdout.readline()
    print(f"📥 Received raw: {response_line!r}")

    # Check for garbage
    if not response_line:
        print("❌ No response received (EOF). checking stderr...")
        print(f"🔴 Stderr: {process.stderr.read()}")
        return False

    try:
        data = json.loads(response_line)
        print("✅ Parsed JSON successfully.")
        
        if data.get("jsonrpc") == "2.0" and data.get("id") == 1:
            print("✅ Valid JSON-RPC Loopback Verified!")
            print(f"✨ Server Capabilities: {json.dumps(data.get('result', {}).get('capabilities'), indent=2)}")
            return True
        else:
            print("❌ Invalid JSON-RPC response content.")
            return False
            
    except json.JSONDecodeError:
        print("❌ JSON Decode Error! The output was likely polluted.")
        print(f"garbage content: {response_line}")
        return False
    finally:
        process.terminate()

if __name__ == "__main__":
    success = run_handshake()
    sys.exit(0 if success else 1)
