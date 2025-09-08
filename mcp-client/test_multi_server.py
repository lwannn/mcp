#!/usr/bin/env python3
"""
多服务器MCP客户端测试脚本

此脚本用于测试多服务器配置是否正常工作。
注意：需要有效的API密钥才能完整测试。
"""

import asyncio
import json
import os
import sys
from pathlib import Path

from multi_server_client import MultiServerMCPClient

async def test_multi_server():
    """测试多服务器功能"""
    
    # 创建测试配置
    test_config = {
        "model": {
            "provider": "qwen",
            "model": "qwen-turbo",
            "api_key": "test-key-placeholder",  # 需要替换为真实密钥
            "max_tokens": 1000
        },
        "servers": [
            {
                "name": "weather",
                "description": "天气服务",
                "script_path": "../mcp-server/weather/weather.py",
                "enabled": True,
                "config": {}
            },
            {
                "name": "calculator", 
                "description": "计算器服务",
                "script_path": "../mcp-server/calculator/calculator.py",
                "enabled": True,
                "config": {}
            },
            {
                "name": "text_processor",
                "description": "文本处理服务", 
                "script_path": "../mcp-server/text_processor/text_processor.py",
                "enabled": True,
                "config": {}
            }
        ],
        "global_settings": {
            "concurrent_connections": 3,
            "connection_timeout": 10,
            "retry_attempts": 2
        }
    }
    
    # 保存测试配置
    config_path = "test_config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(test_config, f, indent=2, ensure_ascii=False)
    
    print("🧪 开始测试多服务器MCP客户端...")
    
    try:
        # 初始化客户端
        print("📝 加载配置文件...")
        client = MultiServerMCPClient(config_path)
        
        print("🔌 连接到服务器...")
        await client.connect_to_servers()
        
        # 检查连接状态
        if not client.servers:
            print("❌ 没有成功连接到任何服务器")
            return False
            
        print(f"✅ 成功连接到 {len(client.servers)} 个服务器")
        
        # 显示服务器信息
        print("\n📊 服务器状态:")
        for name, connection in client.servers.items():
            tools_count = len(connection.tools)
            print(f"  - {name}: {connection.config.description} ({tools_count} 个工具)")
        
        # 显示所有工具
        print("\n🔧 可用工具:")
        all_tools = client.get_all_tools()
        for tool in all_tools:
            server_name = tool.get('server', '未知')
            print(f"  - {tool['name']} (来自 {server_name}): {tool['description']}")
        
        # 测试工具路由
        print("\n🎯 测试工具路由:")
        
        # 测试计算器工具
        if 'add' in client.tool_server_map:
            print("  测试计算器工具 'add'...")
            server_name = client.tool_server_map['add']
            print(f"    工具 'add' 映射到服务器: {server_name}")
            
        # 测试文本处理工具
        if 'count_words' in client.tool_server_map:
            print("  测试文本处理工具 'count_words'...")
            server_name = client.tool_server_map['count_words']
            print(f"    工具 'count_words' 映射到服务器: {server_name}")
            
        # 测试天气工具
        if 'get_forecast' in client.tool_server_map:
            print("  测试天气工具 'get_forecast'...")
            server_name = client.tool_server_map['get_forecast']
            print(f"    工具 'get_forecast' 映射到服务器: {server_name}")
        
        print("\n✅ 多服务器配置测试通过!")
        print("\n💡 要进行完整测试，请:")
        print("   1. 设置有效的API密钥")
        print("   2. 运行: python multi_server_client.py test_config.json")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
        
    finally:
        # 清理资源
        if 'client' in locals():
            await client.cleanup()
        
        # 删除测试配置文件
        if os.path.exists(config_path):
            os.remove(config_path)

def main():
    """主函数"""
    print("🚀 多服务器MCP客户端测试")
    print("=" * 50)
    
    # 检查依赖
    try:
        import mcp
        import anthropic
        import dashscope
        print("✅ 所有依赖已安装")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: uv sync 或 pip install -r requirements.txt")
        return
    
    # 运行测试
    try:
        result = asyncio.run(test_multi_server())
        if result:
            print("\n🎉 测试完成!")
        else:
            print("\n💥 测试失败!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n💥 测试过程中发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
