import asyncio
from typing import Optional, Dict, Any
from contextlib import AsyncExitStack
import os
import json
import re

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from anthropic import Anthropic
import dashscope
from dashscope import Generation
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

class MCPClient:
    def __init__(self, model_config: Optional[Dict[str, Any]] = None):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        
        # Model configuration
        self.model_config = model_config or {
            "provider": "anthropic",
            "model": "claude-3-5-sonnet-20241022",
            "api_key": os.getenv("ANTHROPIC_API_KEY")
        }
        
        # Initialize the appropriate client based on provider
        self._init_model_client()

    def _init_model_client(self):
        """Initialize the model client based on the provider configuration"""
        provider = self.model_config.get("provider", "anthropic").lower()
        
        if provider == "anthropic":
            api_key = self.model_config.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("Anthropic API key is required")
            self.anthropic = Anthropic(api_key=api_key)
            self.client_type = "anthropic"
            
        elif provider == "qwen" or provider == "dashscope":
            api_key = self.model_config.get("api_key") or os.getenv("DASHSCOPE_API_KEY")
            if not api_key:
                raise ValueError("DashScope API key is required for Qwen models")
            
            dashscope.api_key = api_key
            self.client_type = "qwen"
            
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _call_model(self, messages: list, tools: list = None):
        """Call the configured model with messages and tools"""
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
            # Convert messages to Qwen format
            qwen_messages = []
            for msg in messages:
                if msg["role"] == "tool":
                    # Convert tool results to user messages for Qwen
                    qwen_messages.append({
                        "role": "user",
                        "content": f"Tool result: {msg['content']}"
                    })
                else:
                    qwen_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # Add tool information to the system message if tools are available
            if tools:
                tool_descriptions = []
                for tool in tools:
                    tool_desc = f"- {tool['name']}: {tool['description']}"
                    if tool.get('input_schema', {}).get('properties'):
                        params = list(tool['input_schema']['properties'].keys())
                        tool_desc += f" (parameters: {', '.join(params)})"
                    tool_descriptions.append(tool_desc)
                
                tools_info = "Available tools:\n" + "\n".join(tool_descriptions)
                tools_info += "\n\nTo use a tool, respond with: TOOL_CALL: tool_name {\"param1\": \"value1\", \"param2\": \"value2\"}"
                tools_info += "\n\nNote: Common city coordinates for weather queries:"
                tools_info += "\n- Sacramento: latitude=38.5816, longitude=-121.4944"
                tools_info += "\n- San Francisco: latitude=37.7749, longitude=-122.4194"
                tools_info += "\n- Los Angeles: latitude=34.0522, longitude=-118.2437"
                tools_info += "\n- New York: latitude=40.7128, longitude=-74.0060"
                tools_info += "\n- Detroit: latitude=42.3314, longitude=-83.0458"
                tools_info += "\n- Beijing: latitude=39.9042, longitude=116.4074"
                tools_info += "\nFor other cities, use approximate coordinates or ask the user to provide them."
                
                # Add tools info to the first user message
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

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server
        
        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")
            
        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )
        
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        
        await self.session.initialize()
        
        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        """Process a query using the configured model and available tools"""
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]

        response = await self.session.list_tools()
        available_tools = [{ 
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in response.tools]

        # Initial API call using the configured client
        response = self._call_model(messages, available_tools)

        # Process response and handle tool calls
        tool_results = []
        final_text = []

        if self.client_type == "anthropic":
            for content in response.content:
                if content.type == 'text':
                    final_text.append(content.text)
                elif content.type == 'tool_use':
                    tool_name = content.name
                    tool_args = content.input
                    
                    # Execute tool call
                    result = await self.session.call_tool(tool_name, tool_args)
                    tool_results.append({"call": tool_name, "result": result})
                    final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                    # Continue conversation with tool results
                    if hasattr(content, 'text') and content.text:
                        messages.append({
                          "role": "assistant",
                          "content": content.text
                        })
                    messages.append({
                        "role": "user", 
                        "content": result.content
                    })

                    # Get next response
                    response = self._call_model(messages, available_tools)
                    final_text.append(response.content[0].text)
                    
        elif self.client_type == "qwen":
            if response.status_code == 200:
                message_content = response.output.choices[0].message.content
                
                # Check if the response contains a tool call
                if "TOOL_CALL:" in message_content:
                    lines = message_content.split('\n')
                    for line in lines:
                        if line.strip().startswith("TOOL_CALL:"):
                            try:
                                # Parse tool call: TOOL_CALL: tool_name {"param": "value"}
                                parts = line.strip().split("TOOL_CALL:", 1)[1].strip().split(" ", 1)
                                tool_name = parts[0].strip()
                                tool_args = {}
                                
                                if len(parts) > 1:
                                    tool_args = json.loads(parts[1].strip())
                                
                                # Execute tool call
                                result = await self.session.call_tool(tool_name, tool_args)
                                tool_results.append({"call": tool_name, "result": result})
                                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")
                                
                                # Continue conversation with tool results
                                messages.append({
                                    "role": "assistant",
                                    "content": message_content
                                })
                                messages.append({
                                    "role": "user",
                                    "content": f"Tool result: {result.content}"
                                })
                                
                                # Get next response
                                response = self._call_model(messages, available_tools)
                                if response.status_code == 200:
                                    final_text.append(response.output.choices[0].message.content)
                                
                            except Exception as e:
                                final_text.append(f"Error parsing tool call: {e}")
                                final_text.append(message_content)
                            break
                    else:
                        # No tool call found, just add the message
                        final_text.append(message_content)
                else:
                    final_text.append(message_content)
                
            else:
                final_text.append(f"Error: {response.message}")

        return "\n".join(final_text)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                
                if query.lower() == 'quit':
                    break
                    
                response = await self.process_query(query)
                print("\n" + response)
                    
            except Exception as e:
                print(f"\nError: {str(e)}")
    
    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Client with configurable model support")
    parser.add_argument("server_script", help="Path to the MCP server script")
    parser.add_argument("--provider", choices=["anthropic", "qwen", "dashscope"], 
                       default="anthropic", help="Model provider")
    parser.add_argument("--model", help="Model name to use")
    parser.add_argument("--api-key", help="API key for the model provider")
    parser.add_argument("--max-tokens", type=int, default=1000, help="Maximum tokens per response")
    parser.add_argument("--config", help="JSON config file with model settings")
    
    args = parser.parse_args()
    
    # Load configuration
    model_config = {}
    if args.config:
        try:
            with open(args.config, 'r') as f:
                model_config = json.load(f)
        except Exception as e:
            print(f"Error loading config file: {e}")
            sys.exit(1)
    
    # Override with command line arguments
    if args.provider:
        model_config["provider"] = args.provider
    if args.model:
        model_config["model"] = args.model
    if args.api_key:
        model_config["api_key"] = args.api_key
    if args.max_tokens:
        model_config["max_tokens"] = args.max_tokens
    
    # Set default models if not specified
    if "model" not in model_config:
        provider = model_config.get("provider")
        if provider in ["qwen", "dashscope"]:
            model_config["model"] = "qwen-turbo"
        else:
            model_config["model"] = "claude-3-5-sonnet-20241022"
    
    try:
        client = MCPClient(model_config)
        await client.connect_to_server(args.server_script)
        print(f"Using {model_config.get('provider')} with model {model_config.get('model')}")
        await client.chat_loop()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())
