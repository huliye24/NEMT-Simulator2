#!/usr/bin/env python3
"""Test MATLAB MCP server functions with correct API"""
import sys
sys.path.insert(0, "E:/NEMT Simulator")

from matlab.engine import start_matlab
import matlab

print("=== Test 1: Starting MATLAB engine ===")
try:
    eng = start_matlab()
    print(f"MATLAB engine started: {eng}")
    print(f"Engine type: {type(eng)}")
except Exception as e:
    print(f"Error starting engine: {e}")
    sys.exit(1)

print()
print("=== Test 2: eval_matlab - Simple calculation (a = 1 + 2) ===")
try:
    result = eng.eval('a = 1 + 2')
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")

print()
print("=== Test 3: disp function ===")
try:
    eng.eval("disp('Hello from MATLAB!')", nargout=0)
    print("disp executed successfully")
except Exception as e:
    print(f"Error: {e}")

print()
print("=== Test 4: Quit engine ===")
eng.quit()
print("Engine quit successfully")
