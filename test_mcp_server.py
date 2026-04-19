import sys
sys.path.insert(0, "E:/NEMT Simulator")
import matlab_mcp_server

print(f"MATLAB Engine API 可用: {matlab_mcp_server.MATLAB_ENGINE_AVAILABLE}")
info = matlab_mcp_server.get_matlab_info()
print(f"引擎状态: {info}")
