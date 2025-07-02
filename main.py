#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI AI聊天应用演示项目
实现连续多轮对话功能
"""

import json
import time
import uuid
from typing import List, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import redis
from openai import OpenAI

# 应用配置
app = FastAPI(
    title="AI聊天应用演示",
    description="基于FastAPI的AI多轮对话系统",
    version="1.0.0"
)

# Redis连接配置
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)

# OpenAI客户端配置
client = OpenAI(
    api_key="your-api-key-here",
    base_url="https://api.openai.com/v1"
)

# 数据模型定义
class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: str
    content: str
    timestamp: float

class ChatRequest(BaseModel):
    """聊天请求模型"""
    user_id: str
    message: str
    session_id: str = None

class ChatResponse(BaseModel):
    """聊天响应模型"""
    session_id: str
    message: str
    timestamp: float

# AI角色配置
AI_ROLES = {
    "assistant": {
        "name": "智能助手",
        "prompt": "你是一个友善、专业的AI助手，能够帮助用户解答各种问题。请保持礼貌和耐心。"
    },
    "teacher": {
        "name": "AI老师",
        "prompt": "你是一位经验丰富的老师，擅长用简单易懂的方式解释复杂概念，善于启发学生思考。"
    },
    "programmer": {
        "name": "编程专家",
        "prompt": "你是一位资深的程序员，精通多种编程语言和技术栈，能够提供专业的编程建议和解决方案。"
    }
}

def generate_session_id() -> str:
    """生成唯一的会话ID"""
    return str(uuid.uuid4())

def get_conversation_key(user_id: str, session_id: str) -> str:
    """获取对话在Redis中的键名"""
    return f"conversation:{user_id}:{session_id}"

def get_user_sessions_key(user_id: str) -> str:
    """获取用户会话列表在Redis中的键名"""
    return f"user_sessions:{user_id}"

async def save_message_to_redis(user_id: str, session_id: str, message: ChatMessage):
    """将消息保存到Redis"""
    conversation_key = get_conversation_key(user_id, session_id)
    message_data = {
        "role": message.role,
        "content": message.content,
        "timestamp": message.timestamp
    }
    
    # 将消息添加到对话历史
    redis_client.lpush(conversation_key, json.dumps(message_data))
    
    # 设置过期时间（7天）
    redis_client.expire(conversation_key, 7 * 24 * 3600)
    
    # 更新用户会话列表
    sessions_key = get_user_sessions_key(user_id)
    session_info = {
        "session_id": session_id,
        "last_message": message.content[:50] + "..." if len(message.content) > 50 else message.content,
        "last_timestamp": message.timestamp
    }
    redis_client.hset(sessions_key, session_id, json.dumps(session_info))
    redis_client.expire(sessions_key, 30 * 24 * 3600)  # 30天过期

async def get_conversation_history(user_id: str, session_id: str) -> List[Dict[str, Any]]:
    """从Redis获取对话历史"""
    conversation_key = get_conversation_key(user_id, session_id)
    messages = redis_client.lrange(conversation_key, 0, -1)
    
    # 反转消息顺序（Redis中是倒序存储的）
    messages.reverse()
    
    return [json.loads(msg) for msg in messages]

async def generate_ai_response(messages: List[Dict[str, Any]], role: str = "assistant") -> str:
    """调用AI模型生成响应"""
    # 构建系统提示
    system_prompt = AI_ROLES.get(role, AI_ROLES["assistant"])["prompt"]
    
    # 构建消息列表
    openai_messages = [{"role": "system", "content": system_prompt}]
    
    # 添加历史消息（只保留最近10轮对话）
    recent_messages = messages[-20:] if len(messages) > 20 else messages
    for msg in recent_messages:
        if msg["role"] in ["user", "assistant"]:
            openai_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=openai_messages,
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"抱歉，AI服务暂时不可用：{str(e)}"

async def generate_streaming_response(user_id: str, session_id: str, user_message: str, role: str = "assistant"):
    """生成流式响应"""
    try:
        # 保存用户消息
        user_msg = ChatMessage(
            role="user",
            content=user_message,
            timestamp=time.time()
        )
        await save_message_to_redis(user_id, session_id, user_msg)
        
        # 获取对话历史
        history = await get_conversation_history(user_id, session_id)
        
        # 构建系统提示
        system_prompt = AI_ROLES.get(role, AI_ROLES["assistant"])["prompt"]
        
        # 构建消息列表
        openai_messages = [{"role": "system", "content": system_prompt}]
        
        # 添加历史消息
        recent_messages = history[-20:] if len(history) > 20 else history
        for msg in recent_messages:
            if msg["role"] in ["user", "assistant"]:
                openai_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # 调用OpenAI流式API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=openai_messages,
            max_tokens=1000,
            temperature=0.7,
            stream=True
        )
        
        full_response = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                yield f"data: {json.dumps({'content': content, 'type': 'chunk'})}\n\n"
        
        # 保存AI响应
        ai_msg = ChatMessage(
            role="assistant",
            content=full_response,
            timestamp=time.time()
        )
        await save_message_to_redis(user_id, session_id, ai_msg)
        
        # 发送结束信号
        yield f"data: {json.dumps({'type': 'end', 'session_id': session_id})}\n\n"
        
    except Exception as e:
        error_msg = f"抱歉，服务出现错误：{str(e)}"
        yield f"data: {json.dumps({'content': error_msg, 'type': 'error'})}\n\n"

@app.get("/")
async def root():
    """根路径"""
    return {"message": "FastAPI AI聊天应用演示"}

@app.post("/chat/start")
async def start_chat(user_id: str = Query(..., description="用户ID")):
    """开始新的聊天会话"""
    session_id = generate_session_id()
    
    # 初始化会话
    conversation_key = get_conversation_key(user_id, session_id)
    welcome_msg = ChatMessage(
        role="assistant",
        content="你好！我是你的AI助手，有什么可以帮助你的吗？",
        timestamp=time.time()
    )
    
    await save_message_to_redis(user_id, session_id, welcome_msg)
    
    return {
        "session_id": session_id,
        "message": "聊天会话已创建",
        "welcome_message": welcome_msg.content
    }

@app.get("/chat/stream")
async def chat_stream(
    user_id: str = Query(..., description="用户ID"),
    session_id: str = Query(..., description="会话ID"),
    message: str = Query(..., description="用户消息"),
    role: str = Query("assistant", description="AI角色")
):
    """流式聊天接口"""
    if role not in AI_ROLES:
        raise HTTPException(status_code=400, detail="不支持的AI角色")
    
    return StreamingResponse(
        generate_streaming_response(user_id, session_id, message, role),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )

@app.get("/chat/history")
async def get_chat_history(
    user_id: str = Query(..., description="用户ID"),
    session_id: str = Query(..., description="会话ID")
):
    """获取聊天历史"""
    history = await get_conversation_history(user_id, session_id)
    return {
        "session_id": session_id,
        "messages": history,
        "total": len(history)
    }

@app.get("/chat/sessions")
async def get_user_sessions(user_id: str = Query(..., description="用户ID")):
    """获取用户的所有聊天会话"""
    sessions_key = get_user_sessions_key(user_id)
    sessions_data = redis_client.hgetall(sessions_key)
    
    sessions = []
    for session_id, session_info in sessions_data.items():
        session_data = json.loads(session_info)
        sessions.append({
            "session_id": session_id,
            "last_message": session_data["last_message"],
            "last_timestamp": session_data["last_timestamp"],
            "last_time": datetime.fromtimestamp(session_data["last_timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        })
    
    # 按时间倒序排列
    sessions.sort(key=lambda x: x["last_timestamp"], reverse=True)
    
    return {
        "user_id": user_id,
        "sessions": sessions,
        "total": len(sessions)
    }

@app.get("/roles")
async def get_ai_roles():
    """获取可用的AI角色列表"""
    return {
        "roles": [
            {"key": key, "name": value["name"], "description": value["prompt"]}
            for key, value in AI_ROLES.items()
        ]
    }

@app.delete("/chat/session/{session_id}")
async def delete_session(
    session_id: str,
    user_id: str = Query(..., description="用户ID")
):
    """删除聊天会话"""
    conversation_key = get_conversation_key(user_id, session_id)
    sessions_key = get_user_sessions_key(user_id)
    
    # 删除对话历史
    redis_client.delete(conversation_key)
    
    # 从用户会话列表中移除
    redis_client.hdel(sessions_key, session_id)
    
    return {"message": "会话已删除"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)