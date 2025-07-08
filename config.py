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

    # AI提供商默认配置
    _DEFAULT_AI_CONFIG = {
        'max_tokens': 1000,
        'temperature': 0.7
    }

    # AI提供商基础信息
    _AI_PROVIDERS_INFO = {
        'openai': {
            'base_url': 'https://api.openai.com/v1',
            'model': 'gpt-4o'
        },
        'deepseek': {
            'base_url': 'https://api.deepseek.com/v1',
            'model': 'deepseek-chat'
        },
        'qianwen': {
            'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
            'model': 'qwen-turbo'
        }
    }

    @classmethod
    def _build_provider_config(cls, provider: str) -> dict:
        """构建单个AI提供商配置"""
        provider_upper = provider.upper()
        provider_info = cls._AI_PROVIDERS_INFO.get(provider, {})

        return {
            'api_key': os.getenv(f'{provider_upper}_API_KEY', ''),
            'base_url': os.getenv(f'{provider_upper}_BASE_URL', provider_info.get('base_url', '')),
            'model': os.getenv(f'{provider_upper}_MODEL', provider_info.get('model', '')),
            'max_tokens': int(os.getenv(f'{provider_upper}_MAX_TOKENS', cls._DEFAULT_AI_CONFIG['max_tokens'])),
            'temperature': float(os.getenv(f'{provider_upper}_TEMPERATURE', cls._DEFAULT_AI_CONFIG['temperature']))
        }

    # AI提供商配置 - 动态生成
    @classmethod
    def _get_ai_providers_config(cls) -> dict:
        """获取所有AI提供商配置"""
        return {provider: cls._build_provider_config(provider) for provider in cls._AI_PROVIDERS_INFO.keys()}

    # 延迟初始化AI提供商配置
    @property
    def AI_PROVIDERS_CONFIG(self) -> dict:
        if not hasattr(self, '_ai_providers_config'):
            self._ai_providers_config = self._get_ai_providers_config()
        return self._ai_providers_config

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
    def get_all_ai_configs(cls) -> dict:
        """获取所有已配置API Key的AI提供商配置"""
        configs = cls._get_ai_providers_config()
        return {name: config for name, config in configs.items() if config.get('api_key')}

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
        """获取已配置API Key的AI提供商列表"""
        return list(cls.get_all_ai_configs().keys())

    @classmethod
    def get_log_file_path(cls) -> str:
        """获取日志文件完整路径"""
        return os.path.join(cls.LOG_DIR, cls.LOG_FILE)


# 创建配置实例
config = Config()
