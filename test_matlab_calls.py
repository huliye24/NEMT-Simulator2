#!/usr/bin/env python3
"""Test MATLAB MCP server functions directly"""
import sys
sys.path.insert(0, "E:/NEMT Simulator")

from matlab_mcp_server import eval_matlab, execute_matlab

print("=== Test 1: eval_matlab - Simple calculation (a = 1 + 2) ===")
result1 = eval_matlab('a = 1 + 2')
print(f"Result: {result1}")

print()
print("=== Test 2: eval_matlab - Expression only ===")
result2 = eval_matlab('1 + 2')
print(f"Result: {result2}")

print()
print("=== Test 3: execute_matlab - disp function ===")
result3 = execute_matlab("disp('Hello from MATLAB!')")
print(f"Result: {result3}")
