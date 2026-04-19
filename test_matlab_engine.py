#!/usr/bin/env python3
"""Test MATLAB engine with execute method"""
import sys
sys.path.insert(0, "E:/NEMT Simulator")

from matlab_mcp_server import MATLABEngine

engine = MATLABEngine()
info = engine.start()
print("启动:", info)

if info["success"]:
    # 使用 execute 方法执行代码
    result = engine.execute("a = 1 + 2")
    print("执行 a = 1 + 2:", result)

    # 使用 eval_expression 获取变量
    var = engine.get_variable("a")
    print("获取 a:", var)

    # 执行数组赋值
    result2 = engine.execute("freqs = [0.1, 0.2, 0.3]")
    print("执行 freqs = [0.1, 0.2, 0.3]:", result2)

    var2 = engine.get_variable("freqs")
    print("获取 freqs:", var2)

    # 测试 NEMT 频谱分析
    nemt_code = """
    % FFT test
    psi = randn(100, 1) + 1i * randn(100, 1);
    spectrum = abs(fft(psi));
    N = length(psi);
    freqs = (0:N-1) / N;
    meanFreq = sum(freqs .* spectrum.^2) / sum(spectrum.^2);
    spectralWidth = sqrt(sum((freqs - meanFreq).^2 .* spectrum.^2) / sum(spectrum.^2));
    """
    result3 = engine.execute(nemt_code)
    print("执行 NEMT 代码:", result3)

    sw = engine.get_variable("spectralWidth")
    print("spectralWidth:", sw)

    mf = engine.get_variable("meanFreq")
    print("meanFreq:", mf)
