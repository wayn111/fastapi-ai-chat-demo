#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
集中管理应用的所有配置项
"""

import os
import logging
from typing import Optional, List
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

    # AI提供商配置
    DEFAULT_AI_PROVIDER: str = os.getenv('DEFAULT_AI_PROVIDER', 'deepseek')

    # AI提供商配置 - 统一格式
    AI_PROVIDERS_CONFIG = {
        'openai': {
            'api_key': os.getenv('OPENAI_API_KEY', ''),
            'base_url': os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1'),
            'model': os.getenv('OPENAI_MODEL', 'gpt-4o'),
            'max_tokens': int(os.getenv('OPENAI_MAX_TOKENS', 1000)),
            'temperature': float(os.getenv('OPENAI_TEMPERATURE', 0.7))
        },
        'deepseek': {
            'api_key': os.getenv('DEEPSEEK_API_KEY', ''),
            'base_url': os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1'),
            'model': os.getenv('DEEPSEEK_MODEL', 'deepseek-chat'),
            'max_tokens': int(os.getenv('DEEPSEEK_MAX_TOKENS', 1000)),
            'temperature': float(os.getenv('DEEPSEEK_TEMPERATURE', 0.7))
        },
        'qianwen': {
            'api_key': os.getenv('QIANWEN_API_KEY', ''),
            'base_url': os.getenv('QIANWEN_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1'),
            'model': os.getenv('QIANWEN_MODEL', 'qwen-turbo'),
            'max_tokens': int(os.getenv('QIANWEN_MAX_TOKENS', 1000)),
            'temperature': float(os.getenv('QIANWEN_TEMPERATURE', 0.7))
        }
    }
    
    # 向后兼容的属性访问
    @classmethod
    def get_openai_api_key(cls) -> str:
        return cls.AI_PROVIDERS_CONFIG['openai']['api_key']
    
    @classmethod
    def get_deepseek_api_key(cls) -> str:
        return cls.AI_PROVIDERS_CONFIG['deepseek']['api_key']
    
    @classmethod
    def get_qianwen_api_key(cls) -> str:
        return cls.AI_PROVIDERS_CONFIG['qianwen']['api_key']
    
    # 向后兼容的属性
    OPENAI_API_KEY = property(lambda self: self.AI_PROVIDERS_CONFIG['openai']['api_key'])
    DEEPSEEK_API_KEY = property(lambda self: self.AI_PROVIDERS_CONFIG['deepseek']['api_key'])
    QIANWEN_API_KEY = property(lambda self: self.AI_PROVIDERS_CONFIG['qianwen']['api_key'])



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
    def get_provider_config(cls, provider_name: str) -> dict:
        """获取指定AI提供商配置"""
        return cls.AI_PROVIDERS_CONFIG.get(provider_name, {})
    
    @classmethod
    def get_all_ai_configs(cls) -> dict:
        """获取所有AI提供商配置"""
        return {name: config for name, config in cls.AI_PROVIDERS_CONFIG.items() if config.get('api_key')}
    
    # 向后兼容的方法
    @classmethod
    def get_deepseek_config(cls) -> dict:
        """获取DeepSeek客户端配置"""
        return cls.get_provider_config('deepseek')

    @classmethod
    def get_qianwen_config(cls) -> dict:
        """获取通义千问客户端配置"""
        return cls.get_provider_config('qianwen')

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
        # 检查是否至少配置了一个AI提供商
        providers_configured = cls.get_configured_providers()

        if not providers_configured:
            raise ValueError("至少需要配置一个AI提供商的API密钥")

        # 检查默认提供商是否已配置
        if cls.DEFAULT_AI_PROVIDER not in providers_configured:
            # 如果默认提供商未配置，使用第一个已配置的提供商
            cls.DEFAULT_AI_PROVIDER = providers_configured[0]
            print(f"警告: 默认AI提供商未配置或无效，自动设置为: {cls.DEFAULT_AI_PROVIDER}")

    @classmethod
    def get_configured_providers(cls) -> List[str]:
        """获取已配置的AI提供商列表"""
        return [name for name, config in cls.AI_PROVIDERS_CONFIG.items() if config.get('api_key')]

    @classmethod
    def get_log_file_path(cls) -> str:
        """获取日志文件完整路径"""
        return os.path.join(cls.LOG_DIR, cls.LOG_FILE)

# 创建配置实例
config = Config()
