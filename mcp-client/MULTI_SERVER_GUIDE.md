# 多服务器MCP客户端使用指南

## 快速开始

### 1. 准备配置文件

复制并修改示例配置文件：

```bash
cp multi_server_config_example.json my_config.json
```

编辑 `my_config.json`，设置你的API密钥：

```json
{
  "model": {
    "provider": "qwen",
    "model": "qwen-turbo", 
    "api_key": "你的DashScope API密钥",
    "max_tokens": 2000
  }
}
```

### 2. 启动客户端

```bash
python multi_server_client.py my_config.json
```

### 3. 开始使用

启动后，你会看到连接状态：

```
成功连接到服务器: weather
服务器 weather 提供工具: ['get_alerts', 'get_forecast']
成功连接到服务器: calculator  
服务器 calculator 提供工具: ['add', 'subtract', 'multiply', 'divide', 'power', 'square_root', 'factorial', 'sin', 'cos', 'tan']
成功连接到服务器: text_processor
服务器 text_processor 提供工具: ['count_words', 'count_characters', 'to_uppercase', 'to_lowercase', 'reverse_text', 'remove_duplicates', 'extract_emails', 'extract_urls', 'replace_text', 'split_sentences', 'word_frequency']

使用模型: qwen - qwen-turbo
已连接 3 个服务器

多服务器MCP客户端已启动!
输入查询或输入 'quit' 退出。
输入 'servers' 查看已连接的服务器。
输入 'tools' 查看所有可用工具。
```

## 使用示例

### 数学计算

```
查询: 计算 15 的平方根
查询: 计算 sin(30度)
查询: 计算 5 的阶乘
```

### 天气查询

```
查询: 北京的天气预报
查询: 上海有什么天气预警吗？
```

### 文本处理

```
查询: 统计这段文本的单词数："Hello world from MCP client"
查询: 将文本转为大写："hello world"
查询: 从这段文本中提取邮箱：联系我们 support@example.com 或 admin@test.org
```

## 管理命令

- `servers` - 查看已连接的服务器
- `tools` - 查看所有可用工具
- `quit` - 退出程序

## 配置服务器

### 启用/禁用服务器

在配置文件中设置 `enabled` 字段：

```json
{
  "name": "calculator",
  "enabled": false  // 禁用此服务器
}
```

### 自定义服务器路径

```json
{
  "name": "my_server",
  "script_path": "/absolute/path/to/server.py"
}
```

### 服务器特定配置

```json
{
  "name": "weather",
  "config": {
    "timeout": 30,
    "api_endpoint": "custom_endpoint"
  }
}
```

## 故障排除

### 连接失败

1. 检查服务器脚本路径是否正确
2. 确保Python环境包含必要的依赖
3. 检查服务器脚本是否可执行

### API密钥错误

1. 检查配置文件中的API密钥
2. 验证环境变量设置
3. 确认API密钥有效且有足够权限

### 工具调用失败

1. 检查工具参数是否正确
2. 确认目标服务器正常运行
3. 查看错误信息获取详细原因

## 扩展功能

### 添加新服务器

1. 创建MCP服务器脚本
2. 在配置文件中添加服务器配置
3. 重启客户端

### 自定义模型配置

支持不同的模型提供商和参数：

```json
{
  "model": {
    "provider": "anthropic",
    "model": "claude-3-5-sonnet-20241022",
    "api_key": "your-anthropic-key",
    "max_tokens": 1000
  }
}
```
