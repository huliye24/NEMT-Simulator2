#!/usr/bin/env python3
"""Test MATLAB engine"""
import sys
sys.path.insert(0, "E:/NEMT Simulator")

from matlab_mcp_server import get_matlab_info, eval_matlab, get_matlab_variable
import json

info = get_matlab_info()
print("引擎可用:", info["engine_available"])
print("引擎运行:", info["engine_running"])

if info["engine_available"]:
    # 测试简单计算
    result = eval_matlab("spectralWidth = sqrt(0.5)")
    print("计算结果:", result)

    # 测试获取变量
    var = get_matlab_variable("spectralWidth")
    print("变量spectralWidth:", json.dumps(var, indent=2))

    # 测试数组
    result2 = eval_matlab("freqs = [0.1, 0.2, 0.3]")
    print("数组结果:", result2)

    var2 = get_matlab_variable("freqs")
    print("freqs:", var2)
    if var2 and "result" in var2:
        print("freqs type:", type(var2["result"]))
        print("freqs value:", var2["result"])
