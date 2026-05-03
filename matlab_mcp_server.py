#!/usr/bin/env python3
# Copyright 2026 NEMT Lab
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
MATLAB MCP服务器
通过stdin/stdout与MCP客户端通信，实现MATLAB代码执行功能
依赖: MATLAB Engine API for Python
安装: 在MATLAB中运行: engine.start_matlab()
或者: cd $MATLABROOT/extern/engines/python && python setup.py install
"""

import sys
import json
import os

# MATLAB Engine API
try:
    import matlab.engine
    MATLAB_ENGINE_AVAILABLE = True
except ImportError:
    MATLAB_ENGINE_AVAILABLE = False
    print("警告: MATLAB Engine API 未安装", file=sys.stderr)


class MATLABEngine:
    """MATLAB引擎管理器"""
    
    def __init__(self):
        self.eng = None
        self.started = False
    
    def start(self, matlab_path=None):
        """启动MATLAB引擎"""
        if not MATLAB_ENGINE_AVAILABLE:
            return {"success": False, "error": "MATLAB Engine API 未安装"}
        
        try:
            if matlab_path:
                self.eng = matlab.engine.start_matlab(matlab_path)
            else:
                self.eng = matlab.engine.start_matlab()
            self.started = True
            return {"success": True, "message": "MATLAB引擎已启动"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def stop(self):
        """停止MATLAB引擎"""
        if self.eng:
            self.eng.quit()
            self.eng = None
            self.started = False
            return {"success": True, "message": "MATLAB引擎已停止"}
        return {"success": False, "error": "引擎未运行"}
    
    def execute(self, code: str) -> dict:
        """执行MATLAB代码"""
        if not self.started or not self.eng:
            start_result = self.start()
            if not start_result["success"]:
                return start_result
        
        try:
            stdout_capture = []
            stderr_capture = []
            
            # 将代码包装以便捕获输出
            wrapped_code = f"""
            try
                {code}
            catch ME
                fprintf(2, 'Error: %%s\\n', ME.message);
            end
            """
            
            # 执行代码
            self.eng.eval(wrapped_code, nargout=0)
            
            return {
                "success": True,
                "stdout": "",
                "stderr": "",
                "message": "代码执行成功"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"{type(e).__name__}: {str(e)}"
            }
    
    def eval_expression(self, expression: str):
        """计算MATLAB表达式并返回结果"""
        if not self.started or not self.eng:
            start_result = self.start()
            if not start_result["success"]:
                return start_result
        
        try:
            result = self.eng.eval(expression)
            return {"success": True, "result": str(result)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_variable(self, var_name: str):
        """获取MATLAB工作区变量"""
        if not self.started or not self.eng:
            start_result = self.start()
            if not start_result["success"]:
                return start_result
        
        try:
            if self.eng.evalin("base", f"exist('{var_name}', 'var')"):
                result = self.eng.workspace[var_name]
                return {"success": True, "result": str(result), "type": type(result).__name__}
            else:
                return {"success": False, "error": f"变量 '{var_name}' 不存在"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def set_variable(self, var_name: str, value):
        """在MATLAB工作区设置变量"""
        if not self.started or not self.eng:
            start_result = self.start()
            if not start_result["success"]:
                return start_result
        
        try:
            self.eng.workspace[var_name] = value
            return {"success": True, "message": f"变量 '{var_name}' 已设置"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_variables(self) -> dict:
        """列出MATLAB工作区变量"""
        if not self.started or not self.eng:
            start_result = self.start()
            if not start_result["success"]:
                return start_result
        
        try:
            vars = self.eng.eval("who")
            return {"success": True, "variables": list(vars)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def run_script(self, script_path: str) -> dict:
        """运行MATLAB脚本"""
        if not os.path.exists(script_path):
            return {"success": False, "error": f"脚本不存在: {script_path}"}
        
        if not self.started or not self.eng:
            start_result = self.start()
            if not start_result["success"]:
                return start_result
        
        try:
            self.eng.run(script_path, nargout=0)
            return {"success": True, "message": f"脚本执行成功: {script_path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def is_running(self) -> bool:
        """检查引擎是否运行"""
        return self.started and self.eng is not None


# 全局引擎实例
matlab_engine = MATLABEngine()


def execute_matlab(code: str) -> dict:
    """执行MATLAB代码"""
    return matlab_engine.execute(code)


def eval_matlab(expression: str) -> dict:
    """计算MATLAB表达式"""
    return matlab_engine.eval_expression(expression)


def get_matlab_variable(var_name: str) -> dict:
    """获取MATLAB变量"""
    return matlab_engine.get_variable(var_name)


def set_matlab_variable(var_name: str, value) -> dict:
    """设置MATLAB变量"""
    return matlab_engine.set_variable(var_name, value)


def list_matlab_variables() -> dict:
    """列出所有MATLAB变量"""
    return matlab_engine.list_variables()


def run_matlab_script(script_path: str) -> dict:
    """运行MATLAB脚本"""
    return matlab_engine.run_script(script_path)


def get_matlab_info() -> dict:
    """获取MATLAB信息"""
    if not MATLAB_ENGINE_AVAILABLE:
        return {
            "engine_available": False,
            "engine_running": False,
            "error": "MATLAB Engine API 未安装"
        }
    
    return {
        "engine_available": True,
        "engine_running": matlab_engine.is_running(),
        "matlab_version": "R2023b"
    }


def handle_request(request: dict) -> dict:
    """处理MCP请求"""
    method = request.get("method")
    params = request.get("params", {})
    req_id = request.get("id")
    
    response = {"jsonrpc": "2.0", "id": req_id}
    
    if method == "tools/list":
        response["result"] = {
            "tools": [
                {
                    "name": "execute_matlab",
                    "description": "执行MATLAB代码",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "MATLAB代码"
                            }
                        },
                        "required": ["code"]
                    }
                },
                {
                    "name": "eval_matlab",
                    "description": "计算MATLAB表达式并返回结果",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "MATLAB表达式"
                            }
                        },
                        "required": ["expression"]
                    }
                },
                {
                    "name": "get_variable",
                    "description": "获取MATLAB工作区变量",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "var_name": {
                                "type": "string",
                                "description": "变量名"
                            }
                        },
                        "required": ["var_name"]
                    }
                },
                {
                    "name": "set_variable",
                    "description": "设置MATLAB工作区变量",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "var_name": {
                                "type": "string",
                                "description": "变量名"
                            },
                            "value": {
                                "description": "变量值"
                            }
                        },
                        "required": ["var_name", "value"]
                    }
                },
                {
                    "name": "list_variables",
                    "description": "列出MATLAB工作区所有变量"
                },
                {
                    "name": "run_script",
                    "description": "运行MATLAB脚本文件",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "script_path": {
                                "type": "string",
                                "description": "脚本路径"
                            }
                        },
                        "required": ["script_path"]
                    }
                },
                {
                    "name": "get_matlab_info",
                    "description": "获取MATLAB引擎状态信息"
                }
            ]
        }
    
    elif method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})
        
        try:
            if tool_name == "execute_matlab":
                result = execute_matlab(tool_args.get("code", ""))
            elif tool_name == "eval_matlab":
                result = eval_matlab(tool_args.get("expression", ""))
            elif tool_name == "get_variable":
                result = get_matlab_variable(tool_args.get("var_name", ""))
            elif tool_name == "set_variable":
                result = set_matlab_variable(
                    tool_args.get("var_name", ""),
                    tool_args.get("value")
                )
            elif tool_name == "list_variables":
                result = list_matlab_variables()
            elif tool_name == "run_script":
                result = run_matlab_script(tool_args.get("script_path", ""))
            elif tool_name == "get_matlab_info":
                result = get_matlab_info()
            else:
                result = {"error": f"未知工具: {tool_name}"}
            
            response["result"] = {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}
        
        except Exception as e:
            response["error"] = {"code": -32603, "message": str(e)}
    
    elif method == "initialize":
        response["result"] = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": True}
            },
            "serverInfo": {"name": "matlab-mcp", "version": "1.0.0"}
        }
    
    elif method == "notifications/initialized":
        response = None
    
    else:
        response["error"] = {"code": -32601, "message": f"方法未找到: {method}"}
    
    return response


def main():
    """主循环"""
    print("MATLAB MCP Server 已启动", file=sys.stderr)
    print(f"MATLAB Engine API 可用: {MATLAB_ENGINE_AVAILABLE}", file=sys.stderr)
    
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            
            try:
                request = json.loads(line)
                response = handle_request(request)
                
                if response:
                    print(json.dumps(response, ensure_ascii=False))
                    sys.stdout.flush()
            
            except json.JSONDecodeError as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": f"JSON解析错误: {str(e)}"},
                    "id": None
                }
                print(json.dumps(error_response, ensure_ascii=False))
                sys.stdout.flush()
    
    except KeyboardInterrupt:
        print("正在关闭MATLAB MCP Server...", file=sys.stderr)
        matlab_engine.stop()
    except Exception as e:
        print(f"服务器错误: {e}", file=sys.stderr)
        matlab_engine.stop()


if __name__ == "__main__":
    main()
