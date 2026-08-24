#!/usr/bin/env python3
"""
NEMT Pipeline 一键测试脚本
==========================
测试完整的 Notion → NEMT → Signal → Notion 闭环

使用方法:
    python test_full_pipeline.py
"""

import os
import sys
import json
import time
import requests
from pathlib import Path

# 配置
API_BASE_URL = "http://localhost:8080"
TEST_PRICES = [100 + i * 0.5 + 10 * (i % 10) for i in range(100)]

def print_section(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)

def print_json(data, indent=2):
    print(json.dumps(data, indent=indent, ensure_ascii=False))

def wait_for_server(max_wait=10):
    """等待 API 服务器启动"""
    print(f"⏳ 等待 API 服务器 ({API_BASE_URL})...")
    for i in range(max_wait):
        try:
            response = requests.get(f"{API_BASE_URL}/", timeout=2)
            if response.status_code == 200:
                print("✅ API 服务器已就绪")
                return True
        except:
            pass
        time.sleep(1)
        print(f"  重试 {i+1}/{max_wait}...")
    print("❌ API 服务器连接失败")
    return False

def test_server_status():
    """测试服务器状态"""
    print_section("1. 检查服务器状态")
    try:
        response = requests.get(f"{API_BASE_URL}/api/pipeline/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ 服务器状态正常")
            print(f"   版本: {data.get('version', 'unknown')}")
            print(f"   MCP可用: {data.get('mcp_available', False)}")
            print(f"   组件: {list(data.get('components', {}).keys())}")
            return data
        else:
            print(f"❌ 服务器返回错误: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return None

def test_pipeline_run(prices, symbol="BTCUSDT", notion_page_id=None):
    """运行完整 Pipeline"""
    print_section("2. 运行完整 Pipeline")
    
    print(f"📊 参数:")
    print(f"   Symbol: {symbol}")
    print(f"   价格数据: {len(prices)} 个点")
    print(f"   起始价格: ${prices[0]:.2f}")
    print(f"   结束价格: ${prices[-1]:.2f}")
    if notion_page_id:
        print(f"   Notion Page ID: {notion_page_id}")
    
    payload = {
        "prices": prices,
        "symbol": symbol,
        "notion_page_id": notion_page_id
    }
    
    print("\n🚀 发送请求...")
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/pipeline/run",
            json=payload,
            timeout=30
        )
        elapsed = time.time() - start_time
        
        print(f"⏱️  响应时间: {elapsed:.2f}s")
        print(f"📡 状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Pipeline 执行成功!")
            
            # 打印步骤摘要
            steps = result.get('steps', {})
            print("\n📋 执行步骤:")
            for step_name, step_data in steps.items():
                success = step_data.get('success', False)
                status = "✅" if success else "❌"
                print(f"   {status} {step_name}")
            
            # 打印日志
            logs = result.get('logs', [])
            print(f"\n📜 执行日志 ({len(logs)} 条):")
            for log in logs:
                level = log.get('level', 'INFO')
                step = log.get('step', '')
                message = log.get('message', '')
                icon = "✅" if level == "SUCCESS" else "⚠️" if level == "WARNING" else "❌" if level == "ERROR" else "ℹ️"
                print(f"   {icon} [{level}] [{step}] {message}")
            
            # 打印生成的信号
            signal_data = steps.get('signal_generate', {}).get('signal')
            if signal_data:
                print("\n📈 生成的信号:")
                print(f"   类型: {signal_data.get('type', 'unknown')}")
                print(f"   方向: {signal_data.get('direction', 'unknown')}")
                print(f"   价格: ${signal_data.get('price', 0):.2f}")
                print(f"   置信度: {(signal_data.get('confidence', 0) * 100):.1f}%")
            
            return result
        else:
            print(f"❌ Pipeline 执行失败")
            print(f"   响应: {response.text[:500]}")
            return None
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return None

def test_signal_read():
    """测试信号历史读取"""
    print_section("3. 读取信号历史")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/signals?limit=5", timeout=5)
        if response.status_code == 200:
            data = response.json()
            signals = data.get('signals', [])
            print(f"✅ 获取到 {len(signals)} 条信号历史")
            return signals
        else:
            print(f"⚠️ 信号历史获取失败: {response.status_code}")
            return []
    except Exception as e:
        print(f"⚠️ 信号历史获取异常: {e}")
        return []

def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║          NEMT Pipeline 一键测试脚本                        ║
║          测试 Notion → NEMT → Signal → Notion 闭环         ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # 1. 等待服务器
    if not wait_for_server():
        print("\n❌ 无法连接到 API 服务器")
        print("请确保已启动: python quant-sync-server/api_server.py")
        sys.exit(1)
    
    # 2. 检查服务器状态
    status = test_server_status()
    if not status:
        print("\n❌ 服务器状态检查失败")
        sys.exit(1)
    
    # 3. 运行完整 Pipeline
    result = test_pipeline_run(TEST_PRICES, "BTCUSDT")
    
    if result and result.get('success'):
        print_section("🎉 V6 闭环验证成功!")
        print("""
✅ 完整流程已验证:
   1. ✅ Notion 读取策略参数
   2. ✅ NEMT 分析（频谱 + 相位识别）
   3. ✅ 信号生成（DCI + 涡旋 + 共振）
   4. ✅ 结果回写 Notion（模拟模式）

🚀 可以在浏览器中测试前端:
   1. 启动前端: cd web && npm run dev
   2. 打开浏览器: http://localhost:5173
   3. 点击 "Run Full Pipeline" 按钮
   4. 查看日志面板中的完整执行流程
        """)
    else:
        print("\n❌ Pipeline 执行失败，请检查错误日志")
        sys.exit(1)
    
    # 4. 测试信号历史
    test_signal_read()
    
    print("\n" + "="*60)
    print(" 测试完成")
    print("="*60)

if __name__ == "__main__":
    main()