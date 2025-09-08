import asyncio
from typing import Optional, Dict, Any, List
from contextlib import AsyncExitStack
import os
import json
import re
from dataclasses import dataclass

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from anthropic import Anthropic
import dashscope
from dashscope import Generation
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

@dataclass
class ServerConfig:
    """MCP服务器配置"""
    name: str
    description: str
    script_path: str
    enabled: bool = True
    config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}

@dataclass
class ServerConnection:
    """MCP服务器连接信息"""
    config: ServerConfig
    session: ClientSession
    stdio: Any
    write: Any
    tools: List[Dict[str, Any]]

class MultiServerMCPClient:
    """支持多个MCP服务器的客户端"""
    
    def __init__(self, config_path: str):
        """初始化多服务器MCP客户端
        
        Args:
            config_path: 配置文件路径
        """
        self.exit_stack = AsyncExitStack()
        self.servers: Dict[str, ServerConnection] = {}
        self.tool_server_map: Dict[str, str] = {}  # tool_name -> server_name
        
        # 加载配置
        self.config = self._load_config(config_path)
        self.model_config = self.config.get("model", {})
        self.server_configs = [ServerConfig(**server) for server in self.config.get("servers", [])]
        self.global_settings = self.config.get("global_settings", {})
        
        # 初始化模型客户端
        self._init_model_client()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise ValueError(f"无法加载配置文件 {config_path}: {e}")

    def _init_model_client(self):
        """根据配置初始化模型客户端"""
        provider = self.model_config.get("provider", "anthropic").lower()
        
        if provider == "anthropic":
            api_key = self.model_config.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("需要Anthropic API密钥")
            self.anthropic = Anthropic(api_key=api_key)
            self.client_type = "anthropic"
            
        elif provider == "qwen" or provider == "dashscope":
            api_key = self.model_config.get("api_key") or os.getenv("DASHSCOPE_API_KEY")
            if not api_key:
                raise ValueError("Qwen模型需要DashScope API密钥")
            
            dashscope.api_key = api_key
            self.client_type = "qwen"
            
        else:
            raise ValueError(f"不支持的提供商: {provider}")

    async def connect_to_servers(self):
        """连接到所有启用的MCP服务器"""
        connection_tasks = []
        
        for server_config in self.server_configs:
            if server_config.enabled:
                task = self._connect_to_server(server_config)
                connection_tasks.append(task)
        
        # 并发连接所有服务器
        if connection_tasks:
            results = await asyncio.gather(*connection_tasks, return_exceptions=True)
            
            # 处理连接结果
            for i, result in enumerate(results):
                server_config = [s for s in self.server_configs if s.enabled][i]
                if isinstance(result, Exception):
                    print(f"连接服务器 {server_config.name} 失败: {result}")
                else:
                    print(f"成功连接到服务器: {server_config.name}")

    async def _connect_to_server(self, server_config: ServerConfig):
        """连接到单个MCP服务器"""
        try:
            # 检查脚本文件类型
            script_path = server_config.script_path
            if not os.path.exists(script_path):
                raise FileNotFoundError(f"服务器脚本不存在: {script_path}")
                
            is_python = script_path.endswith('.py')
            is_js = script_path.endswith('.js')
            if not (is_python or is_js):
                raise ValueError("服务器脚本必须是.py或.js文件")
                
            command = "python" if is_python else "node"
            server_params = StdioServerParameters(
                command=command,
                args=[script_path],
                env=None
            )
            
            # 建立连接
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            stdio, write = stdio_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(stdio, write)
            )
            
            await session.initialize()
            
            # 获取可用工具
            response = await session.list_tools()
            tools = [{
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
                "server": server_config.name  # 添加服务器标识
            } for tool in response.tools]
            
            # 创建服务器连接对象
            connection = ServerConnection(
                config=server_config,
                session=session,
                stdio=stdio,
                write=write,
                tools=tools
            )
            
            # 保存连接和工具映射
            self.servers[server_config.name] = connection
            for tool in tools:
                self.tool_server_map[tool["name"]] = server_config.name
                
            print(f"服务器 {server_config.name} 提供工具: {[tool['name'] for tool in tools]}")
            
        except Exception as e:
            print(f"连接服务器 {server_config.name} 时出错: {e}")
            raise

    def get_all_tools(self) -> List[Dict[str, Any]]:
        """获取所有服务器的工具列表"""
        all_tools = []
        for server_name, connection in self.servers.items():
            all_tools.extend(connection.tools)
        return all_tools

    async def call_tool(self, tool_name: str, tool_args: Dict[str, Any]):
        """调用指定的工具"""
        server_name = self.tool_server_map.get(tool_name)
        if not server_name:
            raise ValueError(f"未找到工具 {tool_name} 对应的服务器")
            
        server_connection = self.servers.get(server_name)
        if not server_connection:
            raise ValueError(f"服务器 {server_name} 未连接")
            
        return await server_connection.session.call_tool(tool_name, tool_args)

    def _call_model(self, messages: list, tools: list = None):
        """使用配置的模型调用"""
        model_name = self.model_config.get("model")
        max_tokens = self.model_config.get("max_tokens", 1000)
        
        if self.client_type == "anthropic":
            kwargs = {
                "model": model_name,
                "max_tokens": max_tokens,
                "messages": messages
            }
            if tools:
                kwargs["tools"] = tools
            return self.anthropic.messages.create(**kwargs)
            
        elif self.client_type == "qwen":
            # 转换消息格式为Qwen格式
            qwen_messages = []
            for msg in messages:
                if msg["role"] == "tool":
                    # 将工具结果转换为用户消息
                    qwen_messages.append({
                        "role": "user",
                        "content": f"工具结果: {msg['content']}"
                    })
                else:
                    qwen_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # 如果有工具，添加工具信息到系统消息
            if tools:
                tool_descriptions = []
                for tool in tools:
                    tool_desc = f"- {tool['name']} (来自服务器: {tool.get('server', '未知')}): {tool['description']}"
                    if tool.get('input_schema', {}).get('properties'):
                        params = list(tool['input_schema']['properties'].keys())
                        tool_desc += f" (参数: {', '.join(params)})"
                    tool_descriptions.append(tool_desc)
                
                tools_info = "可用工具:\n" + "\n".join(tool_descriptions)
                tools_info += "\n\n要使用工具，请回复: TOOL_CALL: 工具名称 {\"参数1\": \"值1\", \"参数2\": \"值2\"}"
                
                # 将工具信息添加到第一个用户消息
                if qwen_messages and qwen_messages[0]["role"] == "user":
                    qwen_messages[0]["content"] = tools_info + "\n\n" + qwen_messages[0]["content"]
                else:
                    qwen_messages.insert(0, {"role": "user", "content": tools_info})
            
            response = Generation.call(
                model=model_name,
                messages=qwen_messages,
                max_tokens=max_tokens,
                result_format='message'
            )
            return response

    async def process_query(self, query: str) -> str:
        """处理查询请求"""
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]

        # 获取所有可用工具
        available_tools = self.get_all_tools()

        # 调用模型
        response = self._call_model(messages, available_tools)

        # 处理响应和工具调用
        tool_results = []
        final_text = []

        if self.client_type == "anthropic":
            for content in response.content:
                if content.type == 'text':
                    final_text.append(content.text)
                elif content.type == 'tool_use':
                    tool_name = content.name
                    tool_args = content.input
                    
                    # 执行工具调用
                    try:
                        result = await self.call_tool(tool_name, tool_args)
                        server_name = self.tool_server_map.get(tool_name, "未知")
                        tool_results.append({"call": tool_name, "result": result, "server": server_name})
                        final_text.append(f"[调用服务器 {server_name} 的工具 {tool_name}，参数: {tool_args}]")

                        # 继续对话
                        if hasattr(content, 'text') and content.text:
                            messages.append({
                              "role": "assistant",
                              "content": content.text
                            })
                        messages.append({
                            "role": "user", 
                            "content": result.content
                        })

                        # 获取下一个响应
                        response = self._call_model(messages, available_tools)
                        final_text.append(response.content[0].text)
                        
                    except Exception as e:
                        final_text.append(f"工具调用失败: {e}")
                        
        elif self.client_type == "qwen":
            if response.status_code == 200:
                message_content = response.output.choices[0].message.content
                
                # 检查响应是否包含工具调用
                if "TOOL_CALL:" in message_content:
                    lines = message_content.split('\n')
                    for line in lines:
                        if line.strip().startswith("TOOL_CALL:"):
                            try:
                                # 解析工具调用: TOOL_CALL: tool_name {"param": "value"}
                                parts = line.strip().split("TOOL_CALL:", 1)[1].strip().split(" ", 1)
                                tool_name = parts[0].strip()
                                tool_args = {}
                                
                                if len(parts) > 1:
                                    tool_args = json.loads(parts[1].strip())
                                
                                # 执行工具调用
                                result = await self.call_tool(tool_name, tool_args)
                                server_name = self.tool_server_map.get(tool_name, "未知")
                                tool_results.append({"call": tool_name, "result": result, "server": server_name})
                                final_text.append(f"[调用服务器 {server_name} 的工具 {tool_name}，参数: {tool_args}]")
                                
                                # 继续对话
                                messages.append({
                                    "role": "assistant",
                                    "content": message_content
                                })
                                messages.append({
                                    "role": "user",
                                    "content": f"工具结果: {result.content}"
                                })
                                
                                # 获取下一个响应
                                response = self._call_model(messages, available_tools)
                                if response.status_code == 200:
                                    final_text.append(response.output.choices[0].message.content)
                                
                            except Exception as e:
                                final_text.append(f"解析工具调用时出错: {e}")
                                final_text.append(message_content)
                            break
                    else:
                        # 没有找到工具调用，直接添加消息
                        final_text.append(message_content)
                else:
                    final_text.append(message_content)
                
            else:
                final_text.append(f"错误: {response.message}")

        return "\n".join(final_text)

    async def chat_loop(self):
        """运行交互式聊天循环"""
        print("\n多服务器MCP客户端已启动!")
        print("输入查询或输入 'quit' 退出。")
        print("输入 'servers' 查看已连接的服务器。")
        print("输入 'tools' 查看所有可用工具。")
        
        while True:
            try:
                query = input("\n查询: ").strip()
                
                if query.lower() == 'quit':
                    break
                elif query.lower() == 'servers':
                    self._show_servers()
                    continue
                elif query.lower() == 'tools':
                    self._show_tools()
                    continue
                    
                response = await self.process_query(query)
                print("\n" + response)
                    
            except Exception as e:
                print(f"\n错误: {str(e)}")

    def _show_servers(self):
        """显示已连接的服务器"""
        print("\n已连接的服务器:")
        for name, connection in self.servers.items():
            config = connection.config
            tools_count = len(connection.tools)
            print(f"- {name}: {config.description} ({tools_count} 个工具)")

    def _show_tools(self):
        """显示所有可用工具"""
        print("\n所有可用工具:")
        for server_name, connection in self.servers.items():
            print(f"\n服务器 {server_name}:")
            for tool in connection.tools:
                print(f"  - {tool['name']}: {tool['description']}")
    
    async def cleanup(self):
        """清理资源"""
        try:
            await self.exit_stack.aclose()
        except Exception as e:
            # 忽略清理时的错误，避免影响主程序
            pass

async def main():
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="支持多服务器的MCP客户端")
    parser.add_argument("config", help="多服务器配置文件路径")
    
    args = parser.parse_args()
    
    try:
        client = MultiServerMCPClient(args.config)
        await client.connect_to_servers()
        
        # 显示连接状态
        if client.servers:
            print(f"\n使用模型: {client.model_config.get('provider')} - {client.model_config.get('model')}")
            print(f"已连接 {len(client.servers)} 个服务器")
            await client.chat_loop()
        else:
            print("没有成功连接到任何服务器")
            sys.exit(1)
            
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)
    finally:
        if 'client' in locals():
            await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())
