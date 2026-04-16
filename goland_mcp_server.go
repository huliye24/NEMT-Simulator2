// Copyright 2026 NEMT Lab
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// GoLand MCP Server
// 通过 stdio 与 MCP 客户端通信，实现 Go 开发环境功能
package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"strings"
)

// MCP 请求和响应结构
type Request struct {
	JSONRPC string          `json:"jsonrpc"`
	ID      interface{}     `json:"id"`
	Method  string          `json:"method"`
	Params  json.RawMessage `json:"params"`
}

type Response struct {
	JSONRPC string            `json:"jsonrpc"`
	ID     interface{}       `json:"id"`
	Result *json.RawMessage  `json:"result,omitempty"`
	Error  *Error            `json:"error,omitempty"`
}

type Error struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
}

// 工具定义
type Tool struct {
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	InputSchema map[string]interface{} `json:"inputSchema,omitempty"`
}

// 结果结构
type GoResult struct {
	Success bool        `json:"success"`
	Output  string      `json:"output,omitempty"`
	Error   string      `json:"error,omitempty"`
}

// 执行 Go 命令
func runGoCommand(args ...string) GoResult {
	cmd := exec.Command("go", args...)
	output, err := cmd.CombinedOutput()
	result := GoResult{
		Success: err == nil,
		Output:  string(output),
	}
	if err != nil {
		result.Error = err.Error()
	}
	return result
}

// 获取 Go 版本信息
func goVersion() GoResult {
	return runGoCommand("version")
}

// 获取 Go 环境信息
func goEnv() GoResult {
	cmd := exec.Command("go", "env")
	output, err := cmd.CombinedOutput()
	result := GoResult{
		Success: err == nil,
		Output:  string(output),
	}
	if err != nil {
		result.Error = err.Error()
	}
	return result
}

// 获取特定环境变量
func goEnvVar(name string) GoResult {
	cmd := exec.Command("go", "env", name)
	output, err := cmd.Output()
	result := GoResult{
		Success: err == nil,
		Output:  strings.TrimSpace(string(output)),
	}
	if err != nil {
		result.Error = err.Error()
	}
	return result
}

// 运行 go run
func goRun(file string, args []string) GoResult {
	cmdArgs := append([]string{"run", file}, args...)
	return runGoCommand(cmdArgs...)
}

// 运行 go build
func goBuild(file string) GoResult {
	return runGoCommand("build", file)
}

// 运行 go test
func goTest(pkg string, args []string) GoResult {
	cmdArgs := append([]string{"test", pkg}, args...)
	return runGoCommand(cmdArgs...)
}

// go mod tidy
func goModTidy() GoResult {
	return runGoCommand("mod", "tidy")
}

// go get
func goGet(pkg string) GoResult {
	return runGoCommand("get", pkg)
}

// go list
func goList(pkg string) GoResult {
	return runGoCommand("list", "-m", pkg)
}

// go vet
func goVet(pkg string) GoResult {
	return runGoCommand("vet", pkg)
}

// go fmt
func goFmt(file string) GoResult {
	return runGoCommand("fmt", file)
}

// 获取当前目录的模块名
func getCurrentModule() string {
	modFile := "go.mod"
	if _, err := os.Stat(modFile); err == nil {
		data, _ := os.ReadFile(modFile)
		lines := strings.Split(string(data), "\n")
		for _, line := range lines {
			if strings.HasPrefix(line, "module ") {
				return strings.TrimSpace(strings.TrimPrefix(line, "module "))
			}
		}
	}
	return ""
}

// 处理工具调用
func handleToolCall(name string, args map[string]interface{}) GoResult {
	switch name {
	case "go_version":
		return goVersion()
	case "go_env":
		return goEnv()
	case "go_env_var":
		if v, ok := args["name"].(string); ok {
			return goEnvVar(v)
		}
		return GoResult{Success: false, Error: "missing 'name' parameter"}
	case "go_run":
		if f, ok := args["file"].(string); ok {
			var runArgs []string
			if a, ok := args["args"].([]interface{}); ok {
				for _, arg := range a {
					if s, ok := arg.(string); ok {
						runArgs = append(runArgs, s)
					}
				}
			}
			return goRun(f, runArgs)
		}
		return GoResult{Success: false, Error: "missing 'file' parameter"}
	case "go_build":
		if f, ok := args["file"].(string); ok {
			return goBuild(f)
		}
		return GoResult{Success: false, Error: "missing 'file' parameter"}
	case "go_test":
		pkg := "."
		if p, ok := args["package"].(string); ok {
			pkg = p
		}
		var testArgs []string
		if a, ok := args["args"].([]interface{}); ok {
			for _, arg := range a {
				if s, ok := arg.(string); ok {
					testArgs = append(testArgs, s)
				}
			}
		}
		return goTest(pkg, testArgs)
	case "go_mod_tidy":
		return goModTidy()
	case "go_get":
		if p, ok := args["package"].(string); ok {
			return goGet(p)
		}
		return GoResult{Success: false, Error: "missing 'package' parameter"}
	case "go_list":
		pkg := getCurrentModule()
		if p, ok := args["package"].(string); ok {
			pkg = p
		}
		return goList(pkg)
	case "go_vet":
		pkg := "."
		if p, ok := args["package"].(string); ok {
			pkg = p
		}
		return goVet(pkg)
	case "go_fmt":
		if f, ok := args["file"].(string); ok {
			return goFmt(f)
		}
		return GoResult{Success: false, Error: "missing 'file' parameter"}
	case "go_info":
		version := goVersion()
		env := goEnv()
		return GoResult{
			Success: version.Success && env.Success,
			Output: fmt.Sprintf("Version:\n%s\n\nEnvironment:\n%s", version.Output, env.Output),
		}
	default:
		return GoResult{Success: false, Error: fmt.Sprintf("unknown tool: %s", name)}
	}
}

// 主循环
func main() {
	scanner := bufio.NewScanner(os.Stdin)
	fmt.Fprintf(os.Stderr, "GoLand MCP Server started\n")

	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}

		var req Request
		if err := json.Unmarshal([]byte(line), &req); err != nil {
			errorResp := Response{
				JSONRPC: "2.0",
				ID:      nil,
				Error: &Error{
					Code:    -32700,
					Message: fmt.Sprintf("Parse error: %v", err),
				},
			}
			respBytes, _ := json.Marshal(errorResp)
			fmt.Println(string(respBytes))
			os.Stdout.Sync()
			continue
		}

		var resp Response
		resp.JSONRPC = "2.0"
		resp.ID = req.ID

		switch req.Method {
		case "initialize":
			result := map[string]interface{}{
				"protocolVersion": "2024-11-05",
				"capabilities": map[string]interface{}{
					"tools": map[string]interface{}{
						"listChanged": true,
					},
				},
				"serverInfo": map[string]interface{}{
					"name":    "goland-mcp",
					"version": "1.0.0",
				},
			}
			resultBytes, _ := json.Marshal(result)
			rm := json.RawMessage(resultBytes)
			resp.Result = &rm

		case "tools/list":
			tools := []Tool{
				{Name: "go_info", Description: "Get Go environment information"},
				{Name: "go_version", Description: "Get Go version"},
				{Name: "go_env", Description: "Get all Go environment variables"},
				{Name: "go_env_var", Description: "Get specific Go environment variable",
					InputSchema: map[string]interface{}{
						"type": "object",
						"properties": map[string]interface{}{
							"name": map[string]interface{}{"type": "string"},
						},
						"required": []string{"name"},
					}},
				{Name: "go_run", Description: "Run a Go file",
					InputSchema: map[string]interface{}{
						"type": "object",
						"properties": map[string]interface{}{
							"file": map[string]interface{}{"type": "string"},
							"args": map[string]interface{}{"type": "array", "items": map[string]interface{}{"type": "string"}},
						},
						"required": []string{"file"},
					}},
				{Name: "go_build", Description: "Build a Go file",
					InputSchema: map[string]interface{}{
						"type": "object",
						"properties": map[string]interface{}{
							"file": map[string]interface{}{"type": "string"},
						},
						"required": []string{"file"},
					}},
				{Name: "go_test", Description: "Run Go tests",
					InputSchema: map[string]interface{}{
						"type": "object",
						"properties": map[string]interface{}{
							"package": map[string]interface{}{"type": "string"},
							"args":    map[string]interface{}{"type": "array", "items": map[string]interface{}{"type": "string"}},
						},
					}},
				{Name: "go_mod_tidy", Description: "Run go mod tidy"},
				{Name: "go_get", Description: "Get a Go package",
					InputSchema: map[string]interface{}{
						"type": "object",
						"properties": map[string]interface{}{
							"package": map[string]interface{}{"type": "string"},
						},
						"required": []string{"package"},
					}},
				{Name: "go_list", Description: "List Go packages",
					InputSchema: map[string]interface{}{
						"type": "object",
						"properties": map[string]interface{}{
							"package": map[string]interface{}{"type": "string"},
						},
					}},
				{Name: "go_vet", Description: "Run go vet",
					InputSchema: map[string]interface{}{
						"type": "object",
						"properties": map[string]interface{}{
							"package": map[string]interface{}{"type": "string"},
						},
					}},
				{Name: "go_fmt", Description: "Format Go file",
					InputSchema: map[string]interface{}{
						"type": "object",
						"properties": map[string]interface{}{
							"file": map[string]interface{}{"type": "string"},
						},
						"required": []string{"file"},
					}},
			}
			result := map[string]interface{}{"tools": tools}
			resultBytes, _ := json.Marshal(result)
			rm := json.RawMessage(resultBytes)
			resp.Result = &rm

		case "tools/call":
			var params struct {
				Name      string                 `json:"name"`
				Arguments map[string]interface{} `json:"arguments"`
			}
			if err := json.Unmarshal(req.Params, &params); err == nil {
				result := handleToolCall(params.Name, params.Arguments)
				content := []map[string]interface{}{
					{"type": "text", "text": toJSON(result)},
				}
				respResult := map[string]interface{}{"content": content}
				resultBytes, _ := json.Marshal(respResult)
				rm := json.RawMessage(resultBytes)
				resp.Result = &rm
			} else {
				resp.Error = &Error{Code: -32602, Message: "Invalid params"}
			}

		case "notifications/initialized":
			continue

		default:
			resp.Error = &Error{Code: -32601, Message: fmt.Sprintf("Method not found: %s", req.Method)}
		}

		respBytes, _ := json.Marshal(resp)
		fmt.Println(string(respBytes))
		os.Stdout.Sync()
	}
}

func toJSON(v interface{}) string {
	b, _ := json.Marshal(v)
	return string(b)
}
