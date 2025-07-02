#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
集中管理应用的所有配置项
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """应用配置类"""
    
    # 应用配置
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    APP_NAME: str = os.getenv('APP_NAME', 'AI聊天应用演示')
    APP_VERSION: str = os.getenv('APP_VERSION', '1.0.0')
    
    # Redis配置
    REDIS_HOST: str = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT: int = int(os.getenv('REDIS_PORT', 6379))
    REDIS_PASSWORD: Optional[str] = os.getenv('REDIS_PASSWORD')
    REDIS_DB: int = int(os.getenv('REDIS_DB', 0))
    
    # Redis过期时间配置（秒）
    CONVERSATION_EXPIRE_TIME: int = int(os.getenv('CONVERSATION_EXPIRE_TIME', 7 * 24 * 3600))  # 7天
    SESSION_EXPIRE_TIME: int = int(os.getenv('SESSION_EXPIRE_TIME', 30 * 24 * 3600))  # 30天
    
    # OpenAI配置
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    OPENAI_BASE_URL: str = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    OPENAI_MODEL: str = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    OPENAI_MAX_TOKENS: int = int(os.getenv('OPENAI_MAX_TOKENS', 1000))
    OPENAI_TEMPERATURE: float = float(os.getenv('OPENAI_TEMPERATURE', 0.7))
    
    # 对话配置
    MAX_HISTORY_MESSAGES: int = int(os.getenv('MAX_HISTORY_MESSAGES', 20))  # 最大历史消息数
    MAX_MESSAGE_LENGTH: int = int(os.getenv('MAX_MESSAGE_LENGTH', 50))  # 会话列表中显示的最大消息长度
    
    # 日志配置
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'DEBUG' if DEBUG else 'INFO')
    LOG_DIR: str = os.getenv('LOG_DIR', 'logs')
    LOG_FILE: str = os.getenv('LOG_FILE', 'app.log')
    
    # 服务器配置
    HOST: str = os.getenv('HOST', '0.0.0.0')
    PORT: int = int(os.getenv('PORT', 8000))
    
    @classmethod
    def get_redis_config(cls) -> dict:
        """获取Redis连接配置"""
        config = {
            'host': cls.REDIS_HOST,
            'port': cls.REDIS_PORT,
            'db': cls.REDIS_DB,
            'decode_responses': True
        }
        
        if cls.REDIS_PASSWORD:
            config['password'] = cls.REDIS_PASSWORD
            
        return config
    
    @classmethod
    def get_openai_config(cls) -> dict:
        """获取OpenAI客户端配置"""
        return {
            'api_key': cls.OPENAI_API_KEY,
            'base_url': cls.OPENAI_BASE_URL
        }
    
    @classmethod
    def get_log_level(cls) -> int:
        """获取日志级别"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        return level_map.get(cls.LOG_LEVEL.upper(), logging.INFO)
    
    @classmethod
    def validate_config(cls) -> None:
        """验证必需的配置项"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY环境变量未设置")
    
    @classmethod
    def get_log_file_path(cls) -> str:
        """获取日志文件完整路径"""
        return os.path.join(cls.LOG_DIR, cls.LOG_FILE)

# 创建配置实例
config = Config()