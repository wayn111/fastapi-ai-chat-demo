#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI AI聊天应用演示项目
实现连续多轮对话功能
"""

import json
import time
import uuid
import logging
import os
from typing import List, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import redis
from openai import OpenAI
from config import config

# 配置日志系统
# 创建日志目录（如果不存在）
os.makedirs(config.LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=config.get_log_level(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        logging.FileHandler(config.get_log_file_path(), encoding='utf-8')  # 输出到文件
    ]
)

logger = logging.getLogger(__name__)

# 记录应用启动信息
logger.info(f"应用启动 - {config.APP_NAME} v{config.APP_VERSION}")
logger.info(f"调试模式: {config.DEBUG}")
logger.info(f"日志级别: {config.LOG_LEVEL}")
logger.info(f"日志文件: {config.get_log_file_path()}")

# 应用配置
app = FastAPI(
    title=config.APP_NAME,
    description="基于FastAPI和OpenAI的聊天应用",
    version=config.APP_VERSION
)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")

# Redis连接配置
try:
    redis_client = redis.Redis(**config.get_redis_config())
    
    # 测试Redis连接
    redis_client.ping()
    logger.info(f"Redis连接成功 - 主机: {config.REDIS_HOST}:{config.REDIS_PORT}")
    REDIS_AVAILABLE = True
except Exception as e:
    logger.error(f"Redis连接失败: {e}")
    logger.warning("应用将在没有Redis的情况下运行，会话数据将不会持久化")
    redis_client = None
    REDIS_AVAILABLE = False

# 验证配置并初始化OpenAI客户端
try:
    config.validate_config()
    client = OpenAI(**config.get_openai_config())
    logger.info("OpenAI客户端初始化成功")
except ValueError as e:
    logger.error(f"配置验证失败: {e}")
    raise

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

# 对话相关常量（从配置模块获取）
MAX_HISTORY_MESSAGES = config.MAX_HISTORY_MESSAGES
MAX_MESSAGE_LENGTH = config.MAX_MESSAGE_LENGTH
CONVERSATION_EXPIRE_TIME = config.CONVERSATION_EXPIRE_TIME
SESSION_EXPIRE_TIME = config.SESSION_EXPIRE_TIME

# 内存存储（当Redis不可用时使用）
MEMORY_STORAGE = {
    "conversations": {},  # {user_id: {session_id: [messages]}}
    "sessions": {}  # {user_id: {session_id: session_info}}
}

def generate_session_id() -> str:
    """生成唯一的会话ID"""
    session_id = str(uuid.uuid4())
    logger.info(f"生成新会话ID: {session_id}")
    return session_id

def get_conversation_key(user_id: str, session_id: str) -> str:
    """获取对话在Redis中的键名"""
    return f"conversation:{user_id}:{session_id}"

def get_user_sessions_key(user_id: str) -> str:
    """获取用户会话列表在Redis中的键名"""
    return f"user_sessions:{user_id}"

async def save_message_to_redis(user_id: str, session_id: str, message: ChatMessage):
    """将消息保存到Redis或内存"""
    try:
        message_data = {
            "role": message.role,
            "content": message.content,
            "timestamp": message.timestamp
        }
        
        if REDIS_AVAILABLE and redis_client:
            # 使用Redis存储
            conversation_key = get_conversation_key(user_id, session_id)
            
            # 将消息添加到对话历史
            redis_client.lpush(conversation_key, json.dumps(message_data))
            
            # 设置过期时间
            redis_client.expire(conversation_key, CONVERSATION_EXPIRE_TIME)
            
            # 更新用户会话列表
            sessions_key = get_user_sessions_key(user_id)
            session_info = {
                "session_id": session_id,
                "last_message": message.content[:MAX_MESSAGE_LENGTH] + "..." if len(message.content) > MAX_MESSAGE_LENGTH else message.content,
                "last_timestamp": message.timestamp
            }
            redis_client.hset(sessions_key, session_id, json.dumps(session_info))
            redis_client.expire(sessions_key, SESSION_EXPIRE_TIME)
            
            logger.info(f"消息已保存到Redis - 用户: {user_id}, 会话: {session_id[:8]}..., 角色: {message.role}, 内容长度: {len(message.content)}")
        else:
            # 使用内存存储
            if user_id not in MEMORY_STORAGE["conversations"]:
                MEMORY_STORAGE["conversations"][user_id] = {}
            if session_id not in MEMORY_STORAGE["conversations"][user_id]:
                MEMORY_STORAGE["conversations"][user_id][session_id] = []
            
            MEMORY_STORAGE["conversations"][user_id][session_id].append(message_data)
            
            # 更新会话信息
            if user_id not in MEMORY_STORAGE["sessions"]:
                MEMORY_STORAGE["sessions"][user_id] = {}
            
            MEMORY_STORAGE["sessions"][user_id][session_id] = {
                "session_id": session_id,
                "last_message": message.content[:MAX_MESSAGE_LENGTH] + "..." if len(message.content) > MAX_MESSAGE_LENGTH else message.content,
                "last_timestamp": message.timestamp
            }
            
            logger.info(f"消息已保存到内存 - 用户: {user_id}, 会话: {session_id[:8]}..., 角色: {message.role}, 内容长度: {len(message.content)}")
            
    except Exception as e:
        logger.error(f"保存消息失败 - 用户: {user_id}, 会话: {session_id[:8]}..., 错误: {e}")
        raise

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
                logger.info(f"对话历史为空 - 用户: {user_id}, 会话: {session_id[:8]}...")
                return []
    except Exception as e:
        logger.error(f"获取对话历史失败 - 用户: {user_id}, 会话: {session_id[:8]}..., 错误: {e}")
        return []

async def generate_ai_response(messages: List[Dict[str, Any]], role: str = "assistant") -> str:
    """调用AI模型生成响应"""
    logger.info(f"开始生成AI响应 - 角色: {role}, 历史消息数: {len(messages)}")
    
    # 构建系统提示
    system_prompt = AI_ROLES.get(role, AI_ROLES["assistant"])["prompt"]
    
    # 构建消息列表
    openai_messages = [{"role": "system", "content": system_prompt}]
    
    # 添加历史消息（只保留最近的对话）
    recent_messages = messages[-MAX_HISTORY_MESSAGES:] if len(messages) > MAX_HISTORY_MESSAGES else messages
    for msg in recent_messages:
        if msg["role"] in ["user", "assistant"]:
            openai_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    
    try:
        logger.info(f"调用OpenAI API - 消息数: {len(openai_messages)}")
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=openai_messages,
            max_tokens=config.OPENAI_MAX_TOKENS,
            temperature=config.OPENAI_TEMPERATURE
        )
        ai_response = response.choices[0].message.content
        logger.info(f"AI响应生成成功 - 响应长度: {len(ai_response)}")
        return ai_response
    except Exception as e:
        logger.error(f"AI响应生成失败: {e}")
        return f"抱歉，AI服务暂时不可用：{str(e)}"

async def generate_streaming_response(user_id: str, session_id: str, user_message: str, role: str = "assistant"):
    """生成流式响应"""
    logger.info(f"开始流式响应 - 用户: {user_id}, 会话: {session_id[:8]}..., 角色: {role}, 消息长度: {len(user_message)}")
    
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
        recent_messages = history[-MAX_HISTORY_MESSAGES:] if len(history) > MAX_HISTORY_MESSAGES else history
        for msg in recent_messages:
            if msg["role"] in ["user", "assistant"]:
                openai_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # 调用OpenAI流式API
        logger.info(f"调用OpenAI流式API - 消息数: {len(openai_messages)}")
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=openai_messages,
            max_tokens=config.OPENAI_MAX_TOKENS,
            temperature=config.OPENAI_TEMPERATURE,
            stream=True
        )
        
        full_response = ""
        chunk_count = 0
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                chunk_count += 1
                yield f"data: {json.dumps({'content': content, 'type': 'chunk'})}\n\n"
        
        logger.info(f"流式响应完成 - 用户: {user_id}, 会话: {session_id[:8]}..., 块数: {chunk_count}, 总长度: {len(full_response)}")
        
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
        logger.error(f"流式响应错误 - 用户: {user_id}, 会话: {session_id[:8]}..., 错误: {e}")
        error_msg = f"抱歉，服务出现错误：{str(e)}"
        yield f"data: {json.dumps({'content': error_msg, 'type': 'error'})}\n\n"

@app.get("/")
async def root():
    """根路径重定向到聊天界面"""
    logger.info("访问根路径，重定向到聊天界面")
    return RedirectResponse(url="/static/index.html")

@app.get("/api")
async def api_info():
    """API信息"""
    logger.info("获取API信息")
    return {"message": "FastAPI AI聊天应用演示", "version": "1.0.0"}

@app.post("/chat/start")
async def start_chat(user_id: str = Query(..., description="用户ID")):
    """开始新的聊天会话"""
    logger.info(f"开始新聊天会话 - 用户: {user_id}")
    
    try:
        session_id = generate_session_id()
        
        # 初始化会话
        conversation_key = get_conversation_key(user_id, session_id)
        welcome_msg = ChatMessage(
            role="assistant",
            content="你好！我是你的AI助手，有什么可以帮助你的吗？",
            timestamp=time.time()
        )
        
        await save_message_to_redis(user_id, session_id, welcome_msg)
        
        logger.info(f"聊天会话创建成功 - 用户: {user_id}, 会话: {session_id[:8]}...")
        return {
            "session_id": session_id,
            "message": "聊天会话已创建",
            "welcome_message": welcome_msg.content
        }
    except Exception as e:
        logger.error(f"创建聊天会话失败 - 用户: {user_id}, 错误: {e}")
        raise HTTPException(status_code=500, detail="创建会话失败")

@app.get("/chat/stream")
async def chat_stream(
    user_id: str = Query(..., description="用户ID"),
    session_id: str = Query(..., description="会话ID"),
    message: str = Query(..., description="用户消息"),
    role: str = Query("assistant", description="AI角色")
):
    """流式聊天接口"""
    logger.info(f"流式聊天请求 - 用户: {user_id}, 会话: {session_id[:8]}..., 角色: {role}, 消息长度: {len(message)}")
    
    if role not in AI_ROLES:
        logger.warning(f"不支持的AI角色: {role}")
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

@app.get("/chat/sessions")
async def get_user_sessions(user_id: str = Query(..., description="用户ID")):
    """获取用户的所有聊天会话"""
    logger.info(f"获取用户会话列表 - 用户: {user_id}")
    
    try:
        sessions = []
        
        if REDIS_AVAILABLE and redis_client:
            # 从Redis获取
            sessions_key = get_user_sessions_key(user_id)
            sessions_data = redis_client.hgetall(sessions_key)
            
            for session_id, session_info in sessions_data.items():
                session_data = json.loads(session_info)
                sessions.append({
                    "session_id": session_id,
                    "last_message": session_data["last_message"],
                    "last_timestamp": session_data["last_timestamp"],
                    "last_time": datetime.fromtimestamp(session_data["last_timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                })
        else:
            # 从内存获取
            if user_id in MEMORY_STORAGE["sessions"]:
                for session_id, session_data in MEMORY_STORAGE["sessions"][user_id].items():
                    sessions.append({
                        "session_id": session_id,
                        "last_message": session_data["last_message"],
                        "last_timestamp": session_data["last_timestamp"],
                        "last_time": datetime.fromtimestamp(session_data["last_timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                    })
        
        # 按时间倒序排列
        sessions.sort(key=lambda x: x["last_timestamp"], reverse=True)
        
        logger.info(f"用户会话列表获取成功 - 用户: {user_id}, 会话数: {len(sessions)}")
        return {
            "user_id": user_id,
            "sessions": sessions,
            "total": len(sessions)
        }
    except Exception as e:
        logger.error(f"获取用户会话列表失败 - 用户: {user_id}, 错误: {e}")
        raise HTTPException(status_code=500, detail="获取会话列表失败")

@app.get("/roles")
async def get_ai_roles():
    """获取可用的AI角色列表"""
    logger.info("获取AI角色列表")
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
    logger.info(f"删除聊天会话 - 用户: {user_id}, 会话: {session_id[:8]}...")
    
    try:
        if REDIS_AVAILABLE and redis_client:
            # 从Redis删除
            conversation_key = get_conversation_key(user_id, session_id)
            sessions_key = get_user_sessions_key(user_id)
            
            # 删除对话历史
            redis_client.delete(conversation_key)
            
            # 从会话列表中删除
            redis_client.hdel(sessions_key, session_id)
            
            logger.info(f"会话已从Redis删除 - 用户: {user_id}, 会话: {session_id[:8]}...")
        else:
            # 从内存删除
            if (user_id in MEMORY_STORAGE["conversations"] and 
                session_id in MEMORY_STORAGE["conversations"][user_id]):
                del MEMORY_STORAGE["conversations"][user_id][session_id]
                
                # 如果用户没有其他会话，删除用户记录
                if not MEMORY_STORAGE["conversations"][user_id]:
                    del MEMORY_STORAGE["conversations"][user_id]
            
            if (user_id in MEMORY_STORAGE["sessions"] and 
                session_id in MEMORY_STORAGE["sessions"][user_id]):
                del MEMORY_STORAGE["sessions"][user_id][session_id]
                
                # 如果用户没有其他会话，删除用户记录
                if not MEMORY_STORAGE["sessions"][user_id]:
                    del MEMORY_STORAGE["sessions"][user_id]
            
            logger.info(f"会话已从内存删除 - 用户: {user_id}, 会话: {session_id[:8]}...")
        
        return {"message": "会话删除成功", "session_id": session_id}
        
    except Exception as e:
        logger.error(f"删除会话失败 - 用户: {user_id}, 会话: {session_id[:8]}..., 错误: {e}")
        raise HTTPException(status_code=500, detail="删除会话失败")

@app.delete("/chat/history/{session_id}")
async def clear_conversation_history(
    session_id: str,
    user_id: str = Query(..., description="用户ID")
):
    """清除指定会话的对话历史，但保留会话记录"""
    logger.info(f"清除对话历史 - 用户: {user_id}, 会话: {session_id[:8]}...")
    
    try:
        if REDIS_AVAILABLE and redis_client:
            # 从Redis清除对话历史
            conversation_key = get_conversation_key(user_id, session_id)
            
            # 删除对话历史
            redis_client.delete(conversation_key)
            
            # 更新会话信息，保留会话但清空最后消息
            sessions_key = get_user_sessions_key(user_id)
            session_info = {
                "session_id": session_id,
                "last_message": "对话历史已清除",
                "last_timestamp": time.time()
            }
            redis_client.hset(sessions_key, session_id, json.dumps(session_info))
            redis_client.expire(sessions_key, SESSION_EXPIRE_TIME)
            
            logger.info(f"对话历史已从Redis清除 - 用户: {user_id}, 会话: {session_id[:8]}...")
        else:
            # 从内存清除对话历史
            if (user_id in MEMORY_STORAGE["conversations"] and 
                session_id in MEMORY_STORAGE["conversations"][user_id]):
                # 清空对话历史
                MEMORY_STORAGE["conversations"][user_id][session_id] = []
            
            # 更新会话信息
            if user_id not in MEMORY_STORAGE["sessions"]:
                MEMORY_STORAGE["sessions"][user_id] = {}
            
            MEMORY_STORAGE["sessions"][user_id][session_id] = {
                "session_id": session_id,
                "last_message": "对话历史已清除",
                "last_timestamp": time.time()
            }
            
            logger.info(f"对话历史已从内存清除 - 用户: {user_id}, 会话: {session_id[:8]}...")
        
        return {"message": "对话历史清除成功", "session_id": session_id}
        
    except Exception as e:
        logger.error(f"清除对话历史失败 - 用户: {user_id}, 会话: {session_id[:8]}..., 错误: {e}")
        raise HTTPException(status_code=500, detail="清除对话历史失败")
