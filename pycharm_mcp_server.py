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
PyCharm MCP服务器
通过stdin/stdout与MCP客户端通信，实现PyCharm代码执行功能
"""

import sys
import json
import os
import subprocess
import threading

# MATLAB MCP 服务器路径
MATLAB_MCP_SERVER = r"C:\Program Files\Python311\python.exe"
MATLAB_MCP_SCRIPT = "E:/NEMT Simulator/matlab_mcp_server.py"

# 线程本地存储：每个线程一个 MATLAB 引擎实例
_local = threading.local()


def get_matlab_engine():
    """获取或创建 MATLAB 引擎（线程安全）"""
    if not hasattr(_local, 'engine'):
        import matlab.engine
        _local.engine = matlab.engine.start_matlab()
        _local.running = True
    return _local.engine


def stop_matlab_engine():
    """停止 MATLAB 引擎"""
    if hasattr(_local, 'engine') and _local.engine:
        _local.engine.quit()
        _local.engine = None
        _local.running = False


def call_matlab_engine(code: str) -> dict:
    """调用 MATLAB 引擎执行代码（线程安全）"""
    try:
        eng = get_matlab_engine()
        eng.eval(code, nargout=0)
        return {"success": True, "message": "Code executed successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def eval_matlab_expression(expression: str) -> dict:
    """计算 MATLAB 表达式并返回结果"""
    try:
        eng = get_matlab_engine()
        result = eng.eval(expression)
        return {"success": True, "result": str(result) if result is not None else "null"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_matlab_variable(var_name: str) -> dict:
    """获取 MATLAB 工作区变量"""
    try:
        eng = get_matlab_engine()
        if eng.evalin("base", f"exist('{var_name}', 'var')"):
            result = eng.workspace[var_name]
            return {"success": True, "result": str(result), "type": type(result).__name__}
        else:
            return {"success": False, "error": f"Variable '{var_name}' does not exist"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def set_matlab_variable(var_name: str, value) -> dict:
    """设置 MATLAB 工作区变量"""
    try:
        eng = get_matlab_engine()
        eng.workspace[var_name] = value
        return {"success": True, "message": f"Variable '{var_name}' set successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def list_matlab_variables() -> dict:
    """列出 MATLAB 工作区所有变量"""
    try:
        eng = get_matlab_engine()
        vars = eng.eval("who")
        return {"success": True, "variables": list(vars)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_matlab_info() -> dict:
    """获取 MATLAB 信息"""
    try:
        import matlab.engine
        running = hasattr(_local, 'engine') and _local.running
        return {
            "engine_available": True,
            "engine_running": running,
            "matlab_version": "R2023b"
        }
    except ImportError:
        return {
            "engine_available": False,
            "engine_running": False,
            "error": "MATLAB Engine API not installed"
        }

def execute_python(code: str) -> dict:
    """执行Python代码并返回结果"""
    import io
    from contextlib import redirect_stdout, redirect_stderr
    
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
    
    result = {"success": True, "stdout": "", "stderr": "", "return_value": None}
    
    try:
        # 执行代码
        exec_globals = {"__name__": "__main__"}
        exec(code, exec_globals)
        
        stdout_output = sys.stdout.getvalue()
        stderr_output = sys.stderr.getvalue()
        
        result["stdout"] = stdout_output
        result["stderr"] = stderr_output
        
    except Exception as e:
        result["success"] = False
        result["stderr"] = f"{type(e).__name__}: {str(e)}"
    
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
    
    return result


def run_script(script_path: str, args: list = None) -> dict:
    """运行Python脚本"""
    import subprocess
    
    try:
        cmd = [sys.executable, script_path]
        if args:
            cmd.extend(args)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }
    except Exception as e:
        return {
            "success": False,
            "stderr": f"{type(e).__name__}: {str(e)}"
        }


def get_project_info() -> dict:
    """获取项目信息"""
    return {
        "workspace": os.getcwd(),
        "python_path": sys.executable,
        "python_version": sys.version,
        "files": [f for f in os.listdir(".") if f.endswith(".py")]
    }


def analyze_code(code: str) -> dict:
    """分析Python代码"""
    import ast
    
    try:
        tree = ast.parse(code)
        
        functions = []
        classes = []
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    "name": node.name,
                    "line": node.lineno,
                    "args": [arg.arg for arg in node.args.args]
                })
            elif isinstance(node, ast.ClassDef):
                classes.append({
                    "name": node.name,
                    "line": node.lineno,
                    "bases": [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases]
                })
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                else:
                    imports.append(f"{node.module}.{', '.join(a.name for a in node.names)}")
        
        return {
            "success": True,
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "line_count": len(code.split('\n'))
        }
    except SyntaxError as e:
        return {
            "success": False,
            "error": f"SyntaxError: {e.msg} at line {e.lineno}"
        }


def handle_request(request: dict) -> dict:
    """处理MCP请求"""
    method = request.get("method")
    params = request.get("params", {})
    id = request.get("id")
    
    response = {"jsonrpc": "2.0", "id": id}
    
    if method == "tools/list":
        response["result"] = {
            "tools": [
                {
                    "name": "execute_code",
                    "description": "Execute Python code",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Python code to execute"
                            }
                        },
                        "required": ["code"]
                    }
                },
                {
                    "name": "run_script",
                    "description": "Run a Python script file",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "script_path": {
                                "type": "string",
                                "description": "Path to the Python script"
                            },
                            "args": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Command line arguments"
                            }
                        },
                        "required": ["script_path"]
                    }
                },
                {
                    "name": "get_project_info",
                    "description": "Get project information"
                },
                {
                    "name": "analyze_code",
                    "description": "Analyze Python code structure",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Python code to analyze"
                            }
                        },
                        "required": ["code"]
                    }
                },
                {
                    "name": "matlab_info",
                    "description": "Get MATLAB engine status information"
                },
                {
                    "name": "matlab_execute",
                    "description": "Execute MATLAB code",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "MATLAB code to execute"
                            }
                        },
                        "required": ["code"]
                    }
                },
                {
                    "name": "matlab_eval",
                    "description": "Evaluate MATLAB expression and return result",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "MATLAB expression"
                            }
                        },
                        "required": ["expression"]
                    }
                },
                {
                    "name": "matlab_get_variable",
                    "description": "Get MATLAB workspace variable",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "var_name": {
                                "type": "string",
                                "description": "Variable name"
                            }
                        },
                        "required": ["var_name"]
                    }
                },
                {
                    "name": "matlab_set_variable",
                    "description": "Set MATLAB workspace variable",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "var_name": {
                                "type": "string",
                                "description": "Variable name"
                            },
                            "value": {
                                "description": "Variable value"
                            }
                        },
                        "required": ["var_name", "value"]
                    }
                },
                {
                    "name": "matlab_list_variables",
                    "description": "List all variables in MATLAB workspace"
                }
            ]
        }
    
    elif method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})
        
        try:
            if tool_name == "execute_code":
                result = execute_python(tool_args.get("code", ""))
            elif tool_name == "run_script":
                result = run_script(
                    tool_args.get("script_path"),
                    tool_args.get("args")
                )
            elif tool_name == "get_project_info":
                result = get_project_info()
            elif tool_name == "analyze_code":
                result = analyze_code(tool_args.get("code", ""))
            elif tool_name == "matlab_info":
                result = get_matlab_info()
            elif tool_name == "matlab_execute":
                result = call_matlab_engine(tool_args.get("code", ""))
            elif tool_name == "matlab_eval":
                result = eval_matlab_expression(tool_args.get("expression", ""))
            elif tool_name == "matlab_get_variable":
                result = get_matlab_variable(tool_args.get("var_name", ""))
            elif tool_name == "matlab_set_variable":
                result = set_matlab_variable(
                    tool_args.get("var_name", ""),
                    tool_args.get("value")
                )
            elif tool_name == "matlab_list_variables":
                result = list_matlab_variables()
            else:
                result = {"error": f"Unknown tool: {tool_name}"}
            
            response["result"] = {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}
        
        except Exception as e:
            response["error"] = {"code": -32603, "message": str(e)}
    
    elif method == "initialize":
        response["result"] = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {
                    "listChanged": True
                }
            },
            "serverInfo": {"name": "pycharm-mcp", "version": "1.0.0"}
        }
    
    elif method == "notifications/initialized":
        response = None
    
    else:
        response["error"] = {"code": -32601, "message": f"Method not found: {method}"}
    
    return response


def main():
    """主循环"""
    print("PyCharm MCP Server started", file=sys.stderr)
    
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
                "error": {"code": -32700, "message": f"Parse error: {str(e)}"},
                "id": None
            }
            print(json.dumps(error_response, ensure_ascii=False))
            sys.stdout.flush()
        
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": str(e)},
                "id": None
            }
            print(json.dumps(error_response, ensure_ascii=False))
            sys.stdout.flush()


if __name__ == "__main__":
    main()
