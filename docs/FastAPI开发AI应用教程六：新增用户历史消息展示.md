本文将深入介绍如何在 FastAPI AI 聊天应用中实现用户历史消息展示功能，重点讲解每个助手区分 sessionid、获取历史消息接口以及发送消息时携带上下文信息的核心技术实现。通过本教程，你将掌握构建智能聊天应用中消息持久化和上下文管理的关键技术。

> 本项目已经开源至 Github，项目地址：<https://github.com/wayn111/fastapi-ai-chat-demo>
>
> 温馨提示：本文全文约一万字，看完约需 15 分钟。

## 文章概述

在现代 AI 聊天应用中，用户历史消息展示是一个至关重要的功能。它不仅能让用户回顾之前的对话内容，更重要的是为 AI 提供上下文信息，使对话更加连贯和智能。

### 核心功能

* **多助手会话隔离**：每个 AI 助手（智能助手、AI 老师、编程专家）都有独立的会话历史
* **智能会话管理**：自动生成和管理 sessionid，确保会话的唯一性和持久性
* **历史消息加载**：快速加载和展示用户的历史对话记录
* **上下文传递**：发送消息时自动携带历史上下文，保持对话连贯性
* **数据持久化**：支持 Redis 和内存两种存储方式

### 技术栈

* **后端框架**：FastAPI（高性能异步 Web 框架）
* **数据存储**：Redis（主要）+ 内存存储（备用）
* **前端技术**：原生 JavaScript + HTML5 + CSS3
* **数据格式**：JSON（消息序列化和传输）
* **会话管理**：UUID + 时间戳（会话 ID 生成）

## 核心架构设计

### 🏗️ 数据模型设计

在实现历史消息功能之前，我们需要设计合理的数据模型来存储和管理消息数据：

```python
@dataclass
class AIMessage:
    """AI消息数据类"""
    role: str
    content: str
    timestamp: float
    image_data: Optional[str] = None  # Base64编码的图片数据
    image_type: Optional[str] = None  # 图片类型 (jpeg, png, gif)
```

这个数据类定义了消息的基本结构，包含角色、内容、时间戳和可选的图片数据字段。

### 🔑 会话 ID 管理策略

会话 ID 是整个历史消息系统的核心，我们采用了前端生成、后端接收的管理策略：

**前端会话 ID 生成逻辑：**

```javascript
// 前端生成会话ID的核心逻辑
if (sessionId) {
    // 复用已存在的会话ID
    currentSessionId = sessionId;
} else {
    // 生成新的会话ID：时间戳 + 随机数
    const timestamp = Date.now();
    const randomNum = Math.floor(Math.random() * 10000);
    sessionId = `session_${timestamp}_${randomNum}`;
    currentSessionId = sessionId;
    localStorage.setItem(sessionKey, sessionId);
}
```

**后端键名管理：**

```python
def get_conversation_key(user_id: str, session_id: str) -> str:
    """获取对话在Redis中的键名"""
    return f"conversation:{user_id}:{session_id}"

def get_user_sessions_key(user_id: str) -> str:
    """获取用户会话列表在Redis中的键名"""
    return f"user_sessions:{user_id}"
```

前端生成唯一的会话ID并传递给后端，后端使用这个ID构建Redis键名来存储对话数据。

## 核心功能实现

### 🎯 功能一：每个助手区分 sessionid

#### 前端实现：智能会话管理

在前端，我们为每个助手类型维护独立的 sessionid，实现真正的会话隔离：

```javascript
/**
 * 选择智能助手类型
 * @param {string} assistantType - 助手类型
 */
function selectAssistant(assistantType) {
    // 更新当前助手类型
    currentAssistantType = assistantType;

    // 移除所有助手项的active类
    document.querySelectorAll('.assistant-item').forEach(item => {
        item.classList.remove('active');
    });

    // 为当前选中的助手添加active类
    event.target.closest('.assistant-item').classList.add('active');

    // 更新所有现有的assistant消息头像
    updateAssistantAvatars(assistantType);

    // 从全局配置中获取角色信息
    const roleConfig = aiRolesConfig[assistantType];
    if (!roleConfig) {
        console.error('未找到角色配置:', assistantType);
        return;
    }

    // 更新选中模型信息显示
    updateSelectedModelInfo(assistantType);

    // 切换助手时处理sessionId
    const sessionKey = `${assistantType}_sessionId`;
    let sessionId = localStorage.getItem(sessionKey);

    if (sessionId) {
        // 如果该助手已有sessionId，使用之前的
        currentSessionId = sessionId;
    } else {
        // 如果没有sessionId，生成新的
        const timestamp = Date.now();
        const randomNum = Math.floor(Math.random() * 10000);
        sessionId = `session_${timestamp}_${randomNum}`;
        currentSessionId = sessionId;
        localStorage.setItem(sessionKey, sessionId);
    }

    // 根据当前助手的sessionId重新调用history接口
    loadAssistantHistory(assistantType);
}
```

这个函数负责切换助手时的会话管理，为每个助手类型维护独立的sessionId，并从localStorage中获取或生成新的会话ID。

#### 后端实现：接收会话ID并管理数据

后端接收前端传来的会话ID，通过 Redis 实现会话数据的持久化存储：

```python
async def save_message_to_redis(user_id: str, session_id: str, message: ChatMessage):
    """将消息保存到Redis或内存"""
    try:
        message_data = {
            "role": message.role,
            "content": message.content,
            "timestamp": message.timestamp,
            "image_data": getattr(message, 'image_data', None),
            "image_type": getattr(message, 'image_type', None)
        }

        if REDIS_AVAILABLE and redis_client:
            # Redis存储：高性能，支持数据过期
            conversation_key = get_conversation_key(user_id, session_id)
            redis_client.lpush(conversation_key, json.dumps(message_data))
            redis_client.ltrim(conversation_key, 0, 19)  # 只保留最近20条消息
            redis_client.expire(conversation_key, 86400 * 7)  # 7天过期

            # 更新会话信息
            sessions_key = get_user_sessions_key(user_id)
            session_info = {
                "session_id": session_id,
                "last_message": message.content[:50] + "..." if len(message.content) > 50 else message.content,
                "last_timestamp": message.timestamp
            }
            redis_client.hset(sessions_key, session_id, json.dumps(session_info))
            redis_client.expire(sessions_key, 86400 * 30)  # 30天过期

            logger.info(f"消息已保存到Redis - 用户: {user_id}, 会话: {session_id[:8]}..., 角色: {message.role}")
        else:
            # 内存存储：备用方案
            if user_id not in MEMORY_STORAGE["conversations"]:
                MEMORY_STORAGE["conversations"][user_id] = {}
            if session_id not in MEMORY_STORAGE["conversations"][user_id]:
                MEMORY_STORAGE["conversations"][user_id][session_id] = []

            MEMORY_STORAGE["conversations"][user_id][session_id].append(message_data)
            
            # 限制内存中的消息数量
            if len(MEMORY_STORAGE["conversations"][user_id][session_id]) > 20:
                MEMORY_STORAGE["conversations"][user_id][session_id] = \
                    MEMORY_STORAGE["conversations"][user_id][session_id][-20:]

            logger.info(f"消息已保存到内存 - 用户: {user_id}, 会话: {session_id[:8]}..., 角色: {message.role}")

    except Exception as e:
        logger.error(f"保存消息失败 - 用户: {user_id}, 会话: {session_id[:8]}..., 错误: {e}")
        raise
```

这个函数将消息保存到Redis或内存中，支持双重存储策略，并设置了消息数量限制和过期时间。

### 🔍 功能二：获取历史消息接口

#### 后端 API 设计

我们设计了一个高效的历史消息获取接口：

```python
@app.get("/chat/history")
async def get_chat_history(
    user_id: str = Query(..., description="用户ID"),
    session_id: str = Query(..., description="会话ID")
):
    """获取聊天历史"""
    logger.info(f"获取聊天历史 - 用户: {user_id}, 会话: {session_id[:8]}...")

    try:
        history = await get_conversation_history(user_id, session_id)
        logger.info(f"聊天历史获取成功 - 用户: {user_id}, 会话: {session_id[:8]}..., 消息数: {len(history)}")
        return {
            "session_id": session_id,
            "messages": history,
            "total": len(history)
        }
    except Exception as e:
        logger.error(f"获取聊天历史失败 - 用户: {user_id}, 会话: {session_id[:8]}..., 错误: {e}")
        raise HTTPException(status_code=500, detail="获取聊天历史失败")

async def get_conversation_history(user_id: str, session_id: str) -> List[Dict[str, Any]]:
    """从Redis或内存获取对话历史"""
    try:
        if REDIS_AVAILABLE and redis_client:
            # 从Redis获取
            conversation_key = get_conversation_key(user_id, session_id)
            messages = redis_client.lrange(conversation_key, 0, -1)

            # 反转消息顺序（Redis中是倒序存储的）
            messages.reverse()

            history = [json.loads(msg) for msg in messages]
            logger.info(f"从Redis获取对话历史 - 用户: {user_id}, 会话: {session_id[:8]}..., 消息数量: {len(history)}")
            return history
        else:
            # 从内存获取
            if (user_id in MEMORY_STORAGE["conversations"] and
                session_id in MEMORY_STORAGE["conversations"][user_id]):
                history = MEMORY_STORAGE["conversations"][user_id][session_id]
                logger.info(f"从内存获取对话历史 - 用户: {user_id}, 会话: {session_id[:8]}..., 消息数量: {len(history)}")
                return history
            else:
                logger.info(f"未找到对话历史 - 用户: {user_id}, 会话: {session_id[:8]}...")
                return []

    except Exception as e:
        logger.error(f"获取对话历史失败 - 用户: {user_id}, 会话: {session_id[:8]}..., 错误: {e}")
        return []
```

#### 前端历史消息加载

前端通过异步请求加载和渲染历史消息：

```javascript
/**
 * 加载指定助手的历史消息
 * @param {string} assistantType - 助手类型
 */
async function loadAssistantHistory(assistantType) {
    try {
        // 获取该助手的sessionId
        const sessionId = localStorage.getItem(`${assistantType}_sessionId`);
        if (!sessionId) {
            // 如果没有sessionId，显示欢迎消息
            showWelcomeMessage(assistantType);
            return;
        }

        // 更新当前会话ID
        currentSessionId = sessionId;

        // 清空当前聊天消息
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.innerHTML = '';

        // 显示加载提示
        const loadingMessage = document.createElement('div');
        loadingMessage.className = 'message assistant';
        loadingMessage.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content-wrapper">
                正在加载历史消息...
            </div>
        `;
        chatMessages.appendChild(loadingMessage);

        // 从后端获取历史消息
        const response = await fetch(`/chat/history?session_id=${sessionId}&user_id=${userId}`);
        if (response.ok) {
            const data = await response.json();

            // 清空加载提示
            chatMessages.innerHTML = '';

            // 渲染历史消息
            if (data.messages && data.messages.length > 0) {
                data.messages.forEach(message => {
                    renderHistoryMessage(message);
                });
                console.log(`加载了${data.messages.length}条历史消息`);
            } else {
                // 如果没有历史消息，显示欢迎消息
                showWelcomeMessage(assistantType);
            }

            // 滚动到底部
            scrollToBottom();
        } else {
            console.error('加载历史消息失败:', response.statusText);
            showWelcomeMessage(assistantType);
        }
    } catch (error) {
        console.error('加载助手历史失败:', error);
        showWelcomeMessage(assistantType);
    }
}

/**
 * 渲染历史消息
 * @param {Object} message - 消息对象
 */
function renderHistoryMessage(message) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${message.role}`;

    // 创建头像
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';

    // 如果是assistant消息，设置助手图标
    if (message.role === 'assistant') {
        const icon = getAssistantIcon(currentAssistantType);
        avatarDiv.setAttribute('data-icon', icon);
    }

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content-wrapper';

    // 处理消息内容
    if (message.role === 'assistant') {
        // 对于AI回复，使用Markdown渲染
        renderMarkdownContent(message.content, contentDiv);
    } else {
        // 对于用户消息，检查是否包含图片
        if (message.image_data) {
            // 创建图片元素
            const imageDiv = document.createElement('div');
            imageDiv.className = 'message-image';
            const img = document.createElement('img');
            img.src = `data:${message.image_type};base64,${message.image_data}`;
            img.alt = '用户上传的图片';
            img.style.maxWidth = '300px';
            img.style.borderRadius = '8px';
            imageDiv.appendChild(img);
            contentDiv.appendChild(imageDiv);
        }

        // 添加文本内容
        if (message.content && message.content.trim()) {
            const textDiv = document.createElement('div');
            textDiv.textContent = message.content;
            contentDiv.appendChild(textDiv);
        }
    }

    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
}
```

这个函数从后端获取指定助手的历史消息，并在前端进行渲染显示，支持文本和图片消息的完整展示。

### 💬 功能三：发送消息时携带上下文信息

#### 后端流式对话实现

发送消息时，我们需要获取历史上下文并传递给 AI 模型：

##### 1. 流式聊天接口

```python
@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """流式聊天接口"""
    # 设置默认值
    role = "assistant"
    provider = request.provider
    model = getattr(request, 'model', None)
    
    logger.info(f"流式聊天请求 - 用户: {request.user_id}, 会话: {request.session_id[:8]}..., 角色: {role}, 消息长度: {len(request.message)}, 提供商: {provider}")

    if role not in AI_ROLES:
        logger.warning(f"不支持的AI角色: {role}")
        raise HTTPException(status_code=400, detail="不支持的AI角色")

    return StreamingResponse(
        generate_streaming_response(request.user_id, request.session_id, request.message, role, provider, model, request.image_data, request.image_type),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )
```

这个接口是流式聊天的入口点：
- 接收前端发送的 `ChatRequest` 对象，包含用户ID、会话ID、消息内容等
- 设置默认的AI角色为 "assistant"，从请求中获取AI提供商和模型信息
- 验证AI角色是否在支持的角色列表中
- 返回 `StreamingResponse` 对象，设置SSE（Server-Sent Events）相关的响应头
- 调用 `generate_streaming_response` 函数处理具体的流式响应逻辑

##### 2. 流式响应生成函数


```python
async def generate_streaming_response(user_id: str, session_id: str, user_message: str, role: str = "assistant", provider: Optional[str] = None, model: Optional[str] = None, image_data: Optional[str] = None, image_type: Optional[str] = None):
    """生成流式响应"""
    logger.info(f"开始流式响应 - 用户: {user_id}, 会话: {session_id[:8]}..., 角色: {role}, 消息长度: {len(user_message)}, 提供商: {provider}")

    try:
        # 1. 保存用户消息到Redis
        from ai_providers.base import AIMessage
        user_msg = AIMessage(
            role="user",
            content=user_message,
            timestamp=time.time(),
            image_data=image_data,
            image_type=image_type
        )
        await save_message_to_redis(user_id, session_id, user_msg)

        # 2. 获取对话历史记录
        history = await get_conversation_history(user_id, session_id)

        # 3. 构建系统提示词
        system_prompt = AI_ROLES.get(role, AI_ROLES["assistant"])["prompt"]

        # 4. 构建AI消息对象列表
        ai_messages = []

        # 5. 添加历史消息（限制数量避免上下文过长）
        recent_messages = history[-config.MAX_HISTORY_MESSAGES:] if len(history) > config.MAX_HISTORY_MESSAGES else history
        for msg in recent_messages:
            if msg["role"] in ["user", "assistant"]:
                ai_messages.append(AIMessage(
                    role=msg["role"],
                    content=msg["content"],
                    timestamp=msg.get("timestamp", time.time()),
                    image_data=msg.get("image_data"),
                    image_type=msg.get("image_type")
                ))

        # 6. 调用AI提供商的流式API
        logger.info(f"调用AI流式API - 消息数: {len(ai_messages)}, 提供商: {provider or '默认'}, 模型: {model or '默认'}")

        full_response = ""
        content_only_response = ""  # 只保存 type: 'content' 的内容
        chunk_count = 0
        
        # 7. 处理流式响应
        async for chunk in ai_manager.generate_streaming_response(
            messages=ai_messages,
            provider=provider,
            model=model,
            system_prompt=system_prompt
        ):
            if chunk:
                full_response += chunk
                chunk_count += 1

                # 8. 解析chunk数据，过滤出纯文本内容
                try:
                    if chunk.startswith("data: "):
                        json_str = chunk[6:].strip()  # 移除 "data: " 前缀
                        if json_str:
                            chunk_data = json.loads(json_str)
                            # 只累积 type 为 'content' 的内容用于保存到Redis
                            if chunk_data.get('type') == 'content' and 'content' in chunk_data:
                                content_only_response += chunk_data['content']
                except (json.JSONDecodeError, KeyError) as e:
                    # 如果解析失败，按原来的方式处理（向后兼容）
                    logger.debug(f"解析chunk数据失败，使用原始内容: {e}")
                    content_only_response += chunk

                # 9. 实时推送数据到前端
                yield chunk

        logger.info(f"流式响应完成 - 用户: {user_id}, 会话: {session_id[:8]}..., 块数: {chunk_count}, 总长度: {len(full_response)}, 内容长度: {len(content_only_response)}")

        # 10. 保存AI响应到Redis（只保存纯文本内容）
        ai_msg = ChatMessage(
            role="assistant",
            content=content_only_response,  # 使用过滤后的内容
            timestamp=time.time()
        )
        await save_message_to_redis(user_id, session_id, ai_msg)

        # 11. 发送结束信号
        yield f"data: {json.dumps({'type': 'end', 'session_id': session_id})}\n\n"

    except Exception as e:
        logger.error(f"流式响应错误 - 用户: {user_id}, 会话: {session_id[:8]}..., 错误: {e}")
        error_msg = f"抱歉，服务出现错误：{str(e)}"
        yield f"data: {json.dumps({'content': error_msg, 'type': 'error'})}\n\n"

```

这个函数是流式响应的核心实现，主要包含以下步骤：

1. **保存用户消息**：将用户发送的消息（包括文本和图片）保存到Redis中
2. **获取历史记录**：根据用户ID和会话ID从Redis中获取完整的对话历史
3. **构建系统提示**：根据AI角色获取对应的系统提示词
4. **构建消息列表**：将历史消息转换为AI模型需要的格式
5. **限制历史长度**：只取最近的N条消息，避免上下文过长影响性能
6. **调用AI API**：使用AI管理器调用指定提供商的流式API
7. **处理流式数据**：逐块接收AI响应，实时推送给前端
8. **数据过滤**：从流式数据中提取纯文本内容，用于保存到数据库
9. **实时推送**：使用 `yield` 将数据块实时发送给前端
10. **保存AI响应**：将完整的AI回复保存到Redis中
11. **发送结束信号**：通知前端流式响应已完成

通过这种设计，实现了带有完整上下文的流式对话功能，用户可以看到AI的实时回复，同时所有对话记录都会被持久化保存。


## 总结

本教程通过前端会话ID管理、后端历史消息接口和流式对话上下文传递三个核心技术，实现了支持多助手切换和历史记录持久化的AI聊天应用。