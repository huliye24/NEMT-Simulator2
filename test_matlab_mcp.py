#!/usr/bin/env python3
"""测试 MATLAB MCP 工具"""
import sys
sys.path.insert(0, 'E:/NEMT Simulator')
from matlab_mcp_server import get_matlab_info, eval_matlab, get_matlab_variable, matlab_engine
import json

print('=' * 60)
print('测试 1: get_matlab_info')
print('=' * 60)
result = get_matlab_info()
print(json.dumps(result, indent=2, ensure_ascii=False))
print()

print('=' * 60)
print('测试 2: eval_matlab 执行 a = 1 + 2')
print('=' * 60)
result = eval_matlab('a = 1 + 2')
print(json.dumps(result, indent=2, ensure_ascii=False))
print()

print('=' * 60)
print('测试 3: eval_matlab 执行 disp("Hello from MATLAB!")')
print('=' * 60)
result = eval_matlab('disp("Hello from MATLAB!")')
print(json.dumps(result, indent=2, ensure_ascii=False))
print()

print('=' * 60)
print('测试 4: get_variable 获取变量 a')
print('=' * 60)
result = get_matlab_variable('a')
print(json.dumps(result, indent=2, ensure_ascii=False))
print()

print('=' * 60)
print('所有测试完成')
print('=' * 60)
