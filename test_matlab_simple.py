#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test MATLAB MCP tools - simple version"""
import sys
sys.path.insert(0, 'E:/NEMT Simulator')
from matlab_mcp_server import get_matlab_info, eval_matlab, get_matlab_variable, execute_matlab
import json

# Test 1: get_matlab_info
print("Test 1: get_matlab_info")
result = get_matlab_info()
print("Success:", result.get("engine_available"))
print("Engine Running:", result.get("engine_running"))
print("MATLAB Version:", result.get("matlab_version"))
print()

# Test 2: execute_matlab for assignment (not eval_matlab)
print("Test 2: execute_matlab('a = 1 + 2')")
result = execute_matlab('a = 1 + 2')
print("Success:", result.get("success"))
if not result.get("success"):
    print("Error:", result.get("error"))
print()

# Test 3: eval_matlab for disp
print("Test 3: eval_matlab('disp(\"Hello from MATLAB!\")')")
result = eval_matlab('disp("Hello from MATLAB!")')
print("Success:", result.get("success"))
if not result.get("success"):
    print("Error:", result.get("error"))
print()

# Test 4: get_variable
print("Test 4: get_matlab_variable('a')")
result = get_matlab_variable('a')
print("Success:", result.get("success"))
if result.get("success"):
    print("Result:", result.get("result"))
else:
    print("Error:", result.get("error"))
