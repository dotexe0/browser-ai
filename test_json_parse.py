#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test if the JSON from Ollama actually parses"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import json

# Exact string from the debug output
ollama_response = '[{"action": "type", "params": {"text": "AI is working!", "target": "window"}}]'

print("Testing JSON parsing:")
print(f"Input: {ollama_response}")
print()

try:
    parsed = json.loads(ollama_response)
    print("✅ JSON parsed successfully!")
    print(f"Type: {type(parsed)}")
    print(f"Length: {len(parsed)}")
    print(f"Parsed data: {json.dumps(parsed, indent=2)}")
except json.JSONDecodeError as e:
    print(f"❌ Failed to parse: {e}")

