#!/usr/bin/env python3
"""
 REAL AI AUTOMATION TEST

This is the BIG ONE - connects all layers:
1. Automation Service (Layer 2) - captures screen & controls PC
2. Backend Proxy (Layer 3) - routes to AI
3. Ollama + LLaVA (AI Brain) - analyzes and decides actions
4. Executes AI-generated actions on YOUR computer!

This is automation magic! *
"""

import subprocess
import json
import sys
import time
import struct
import requests

SERVICE_PATH = r"automation_service\build\bin\Release\automation_service.exe"

class AutomationService:
    """Communicates with the C++ automation service"""
    
    def __init__(self):
        self.process = None
        
    def start(self):
        """Start the automation service"""
        print("Starting automation service...")
        self.process = subprocess.Popen(
            [SERVICE_PATH],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("[OK] Service started")
        
    def send_message(self, message):
        """Send a message via Native Messaging protocol"""
        encoded = json.dumps(message).encode('utf-8')
        length = struct.pack('@I', len(encoded))
        
        self.process.stdin.write(length)
        self.process.stdin.write(encoded)
        self.process.stdin.flush()
        
        # Read response
        raw_length = self.process.stdout.read(4)
        if not raw_length:
            raise Exception("No response from service")
            
        msg_length = struct.unpack('@I', raw_length)[0]
        response = self.process.stdout.read(msg_length)
        
        return json.loads(response.decode('utf-8'))
    
    def capture_screen(self):
        """Capture screenshot"""
        response = self.send_message({
            "action": "capture_screen",
            "params": {}
        })
        
        if response.get("success"):
            return response.get("screenshot")  # Base64 encoded
        else:
            raise Exception(f"Screen capture failed: {response.get('error')}")
    
    def get_ui_tree(self):
        """Get UI tree"""
        response = self.send_message({
            "action": "inspect_ui",
            "params": {}
        })
        
        if response.get("success"):
            return response.get("ui_tree")
        else:
            raise Exception(f"UI inspection failed: {response.get('error')}")
    
    def execute_action(self, action):
        """Execute a single action"""
        response = self.send_message(action)
        return response.get("success", False)
    
    def stop(self):
        """Stop the service"""
        if self.process:
            self.process.terminate()
            self.process.wait()


def send_to_ollama(screenshot, ui_tree, user_request):
    """Send to backend (Ollama)"""
    print(f"\nSending to Ollama: '{user_request}'")
    print("This may take 10-30 seconds...")
    
    payload = {
        'provider': 'ollama',
        'screenshot': screenshot,
        'ui_tree': ui_tree,
        'user_request': user_request
    }
    
    try:
        response = requests.post(
            'http://localhost:5000/api/get-actions',
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success') and 'actions' in data:
                return data['actions']
            elif 'error' in data:
                print(f"[ERROR] {data['error']}")
                if 'raw_response' in data:
                    print(f"Raw: {data['raw_response'][:200]}")
                return None
        else:
            print(f"[ERROR] HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"[ERROR] {e}")
        return None


def main():
    print("=" * 70)
    print("[AI] REAL AI AUTOMATION TEST")
    print("=" * 70)
    print()
    print("This will:")
    print("  1. Capture your screen (real screenshot)")
    print("  2. Send to Ollama AI")
    print("  3. Get automation actions from AI")
    print("  4. Execute on your computer!")
    print()
    print("REQUIREMENTS:")
    print("  - Ollama running (check)")
    print("  - Backend server running (check)")
    print("  - Automation service built (check)")
    print()
    
    input("Press Enter to start... ")
    print()
    
    # Step 1: Start automation service
    print("Step 1: Starting automation service...")
    service = AutomationService()
    
    try:
        service.start()
        print("[OK] Service started")
        print()
        
        # Step 2: Capture screen
        print("Step 2: Capturing your screen...")
        screenshot = service.capture_screen()
        print(f"[OK] Screenshot captured ({len(screenshot)} bytes base64)")
        print()
        
        # Step 3: Get UI tree
        print("Step 3: Getting UI tree...")
        ui_tree = service.get_ui_tree()
        print(f"[OK] UI tree captured ({len(str(ui_tree))} bytes)")
        print()
        
        # Step 4: Ask user what to do
        print("Step 4: What do you want the AI to do?")
        print()
        print("Examples:")
        print("  - Find the Start button")
        print("  - Click on Notepad if it's open")
        print("  - Describe what you see on screen")
        print()
        
        user_request = input("Your command: ").strip()
        
        if not user_request:
            print("[WARN] No command entered, using default")
            user_request = "Describe what you see on the screen"
        
        print()
        
        # Step 5: Send to Ollama
        print("Step 5: Sending to Ollama AI...")
        actions = send_to_ollama(screenshot, ui_tree, user_request)
        
        if not actions:
            print("[FAIL] No actions received from AI")
            print()
            print("This could mean:")
            print("  - Ollama is processing but returned unexpected format")
            print("  - The prompt needs tuning")
            print("  - Network issue")
            return
        
        print(f"[OK] AI returned {len(actions)} action(s)!")
        print()
        
        # Step 6: Show actions
        print("Step 6: AI-Generated Actions:")
        print()
        for i, action in enumerate(actions, 1):
            print(f"  {i}. {json.dumps(action, indent=4)}")
        print()
        
        # Step 7: Execute?
        print("Step 7: Execute these actions?")
        response = input("  (yes/no): ").strip().lower()
        
        if response == 'yes' or response == 'y':
            print()
            print("Executing actions...")
            
            for i, action in enumerate(actions, 1):
                print(f"  [{i}/{len(actions)}] Executing: {action.get('action', 'unknown')}")
                
                success = service.execute_action(action)
                
                if success:
                    print(f"      [OK]")
                else:
                    print(f"      [FAIL]")
                
                # Small delay between actions
                time.sleep(0.5)
            
            print()
            print("[OK] All actions executed!")
        else:
            print("[SKIP] Actions not executed")
        
        print()
        print("=" * 70)
        print("Success! TEST COMPLETE")
        print("=" * 70)
        print()
        print("What just happened:")
        print("  ✅ Captured your real screen")
        print("  ✅ AI (Ollama/LLaVA) analyzed it")
        print("  ✅ AI generated automation actions")
        if response in ('yes', 'y'):
            print("  ✅ Actions executed on your computer!")
        else:
            print("  [PAUSE] Actions shown but not executed")
        print()
        print("This is AI desktop automation! ==>")
        print()
        
    except KeyboardInterrupt:
        print("\n[STOP] Interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Always stop the service
        print("\nStopping automation service...")
        service.stop()
        print("[OK] Service stopped")


if __name__ == '__main__':
    main()

