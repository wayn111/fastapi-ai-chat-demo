# FastAPI开发AI应用三：添加深度思考功能

本文将深入讲解如何在 FastAPI AI 聊天应用中实现深度思考功能，让 AI 能够展示其推理过程，提升用户对 AI 回答的理解和信任度。通过本教程，你将学会如何处理 AI 模型的 reasoning_content 输出，并在前端优雅地展示思考过程。

> 📖 项目地址：<https://github.com/wayn111/fastapi-ai-chat-demo>
> 
> 温馨提示：本文全文约六千字，看完约需 10 分钟。

## 项目概述

想象一下，当你向 AI 提出一个复杂问题时，AI 不仅给出答案，还能展示它的思考过程——就像一个学生在黑板上展示解题步骤一样。这就是我们要实现的深度思考功能！用户可以看到 AI 如何分析问题、权衡不同选项、最终得出结论，这种透明度大大提升了 AI 回答的可信度和教育价值。

### 核心功能

- **思考过程可视化**：实时展示 AI 的推理步骤和思考逻辑
- **双重内容流**：同时处理思考内容（reasoning_content）和最终回答（content）
- **差异化展示**：思考内容和最终回答采用不同的视觉样式
- **流式渲染**：思考过程和回答都支持实时流式显示
- **Markdown 支持**：思考内容支持完整的 Markdown 格式渲染

### 技术栈

- **后端框架**：FastAPI（高性能异步 Web 框架）
- **AI 集成**：OpenAI SDK（支持 reasoning_content 的模型）
- **流式协议**：Server-Sent Events（SSE）
- **前端渲染**：Marked.js + Highlight.js（Markdown 和代码高亮）
- **样式设计**：CSS3（差异化视觉效果）

### 🤖 支持的模型

| 模型系列 | 代表模型 | 思考能力 | 特色 |
|---------|---------|----------|------|
| **OpenAI o1** | o1-preview, o1-mini | 强推理 | 数学、编程、逻辑推理 |
| **DeepSeek R1** | deepseek-reasoner | 深度思考 | 中文推理、多步骤分析 |
| **Qwen QwQ** | qwq-32b-preview | 问题分解 | 结构化思维、步骤清晰 |

## 🏗️ 核心架构设计

### 🎯 设计理念

深度思考功能的实现基于三个核心设计原则：

**1. 内容分离原则**
思考内容（reasoning_content）和最终回答（content）是两个独立的数据流，需要分别处理和展示。这样可以让用户清楚地区分 AI 的思考过程和最终结论。

**2. 实时展示原则**
思考过程应该实时展示，让用户能够跟随 AI 的思维轨迹。这不仅提升了用户体验，还增加了 AI 回答的透明度和可信度。

**3. 视觉区分原则**
思考内容和最终回答需要采用不同的视觉样式，让用户能够一眼区分两种不同类型的内容。

### 🏛️ 架构层次

深度思考功能的架构分为三个清晰的层次：

#### 1. 后端处理层（AI Provider）

这一层负责处理 AI 模型的原始输出，识别和分离 reasoning_content 和 content：

```python
async def generate_streaming_response(
    self,
    messages: List[AIMessage],
    **kwargs
) -> AsyncGenerator[str, None]:
    """
    生成流式AI响应，支持深度思考内容
    
    Args:
        messages: 对话历史消息列表
        **kwargs: 其他参数
    
    Yields:
        str: 流式响应内容片段，包含类型标识
    """
    try:
        # 格式化消息并构建请求参数
        system_prompt = kwargs.get('system_prompt')
        formatted_messages = self.format_messages(messages, system_prompt)
        request_params = self._build_request_params(formatted_messages, stream=True, **kwargs)
        
        logger.info(f"调用{self.get_provider_display_name()}流式API - 模型: {request_params['model']}")
        
        # 调用流式API
        response = self.client.chat.completions.create(**request_params)
        
        chunk_count = 0
        import json
        
        for chunk in response:
            # 处理深度思考内容
            if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content:
                content = chunk.choices[0].delta.reasoning_content
                chunk_count += 1
                # 返回带类型标识的思考内容
                yield f"data: {json.dumps({'type': 'reasoning', 'content': content})}\n\n"
            
            # 处理普通回答内容
            elif hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                chunk_count += 1
                # 返回带类型标识的回答内容
                yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
        
        logger.info(f"{self.get_provider_display_name()}流式响应完成 - 块数: {chunk_count}")
        
    except Exception as e:
        logger.error(f"{self.get_provider_display_name()}流式响应失败: {e}")
        yield f"抱歉，{self.get_provider_display_name()}流式服务暂时不可用：{str(e)}"
```

**核心特点：**
- **双重检测**：同时检测 reasoning_content 和 content 字段
- **类型标识**：为每个数据块添加 type 字段，便于前端区分处理
- **JSON 格式**：使用结构化的 JSON 格式传输数据
- **错误处理**：完善的异常处理机制

#### 2. 接口传输层（FastAPI）

这一层负责将处理后的数据通过 SSE 协议传输给前端：

```python
@app.get("/chat/stream")
async def chat_stream(
    user_id: str = Query(..., description="用户ID"),
    session_id: str = Query(..., description="会话ID"),
    message: str = Query(..., description="用户消息"),
    role: str = Query("assistant", description="AI角色"),
    provider: Optional[str] = Query(None, description="AI提供商"),
    model: Optional[str] = Query(None, description="AI模型")
):
    """
    流式聊天接口，支持深度思考功能
    
    Returns:
        StreamingResponse: SSE格式的流式响应
    """
    logger.info(f"流式聊天请求 - 用户: {user_id}, 会话: {session_id[:8]}..., 提供商: {provider}")
    
    if role not in AI_ROLES:
        logger.warning(f"不支持的AI角色: {role}")
        raise HTTPException(status_code=400, detail="不支持的AI角色")
    
    return StreamingResponse(
        generate_streaming_response(user_id, session_id, message, role, provider, model),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )
```

**关键配置：**
- **media_type**: "text/event-stream" 启用 SSE 协议
- **Cache-Control**: "no-cache" 禁用缓存确保实时性
- **Connection**: "keep-alive" 保持连接活跃

#### 3. 前端展示层（JavaScript + CSS）

这一层负责接收数据并进行差异化展示：

```javascript
// 项目中的实际前端处理逻辑
if (data.type === 'chunk' || data.type === 'content' || data.type === 'reasoning') {
    if (data.type === 'reasoning') {
        // 处理深度思考内容
        if (!reasoningElement) {
            reasoningElement = document.createElement('div');
            reasoningElement.className = 'message-content reasoning-content';
            
            // 创建reasoning-body容器
            const reasoningBody = document.createElement('div');
            reasoningBody.className = 'reasoning-body';
            reasoningElement.appendChild(reasoningBody);
            
            // 将reasoning元素添加到消息容器的content wrapper中
            const contentWrapper = messageContainer.querySelector('.message-content-wrapper');
            contentWrapper.appendChild(reasoningElement);
        }
        reasoningMessage += data.content;
        
        // 实时渲染思考内容
        const reasoningBody = reasoningElement.querySelector('.reasoning-body');
        
        // 简单的Markdown检测和渲染
        if (reasoningMessage.includes('```') || 
            reasoningMessage.includes('**') || 
            reasoningMessage.includes('##') || 
            reasoningMessage.includes('- ') || 
            reasoningMessage.includes('1. ')) {
            try {
                reasoningBody.innerHTML = marked.parse(reasoningMessage);
                reasoningBody.querySelectorAll('pre code').forEach((block) => {
                    hljs.highlightElement(block);
                });
            } catch (error) {
                reasoningBody.textContent = reasoningMessage;
            }
        } else {
            reasoningBody.textContent = reasoningMessage;
        }
    } else {
        // 处理普通内容（content或chunk类型）
        if (!contentElement) {
            contentElement = document.createElement('div');
            contentElement.className = 'message-content';
            
            const contentWrapper = messageContainer.querySelector('.message-content-wrapper');
            contentWrapper.appendChild(contentElement);
        }
        
        contentMessage += data.content;
        
        // 实时渲染普通内容
        if (contentMessage.includes('```') || 
            contentMessage.includes('**') || 
            contentMessage.includes('##') || 
            contentMessage.includes('- ') || 
            contentMessage.includes('1. ')) {
            try {
                contentElement.innerHTML = marked.parse(contentMessage);
                contentElement.querySelectorAll('pre code').forEach((block) => {
                    hljs.highlightElement(block);
                });
            } catch (error) {
                contentElement.textContent = contentMessage;
            }
        } else {
            contentElement.textContent = contentMessage;
        }
    }
    
    scrollToBottom();
}
```

**前端处理特点：**
- **动态元素创建**：根据数据类型动态创建不同的DOM元素
- **实时渲染**：支持Markdown和代码高亮的实时渲染
- **智能检测**：自动检测内容格式并选择合适的渲染方式
- **用户体验**：自动滚动到最新内容

### 🎨 视觉设计

深度思考功能的视觉设计采用了差异化的样式策略：

```css
/* 深度思考内容样式 - 引用文本风格 */
.message.assistant .message-content.reasoning-content {
    background: #f8fafc;           /* 浅灰背景，区别于普通回答 */
    padding: 0;
    color: #64748b;                /* 较淡的文字颜色 */
    position: relative;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    line-height: 2;                /* 较大的行高，便于阅读 */
    margin-bottom: 15px;           /* 与普通回答保持间距 */
}

.message.assistant .message-content.reasoning-content .reasoning-body {
    padding: 16px 20px;            /* 内边距确保内容不贴边 */
}

.message.assistant .message-content.reasoning-content p {
    margin: 0 0 8px 0;
    line-height: 1.6;
}

.message.assistant .message-content.reasoning-content code {
    background: #e2e8f0;          /* 代码块背景色 */
    color: #475569;                /* 代码文字颜色 */
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 0.9em;
}
```

**设计理念：**
- **颜色区分**：思考内容使用浅灰背景和较淡的文字颜色
- **间距设计**：合理的内外边距确保内容层次清晰
- **字体选择**：代码部分使用等宽字体提升可读性
- **阴影效果**：轻微的阴影增加视觉层次感

## 🔧 核心功能实现

### 📡 数据流处理

深度思考功能的核心在于正确处理两种不同类型的数据流。在项目的实际实现中，后端通过检测 `reasoning_content` 和 `content` 字段来区分不同类型的内容，前端则根据 `type` 字段进行差异化渲染。

#### 1. 后端数据处理

在 `main.py` 的流式响应处理中，系统会解析每个数据块并只保存 `type: 'content'` 的内容到 Redis：

```python
# 解析chunk数据，只保留 type: 'content' 的内容到Redis
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
```

#### 2. 前端智能渲染

前端使用简单而有效的 Markdown 检测逻辑来决定渲染方式：

```javascript
// 检测是否包含Markdown格式
if (reasoningMessage.includes('```') || 
    reasoningMessage.includes('**') || 
    reasoningMessage.includes('##') || 
    reasoningMessage.includes('- ') || 
    reasoningMessage.includes('1. ')) {
    // 使用Markdown渲染
    reasoningBody.innerHTML = marked.parse(reasoningMessage);
    reasoningBody.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
    });
} else {
    // 使用纯文本渲染
    reasoningBody.textContent = reasoningMessage;
}
```

## 📚 总结

本文详细介绍了如何在 FastAPI AI 聊天应用中实现深度思考功能。通过分离处理 reasoning_content 和 content 两种数据流，我们成功构建了一个能够展示 AI 思考过程的透明化聊天系统。核心实现包括后端的双重内容检测与分离、SSE 协议的实时数据传输、前端的差异化渲染。项目采用了简洁而实用的技术方案：后端通过检测 OpenAI SDK 返回的 reasoning_content 字段来识别思考内容，前端使用简单的字符串匹配来检测 Markdown 格式并进行相应渲染。这套架构不仅提升了用户对 AI 回答的理解和信任度，还为教育场景下的 AI 应用提供了重要的技术基础。通过合理的视觉设计，用户可以清晰地看到 AI 的推理步骤，体验更加透明和可信的人工智能交互。