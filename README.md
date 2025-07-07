# FastAPI AI聊天应用

🤖 基于FastAPI的AI聊天应用，支持多轮对话、流式响应和Markdown渲染。

## ✨ 核心特性

- **多模型厂商支持** - 支持OpenAI、Claude、通义千问、文心一言等多个AI模型
- **多轮对话** - 保持上下文记忆的连续对话
- **流式响应** - 实时打字效果，流畅体验
- **多角色支持** - 智能助手、AI老师、编程专家
- **Markdown渲染** - 支持代码高亮、表格、列表等格式
- **现代化UI** - 响应式设计，支持移动端
- **Redis存储** - 高效的会话管理

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Redis服务器
- OpenAI API密钥

### 安装运行

```bash
# 1. 克隆项目
git clone <repository-url>
cd fastapi-ai-chat-demo

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 OpenAI API 密钥

# 4. 启动Redis
redis-server

# 5. 运行应用
python start_server.py
```

访问 http://localhost:8000 开始聊天！

## 📁 项目结构

```
fastapi-ai-chat-demo/
├── main.py              # 主应用
├── config.py            # 配置管理
├── start_server.py      # 启动脚本
├── static/index.html    # 前端界面
├── requirements.txt     # 依赖列表
└── .env.example        # 环境变量模板
```

## 🔧 技术栈

- **后端**: FastAPI + Python
- **存储**: Redis
- **AI模型**: OpenAI GPT-4o
- **前端**: HTML + CSS + JavaScript
- **特性**: SSE流式响应、Markdown解析、代码高亮

## 📖 主要功能

### 会话管理
- 自动生成会话ID
- 持久化对话历史
- 支持清除历史记录

### 流式对话
- 实时显示AI回复
- 支持中断和重试
- 优雅的错误处理

### Markdown支持
- 代码块语法高亮
- 表格、列表、引用
- 数学公式渲染

## 🔑 环境配置

复制环境变量模板并配置：
```bash
cp .env.example .env
```

编辑 `.env` 文件，配置AI提供商参数（至少配置一个）：

### OpenAI配置
```env
# OpenAI配置
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# 应用配置
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
```

## 🚀 部署

### 开发环境
```bash
python start_server.py
```

### 生产环境
```bash
# 使用Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker

# 或使用Docker
docker build -t fastapi-ai-chat .
docker run -p 8000:8000 fastapi-ai-chat
```

## 📡 API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/chat/start` | POST | 开始新对话 |
| `/chat/stream` | GET | 流式聊天（支持provider参数选择AI提供商） |
| `/chat/history/{session_id}` | GET | 获取聊天历史 |
| `/chat/sessions` | GET | 获取用户会话列表 |
| `/roles` | GET | 获取AI角色列表 |
| `/providers` | GET | 获取可用AI提供商列表 |
| `/chat/session/{session_id}` | DELETE | 删除会话 |

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License
