import time
import webbrowser
import paramiko
import sys

# --- CONFIGURATION ---
HOST = "100.124.168.21"
USER = "root"
PASS = "R3dL05n3r!" 

# Your exact commands
REMOTE_CMD = "cd disk_web/ && fuser -k 8080/tcp; sleep 1; nohup python3 web_monitor.py > /dev/null 2>&1 &"
URL = f"http://{HOST}:8080" 

def start_nokia_monitor():
    try:
        print(f"[*] Connecting to Nokia Node: {HOST}...")
        
        # 1. Create a raw Transport (Bypasses the DSSKey/PKey discovery entirely)
        transport = paramiko.Transport((HOST, 22))
        transport.connect(username=USER, password=PASS)
        
        # 2. Open a session (channel) to run your commands
        channel = transport.open_session()
        print("[*] Executing remote commands...")
        channel.exec_command(REMOTE_CMD)
        
        # 3. Wait for the server to initialize
        print("[*] Waiting 10 seconds for initialization...")
        time.sleep(10)
        
        print(f"[*] Launching Chrome: {URL}")
        webbrowser.open(URL)
        
        print("\n" + "="*40)
        print(" SUCCESS: Nokia Disk Monitor is running.")
        print("="*40)
        print("[!] KEEP THIS WINDOW OPEN.")
        print("[!] Closing this window kills the SSH transport.")
        
        # 4. Keep the transport alive
        while transport.is_active():
            time.sleep(60)
            transport.send_ignore()

    except Exception as e:
        print(f"\n[!] Error: {e}")
        print("\nTIP: If it says 'Authentication failed', check your password.")
        input("\nPress Enter to exit...")
    finally:
        if 'transport' in locals():
            transport.close()

if __name__ == "__main__":
    start_nokia_monitor()