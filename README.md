# MCP Client with Configurable Model Support

一个支持多种AI模型的MCP（Model Context Protocol）客户端，可以连接到任何MCP服务器并使用不同的AI模型进行交互。

## 功能特性

- 支持两种AI模型提供商：
  - Anthropic Claude
  - 阿里云Qwen（通过DashScope API）
- 灵活的配置选项（命令行参数或配置文件）
- 完整的工具调用支持
- 交互式聊天界面

## 安装

```bash
# 使用uv安装依赖
uv sync

# 或使用pip安装依赖
pip install -r requirements.txt
```

## 使用方法

### 基本用法（使用默认Claude模型）

```bash
python client.py /path/to/mcp/server.py
```

### 使用Qwen模型

```bash
python client.py /path/to/mcp/server.py --provider qwen --model qwen-turbo --api-key your-dashscope-api-key
```

### 使用配置文件

使用配置文件运行：

```bash
python client.py /path/to/mcp/server.py --config qwen_config_example.json
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
