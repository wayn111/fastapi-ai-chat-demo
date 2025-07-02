# FastAPI AI聊天应用演示

这是一个基于FastAPI的AI聊天应用演示项目，展示了如何实现连续多轮对话功能。

## 功能特性

- ✨ **多轮对话**: 支持连续的多轮对话，保持上下文记忆
- 🎭 **多角色支持**: 内置智能助手、AI老师、编程专家等多种AI角色
- 🔄 **流式响应**: 实时流式输出，提供流畅的对话体验
- 💾 **会话管理**: 基于Redis的高效会话存储和管理
- 🌐 **Web界面**: 简洁美观的聊天界面
- 📱 **响应式设计**: 支持多种设备访问

## 技术栈

- **后端**: FastAPI + Python 3.8+
- **数据库**: Redis (会话存储)
- **AI模型**: OpenAI GPT-3.5-turbo
- **前端**: HTML + CSS + JavaScript
- **部署**: Uvicorn ASGI服务器

## 项目结构

```
fastapi-ai-chat-demo/
├── main.py              # 主应用文件
├── config.py            # 配置文件
├── requirements.txt     # 依赖包列表
├── static/
│   └── index.html      # 前端聊天界面
└── README.md           # 项目说明
```

## 快速开始

### 1. 环境准备

确保您的系统已安装：
- Python 3.8 或更高版本
- Redis 服务器

### 2. 安装依赖

```bash
cd fastapi-ai-chat-demo
pip install -r requirements.txt
```

### 3. 配置环境

创建 `.env` 文件并配置以下参数：

```env
# OpenAI配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# 应用配置
DEBUG=true
API_HOST=0.0.0.0
API_PORT=8000
```

### 4. 启动Redis服务

```bash
# Windows (如果使用Redis for Windows)
redis-server

# Linux/macOS
sudo systemctl start redis
# 或
redis-server
```

### 5. 运行应用

```bash
python main.py
```

应用将在 `http://localhost:8000` 启动。

### 6. 访问聊天界面

打开浏览器访问：`http://localhost:8000/static/index.html`

## API接口说明

### 开始新对话
```http
POST /chat/start?user_id=your_user_id
```

### 流式聊天
```http
GET /chat/stream?user_id=your_user_id&session_id=session_id&message=your_message&role=assistant
```

### 获取聊天历史
```http
GET /chat/history?user_id=your_user_id&session_id=session_id
```

### 获取用户会话列表
```http
GET /chat/sessions?user_id=your_user_id
```

### 获取AI角色列表
```http
GET /roles
```

### 删除会话
```http
DELETE /chat/session/{session_id}?user_id=your_user_id
```

## 核心实现原理

### 1. 会话管理

每个用户的对话会话通过唯一的 `session_id` 标识，会话数据存储在Redis中：

- **对话历史**: `conversation:{user_id}:{session_id}`
- **用户会话列表**: `user_sessions:{user_id}`

### 2. 多轮对话实现

```python
# 获取历史对话
history = await get_conversation_history(user_id, session_id)

# 构建上下文消息
openai_messages = [{"role": "system", "content": system_prompt}]
for msg in history[-20:]:  # 保留最近20轮对话
    openai_messages.append({"role": msg["role"], "content": msg["content"]})
```

### 3. 流式响应

使用Server-Sent Events (SSE) 实现实时流式输出：

```python
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=openai_messages,
    stream=True  # 启用流式响应
)

for chunk in response:
    if chunk.choices[0].delta.content:
        content = chunk.choices[0].delta.content
        yield f"data: {json.dumps({'content': content, 'type': 'chunk'})}\n\n"
```

### 4. 角色系统

通过不同的系统提示词实现多种AI角色：

```python
AI_ROLES = {
    "assistant": {
        "name": "智能助手",
        "prompt": "你是一个友善、专业的AI助手..."
    },
    "teacher": {
        "name": "AI老师", 
        "prompt": "你是一位经验丰富的老师..."
    }
}
```

## 扩展功能

### 添加新的AI角色

在 `main.py` 中的 `AI_ROLES` 字典中添加新角色：

```python
AI_ROLES["doctor"] = {
    "name": "AI医生",
    "prompt": "你是一位专业的医生，能够提供健康咨询..."
}
```

### 集成其他AI模型

修改 `generate_streaming_response` 函数中的模型调用部分，支持其他AI服务提供商。

### 添加用户认证

可以集成JWT或其他认证机制来管理用户身份。

## 部署建议

### Docker部署

创建 `Dockerfile`：

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py"]
```

### 生产环境配置

- 使用Gunicorn或其他WSGI服务器
- 配置Nginx反向代理
- 使用Redis集群提高可用性
- 添加日志和监控

## 注意事项

1. **API密钥安全**: 请妥善保管OpenAI API密钥，不要提交到版本控制系统
2. **Redis安全**: 生产环境中请配置Redis密码和访问控制
3. **资源限制**: 建议设置对话长度和并发连接数限制
4. **错误处理**: 完善异常处理和用户友好的错误提示

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！