#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目配置文件
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基本配置
    app_name: str = "FastAPI AI聊天应用"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Redis配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # OpenAI配置
    openai_api_key: str = "your-openai-api-key"
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-3.5-turbo"
    
    # 对话配置
    max_conversation_length: int = 20  # 最大对话轮数
    conversation_expire_days: int = 7   # 对话过期天数
    session_expire_days: int = 30       # 会话列表过期天数
    
    # API配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# 创建全局配置实例
settings = Settings()