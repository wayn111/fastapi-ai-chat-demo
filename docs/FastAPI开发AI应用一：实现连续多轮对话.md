本文将通过一个完整的实战项目，介绍如何使用 FastAPI 框架开发 AI 聊天应用，重点讲解连续多轮对话的实现原理和核心技术。即使你是编程新手，也能跟着本教程一步步构建出功能完整的 AI 聊天应用。

> 本项目已经开源之 Github，项目地址：<https://github.com/wayn111/fastapi-ai-chat-demo>
>
> 温馨提示：本文全文约一万字，看完约需 15分钟。

## 项目概述

想象一下，你正在和一个聪明的 AI 助手对话，它不仅能回答你的问题，还能记住你们之前聊过的内容。这就是我们要构建的 AI 聊天应用！

### 核心功能

*   **连续多轮对话**：AI 能记住对话历史，就像和真人聊天一样自然
*   **多角色切换**：可以选择不同的 AI 角色（智能助手、AI 老师、编程专家）
*   **流式响应**：AI 回复时有打字机效果，体验更流畅
*   **会话管理**：支持多个对话会话，可以随时切换
*   **Web 界面**：简洁美观的聊天界面，操作简单

### 技术栈

*   **后端框架**：FastAPI（Python 的现代 Web 框架）
*   **数据存储**：Redis（高性能内存数据库）
*   **AI 模型**：支持 OpenAI 接口请求调用
*   **前端**：HTML + CSS + JavaScript
*   **服务器**：Uvicorn（高性能 ASGI 服务器）

## 核心架构

### 🏗️ 应用初始化

应用启动时需要完成几个关键的初始化步骤，就像搭建房子需要先打地基一样：

**1. 创建 Web 应用框架**

使用 FastAPI 创建应用实例，这是整个系统的核心。FastAPI 会自动生成 API 文档，让开发和调试变得更简单。

**2. 连接数据存储**

Redis 就像应用的"大脑记忆"，用来存储所有的对话历史。选择 Redis 是因为它速度快、支持数据过期，非常适合聊天应用的场景。

**3. 连接 AI 服务**

这是连接到 OpenAI 的"桥梁"，让我们能够调用 GPT 模型进行智能对话。通过配置 API 密钥和基础 URL，建立与 AI 服务的通信通道。

**4. 配置 AI 角色**

通过不同的"人设"提示词，让 AI 扮演不同的角色：

*   **智能助手**：友善专业，适合日常问答
*   **AI 老师**：耐心教学，善于解释复杂概念
*   **编程专家**：技术专业，提供代码建议

每个角色都有独特的回答风格，让用户获得更个性化的体验。

### 📋 数据模型设计

在聊天应用中，我们需要一个标准的"消息格式"来确保数据的一致性。就像寄信需要标准的信封格式一样：

    class ChatMessage(BaseModel):
        role: str        # 谁说的话："user"(用户) 或 "assistant"(AI)
        content: str     # 说了什么：具体的对话内容
        timestamp: float # 什么时候说的：消息时间戳

**为什么需要这个格式？**

*   **role 字段**：帮助 AI 区分哪些是用户的问题，哪些是自己的回答
*   **content 字段**：存储实际的对话内容
*   **timestamp 字段**：记录时间，方便按时间顺序显示对话

这种标准化的数据格式让我们的应用更加稳定可靠，也方便后续的功能扩展。

### 💭 多轮对话实现原理

多轮对话的"秘密"在于让 AI 能够"记住"之前聊过的内容。就像人类对话一样，我们需要上下文来理解当前的话题。

#### 🧠 工作原理

想象 AI 的"记忆"是这样工作的：

1.  **系统角色设定**："你是一个友善的 AI 助手"
2.  **历史对话**：
3.  *   用户："我叫小明"
    *   AI："你好小明！"
    *   用户："我喜欢编程"
    *   AI："编程很有趣！"
4.  **当前问题**："你还记得我的名字吗？"

当 AI 收到新问题时，它会看到完整的对话历史，所以能回答："当然记得，你是小明！"

### 🗂️ 会话管理

会话管理就像给每个用户分配一个"聊天房间"，让 AI 能够记住每个用户的对话历史。

#### 核心功能说明

**1. 生成会话 ID**

    def generate_session_id() -> str:
        return str(uuid.uuid4())

每个用户开始聊天时，系统会生成一个唯一的"房间号"（会话 ID），就像酒店给客人分配房间一样。

**2. 保存对话消息**

    def save_message(user_id: str, session_id: str, message: ChatMessage):
        conversation_key = get_conversation_key(user_id, session_id)
        redis_client.lpush(conversation_key, json.dumps(message_data))
        redis_client.ltrim(conversation_key, 0, 19)  # 只保留最近20条消息

通过 userid + 会话 id 生成 key，将消息保存到 Redis 队列中

**3. 获取对话历史**

    def get_conversation_history(user_id: str, session_id: str):
        conversation_key = get_conversation_key(user_id, session_id)
        messages = redis_client.lrange(conversation_key, 0, -1)
        return [json.loads(msg) for msg in messages]

从 userid + 会话 id 生成 key，从 Redis 中读取用户该会话的历史消息，让 AI 了解之前聊了什么

#### 为什么这样设计？

*   **唯一性**：每个会话都有独特的 ID，避免混淆
*   **持久化**：消息存储在 Redis 中，重启应用也不会丢失
*   **性能优化**：只保留最近的消息，避免内存占用过大
*   **自动清理**：每次只保留最近 20 条消息，自动清理旧数据

这种设计让 AI 能够"记住"每个用户的对话历史，实现真正的多轮对话体验。

### ⚡ 流式响应核心

流式响应就像 AI 在"实时打字"，让用户看到回复逐字出现，而不是等待很久后一次性显示全部内容。

#### 🔄 工作流程

**1. 保存用户消息**

    user_msg = ChatMessage(role="user", content=user_message)
    save_message(session_id, user_msg)

首先将用户的问题保存到"聊天记录本"中。

**2. 获取对话历史**

    history = get_conversation_history(session_id, limit=10)

读取最近 10 条对话记录，让 AI 了解聊天的上下文。

**3. 构建完整对话**

    messages = [
        {"role": "system", "content": AI_ROLES[role]},  # AI角色设定
        *history,  # 历史对话
        {"role": "user", "content": user_message}  # 当前问题
    ]

将角色设定、历史对话和当前问题组合成完整的对话上下文。

**4. 调用 AI 服务**

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        stream=True  # 关键：启用流式响应
    )

在 openAi 接口请求格式中，stream=True 表示启用流式响应。

**5. 实时返回回复**

    for chunk in response:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            yield f"data: {json.dumps({'content': content})}\n\n"

AI 每生成一小段文字，就立即发送给前端显示。

#### 💡 技术亮点

*   **Server-Sent Events (SSE)**  ：使用 SSE 协议实现服务器向浏览器的实时推送
*   **异步处理**：不阻塞其他用户的请求
*   **错误恢复**：网络中断时能够优雅处理
*   **上下文保持**：每次对话都能"记住"之前聊过的内容

这种设计让聊天体验更加自然流畅，就像和真人对话一样！

## 🔧 核心功能实现

### API 接口设计

我们的聊天应用提供了 5 个核心 API 接口，就像一个完整的"聊天服务台"：

#### 🆕 1. 开始新对话

    @app.post("/chat/start")
    async def start_chat(user_id: str):
        session_id = generate_session_id()
        return {"session_id": session_id, "welcome_message": "你好！我是你的AI助手"}

**功能**：为每个用户创建一个新的"聊天房间"，返回房间号（会话 ID）。

#### 💬 2. 流式聊天

    @app.get("/chat/stream")
    async def chat_stream(user_id: str, session_id: str, message: str, role: str = "assistant"):
        return StreamingResponse(generate_streaming_response(user_id, session_id, message, role))

**功能**：这是核心接口！处理用户消息，调用 AI 生成回复，并实时返回。

#### 📚 3. 获取聊天历史

    @app.get("/chat/history")
    async def get_chat_history(user_id: str, session_id: str):
        history = await get_conversation_history(user_id, session_id)
        return {"messages": history, "total": len(history)}

**功能**：查看之前的聊天记录，就像翻看聊天记录本。

#### 🗑️ 4. 清除对话历史

    @app.delete("/chat/history/{session_id}")
    async def clear_conversation_history(session_id: str, user_id: str):
        redis_client.delete(get_conversation_key(user_id, session_id))
        return {"message": "对话历史已清除"}

**功能**：清空聊天记录，重新开始对话。

#### 🎭 5. 获取 AI 角色列表

    @app.get("/roles")
    async def get_roles():
        return {"roles": AI_ROLES, "default_role": "assistant"}

**功能**：获取所有可用的 AI 角色（助手、老师、程序员等）。

#### 🛡️ 安全特性

*   **参数验证**：检查输入参数的有效性
*   **错误处理**：优雅处理各种异常情况
*   **CORS 支持**：允许跨域访问
*   **速率限制**：防止恶意请求（可选）

### 🎨 前端实现

前端就是用户看到和操作的界面，我们用 HTML、CSS 和 JavaScript 构建了一个现代化的聊天界面。

#### 🏗️ 界面结构

我们的聊天界面包含几个主要部分：

    <div class="chat-container">
        <!-- 1. 头部：显示标题和角色选择 -->
        <div class="chat-header">
            <h1>🤖 AI智能助手</h1>
            <select id="roleSelect">
                <option value="assistant">💬 智能助手</option>
                <option value="teacher">👨‍🏫 AI老师</option>
                <option value="programmer">👨‍💻 编程专家</option>
            </select>
        </div>

        <!-- 2. 消息区域：显示对话内容 -->
        <div class="messages-container" id="messagesContainer">
            <!-- 消息会动态添加到这里 -->
        </div>

        <!-- 3. 输入区域：用户输入消息 -->
        <div class="input-container">
            <input type="text" id="messageInput" placeholder="输入你的消息...">
            <button onclick="sendMessage()">📤 发送</button>
        </div>

        <!-- 4. 工具栏：常用功能按钮 -->
        <div class="toolbar">
            <button onclick="clearHistory()">🗑️ 清除历史</button>
            <button onclick="newChat()">🆕 新对话</button>
        </div>
    </div>

#### 🎨 样式设计特点

*   **现代化外观**：使用渐变色和圆角设计
*   **消息气泡**：用户消息在右边（蓝色），AI 消息在左边（白色）
*   **响应式布局**：在手机和电脑上都能正常显示
*   **动画效果**：按钮悬停效果和打字指示器
*   **清晰层次**：不同区域有明确的视觉分割

#### ⚙️ JavaScript 核心逻辑

JavaScript 负责处理用户交互和与后端的通信，就像聊天应用的"大脑"。

#### 🔧 核心功能实现

**1. 开始新对话**

    async function startNewChat() {
        // 调用后端API创建新会话
        const response = await fetch('/api/chat/start', { method: 'POST' });
        const data = await response.json();
        currentSessionId = data.session_id;

        // 显示欢迎消息
        addMessage('assistant', '你好！我是你的AI助手，有什么可以帮助你的吗？');
    }

**2. 发送消息**

    async function sendMessage() {
        const message = document.getElementById('messageInput').value;

        // 显示用户消息
        addMessage('user', message);

        // 使用EventSource接收流式响应
        const eventSource = new EventSource(`/api/chat/stream?session_id=${currentSessionId}&message=${message}`);

        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if (data.content) {
                // 实时显示AI回复
                updateAIMessage(data.content);
            }
        };
    }

**3. 添加消息到界面**

    function addMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        // 用户消息显示在右边，AI消息显示在左边
        const icon = role === 'user' ? '👤' : '🤖';
        messageDiv.innerHTML = `${icon} ${content}`;

        document.getElementById('messagesContainer').appendChild(messageDiv);

        // 自动滚动到最新消息
        messageDiv.scrollIntoView({ behavior: 'smooth' });
    }

**4. 清除历史记录**

    async function clearHistory() {
        if (confirm('确定要清除所有对话历史吗？')) {
            await fetch(`/api/chat/history/${currentSessionId}`, { method: 'DELETE' });
            document.getElementById('messagesContainer').innerHTML = '';
            addMessage('system', '对话历史已清除');
        }
    }

#### 💡 技术亮点

*   **EventSource**：实现服务器推送，让 AI 回复实时显示
*   **DOM 操作**：动态添加和更新聊天消息
*   **用户体验**：自动滚动、按钮状态管理、错误提示
*   **响应式设计**：适配不同设备和屏幕尺寸

这些 JavaScript 代码让聊天界面变得生动有趣，用户可以流畅地与 AI 进行对话！

## 如何开始项目

### 📋 环境准备

在开始之前，请确保你的电脑已安装：

1.  **Python 3.8+**  ：编程语言环境
2.  **Redis**：数据存储服务
3.  **OpenAI API 密钥**：用于调用 AI 模型

### 📁 项目结构

让我们先了解一下项目的文件组织结构：

    fastapi-ai-chat-demo/
    ├── main.py              # 🚀 主应用文件（核心逻辑）
    ├── config.py            # ⚙️ 配置文件（参数设置）
    ├── start_server.py      # 🔧 服务器启动脚本
    ├── requirements.txt     # 📦 依赖包列表
    ├── .env.example         # 📝 环境变量模板
    ├── static/
    │   └── index.html      # 🌐 前端聊天界面
    └── README.md           # 📖 项目说明文档

**文件说明：**

*   `main.py`：包含所有的 API 接口和核心业务逻辑
*   `config.py`：存放配置参数，如 Redis 连接信息、OpenAI 设置等
*   `static/index.html`：聊天界面的前端代码
*   `requirements.txt`：列出了项目需要的所有 Python 包

### 🚀 安装步骤

#### 1. 克隆项目

    git clone git@github.com:wayn111/fastapi-ai-chat-demo.git
    cd fastapi-ai-chat-demo

#### 2. 安装依赖包

    pip install -r requirements.txt

这会安装以下核心包：

*   `fastapi`：Web 框架
*   `uvicorn`：ASGI 服务器
*   `redis`：Redis 客户端
*   `openai`：OpenAI API 客户端
*   `pydantic`：数据验证库

#### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并填入你的配置：

    # OpenAI配置
    OPENAI_API_KEY=your_openai_api_key_here
    OPENAI_BASE_URL=https://api.openai.com/v1

    # Redis配置
    REDIS_HOST=localhost
    REDIS_PORT=6379

#### 4. 启动 Redis 服务

    # Windows
    redis-server

    # Linux/macOS
    sudo systemctl start redis

#### 5. 运行应用

    python start_server.py

#### 6. 访问应用

打开浏览器访问：`http://localhost:8000`

![图片](https://p0-xtjj-private.juejin.cn/tos-cn-i-73owjymdk6/55e6fcc2af384967aa4c94186887189b~tplv-73owjymdk6-jj-mark-v1:0:0:0:0:5o6Y6YeR5oqA5pyv56S-5Yy6IEAg56iL5bqP5ZGYd2F5bg==:q75.awebp?policy=eyJ2bSI6MywidWlkIjoiNDQwNjQ5ODMzNjk4MDEwMyJ9&rk3s=f64ab15b&x-orig-authkey=f32326d3454f2ac7e96d3d06cdbb035152127018&x-orig-expires=1752330791&x-orig-sign=DkikOm1f3yBLkYVYqKPz8xGjjHE%3D)

恭喜！你的 AI 聊天应用已经运行起来了！🎉

## 总结

本项目展示了使用 FastAPI 构建 AI 聊天应用的完整流程，核心技术包括：

*   **异步编程**：提升并发处理能力
*   **流式响应**：改善用户体验
*   **会话管理**：实现多轮对话记忆
*   **角色系统**：支持多样化 AI 交互

这个架构具有良好的扩展性，可以轻松添加用户认证、多模态交互等高级功能。FastAPI 的高性能和完善的类型系统使其成为构建现代 AI 应用的理想选择。
