import subprocess
import time
import sys
import os

def start_tunnel():
    """
    Establishes a persistent SSH tunnel to the VPS n8n instance.
    Local port 5678 -> VPS port 5678
    """
    vps_ip = "72.61.78.89"
    ssh_user = "mani" # Assuming mani based on previous contexts
    ssh_key = "~/.ssh/mani_vps"
    
    print(f"🚀 Establishing SSH Tunnel to {vps_ip}:5678...")
    
    # -N: Do not execute a remote command (just for tunneling)
    # -L: Local port forwarding
    cmd = [
        "ssh", "-i", os.expanduser(ssh_key), 
        "-N", "-L", "5678:localhost:5678", 
        f"{ssh_user}@{vps_ip}"
    ]
    
    try:
        process = subprocess.Popen(cmd)
        print("✅ Tunnel process started (PID: {).".format(process.pid))
        print("📍 You can now access n8n at http://localhost:5678")
        print("⌨️ Press Ctrl+C to close the tunnel.")
        
        while True:
            time.sleep(1)
            if process.poll() is not None:
                print("❌ Tunnel crashed or closed. Restarting in 5s...")
                time.sleep(5)
                process = subprocess.Popen(cmd)
                
    except KeyboardInterrupt:
        print("\n🛑 Closing tunnel...")
        process.terminate()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_tunnel()
