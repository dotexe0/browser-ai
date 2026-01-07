#!/usr/bin/env python3
"""Test script for Native Messaging protocol"""
import sys
import struct
import json
import subprocess

def send_message(message):
    """Send a message using Chrome Native Messaging protocol"""
    # Encode message as JSON
    encoded_message = json.dumps(message).encode('utf-8')
    
    # Write message length as 32-bit integer
    message_length = len(encoded_message)
    length_bytes = struct.pack('@I', message_length)
    
    return length_bytes + encoded_message

def read_message(input_stream):
    """Read a message from Native Messaging protocol"""
    # Read message length (4 bytes)
    raw_length = input_stream.read(4)
    
    if len(raw_length) == 0:
        return None
    
    message_length = struct.unpack('@I', raw_length)[0]
    
    # Read message
    message = input_stream.read(message_length).decode('utf-8')
    return json.loads(message)

def test_service(service_exe, message):
    """Test the service with a message"""
    # Start the service
    process = subprocess.Popen(
        [service_exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Send message
    encoded = send_message(message)
    process.stdin.write(encoded)
    process.stdin.flush()
    process.stdin.close()
    
    # Read response
    response = read_message(process.stdout)
    
    # Read stderr (logs)
    stderr = process.stderr.read().decode('utf-8')
    
    # Wait for process to finish
    process.wait()
    
    return response, stderr

if __name__ == '__main__':
    service_exe = r'A:\browser-ai\automation_service\build\bin\Release\automation_service.exe'
    
    print("=" * 60)
    print("Testing Browser AI Automation Service")
    print("=" * 60)
    print()
    
    # Test 1: Ping
    print("Test 1: Ping")
    print("-" * 60)
    message = {"action": "ping"}
    print(f"Sending: {json.dumps(message)}")
    response, logs = test_service(service_exe, message)
    print(f"Response: {json.dumps(response, indent=2)}")
    print()
    
    # Test 2: Get Capabilities
    print("Test 2: Get Capabilities")
    print("-" * 60)
    message = {"action": "get_capabilities"}
    print(f"Sending: {json.dumps(message)}")
    response, logs = test_service(service_exe, message)
    print(f"Response: {json.dumps(response, indent=2)}")
    print()
    
    print("=" * 60)
    print("Tests complete!")
    print("=" * 60)

