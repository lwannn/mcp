# MCP Client with Configurable Model Support

一个支持多种AI模型的MCP（Model Context Protocol）客户端，可以连接到任何MCP服务器并使用不同的AI模型进行交互。

## 功能特性

- 支持两种AI模型提供商：
  - Anthropic Claude
  - 阿里云Qwen（通过DashScope API）
- 灵活的配置选项（命令行参数或配置文件）
- 完整的工具调用支持
- 交互式聊天界面
- **🆕 多服务器支持**：同时连接多个MCP服务器，统一管理所有工具

## 安装

```bash
# 使用uv安装依赖
uv sync

# 或使用pip安装依赖
pip install -r requirements.txt
```

## 使用方法

### 单服务器模式（原有功能）

#### 基本用法（使用默认Claude模型）

```bash
python client.py /path/to/mcp/server.py
```

#### 使用Qwen模型

```bash
python client.py /path/to/mcp/server.py --provider qwen --model qwen-turbo --api-key your-dashscope-api-key
```

#### 使用配置文件

使用配置文件运行：

```bash
python client.py /path/to/mcp/server.py --config qwen_config_example.json
```

### 🆕 多服务器模式

#### 使用多服务器配置文件

```bash
python multi_server_client.py multi_server_config_example.json
```

#### 使用Claude模型的多服务器配置

```bash
python multi_server_client.py claude_multi_server_config.json
```

## 命令行参数

- `server_script`: MCP服务器脚本路径（必需）
- `--provider`: 模型提供商 (`anthropic`, `qwen`, `dashscope`)
- `--model`: 模型名称
- `--api-key`: API密钥
- `--max-tokens`: 最大令牌数
- `--config`: JSON配置文件路径

## 环境变量

你也可以使用环境变量设置API密钥：

```bash
export ANTHROPIC_API_KEY="your-anthropic-key"
export DASHSCOPE_API_KEY="your-dashscope-key"
```

## 支持的模型提供商

### Anthropic
- 模型: `claude-3-5-sonnet-20241022`, `claude-3-haiku-20240307` 等
- 需要: `ANTHROPIC_API_KEY`

### 阿里云Qwen
- 模型: `qwen-turbo`, `qwen-plus`, `qwen-max` 等
- 需要: `DASHSCOPE_API_KEY`
- 获取API密钥: [阿里云DashScope控制台](https://dashscope.console.aliyun.com/)

## 示例

### 使用Qwen模型查询天气

```bash
python client.py ../weather/main.py --provider qwen --model qwen-turbo --api-key your-dashscope-key
```

### 使用Claude模型查询天气

```bash
python client.py ../weather/main.py --provider anthropic --model claude-3-5-sonnet-20241022 --api-key your-anthropic-key
```

## 故障排除

1. **导入错误**: 确保所有依赖都已安装 (`uv sync` 或 `pip install -r requirements.txt`)
2. **API密钥错误**: 检查环境变量或命令行参数中的API密钥
3. **连接错误**: 确保MCP服务器脚本路径正确且可执行

## 配置文件格式

配置文件应为JSON格式，支持以下字段：

```json
{
  "provider": "anthropic|qwen|dashscope",
  "model": "模型名称",
  "api_key": "API密钥",
  "max_tokens": 最大令牌数（默认1000）
}
```

### Qwen配置示例

参考 `qwen_config_example.json`：

```json
{
  "provider": "qwen",
  "model": "qwen-turbo",
  "api_key": "your-dashscope-api-key-here",
  "max_tokens": 2000
}
```

命令行参数会覆盖配置文件中的设置。

## 🆕 多服务器配置

### 多服务器配置文件格式

多服务器配置文件使用JSON格式，包含以下主要部分：

```json
{
  "model": {
    "provider": "qwen|anthropic",
    "model": "模型名称",
    "api_key": "API密钥",
    "max_tokens": 最大令牌数
  },
  "servers": [
    {
      "name": "服务器名称",
      "description": "服务器描述",
      "script_path": "服务器脚本路径",
      "enabled": true,
      "config": {
        "自定义配置": "值"
      }
    }
  ],
  "global_settings": {
    "concurrent_connections": 5,
    "connection_timeout": 10,
    "retry_attempts": 3
  }
}
```

### 配置说明

#### model 部分
- `provider`: 模型提供商（anthropic 或 qwen）
- `model`: 具体的模型名称
- `api_key`: API密钥
- `max_tokens`: 最大令牌数

#### servers 部分
- `name`: 服务器的唯一名称
- `description`: 服务器功能描述
- `script_path`: MCP服务器脚本的路径（相对或绝对路径）
- `enabled`: 是否启用此服务器（true/false）
- `config`: 服务器特定的配置参数

#### global_settings 部分
- `concurrent_connections`: 最大并发连接数
- `connection_timeout`: 连接超时时间（秒）
- `retry_attempts`: 连接失败重试次数

### 多服务器使用示例

#### 1. 启动多服务器客户端

```bash
cd mcp-client
python multi_server_client.py multi_server_config_example.json
```

#### 2. 交互式命令

在多服务器模式下，你可以使用以下特殊命令：

- `servers`: 查看已连接的服务器列表
- `tools`: 查看所有可用工具及其所属服务器
- `quit`: 退出程序

#### 3. 使用工具

客户端会自动将工具调用路由到正确的服务器。例如：

```
查询: 计算 2 + 3 的结果
# 自动调用calculator服务器的add工具

查询: 北京的天气怎么样？
# 自动调用weather服务器的get_forecast工具

查询: 统计这段文本的单词数量："Hello world from MCP"
# 自动调用text_processor服务器的count_words工具
```

### 内置服务器示例

项目包含以下示例MCP服务器：

1. **weather** - 天气服务
   - `get_forecast`: 获取天气预报
   - `get_alerts`: 获取天气预警

2. **calculator** - 数学计算
   - `add`, `subtract`, `multiply`, `divide`: 基础运算
   - `power`, `square_root`, `factorial`: 高级运算
   - `sin`, `cos`, `tan`: 三角函数

3. **text_processor** - 文本处理
   - `count_words`, `count_characters`: 文本统计
   - `to_uppercase`, `to_lowercase`, `reverse_text`: 文本转换
   - `extract_emails`, `extract_urls`: 内容提取
   - `word_frequency`, `split_sentences`: 文本分析

### 创建自定义MCP服务器

要创建自己的MCP服务器，请参考现有的服务器示例，使用FastMCP框架：

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("your_server_name")

@mcp.tool()
def your_function(param: str) -> str:
    """工具描述
    
    Args:
        param: 参数描述
    
    Returns:
        返回值描述
    """
    return f"处理结果: {param}"

if __name__ == "__main__":
    mcp.run(transport='stdio')
```

然后在配置文件中添加你的服务器配置即可。
