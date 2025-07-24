#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek提供商实现
支持DeepSeek系列模型
使用OpenAI SDK格式统一接口
"""

from .openai_compatible_provider import OpenAICompatibleProvider

class DeepseekProvider(OpenAICompatibleProvider):
    """DeepSeek提供商实现类 - 使用OpenAI兼容格式"""

    # 提供商配置
    DEFAULT_BASE_URL = 'https://api.deepseek.com/v1'
    DEFAULT_MODEL = 'deepseek-chat'
    PROVIDER_NAME = 'DeepSeek'
    AVAILABLE_MODELS = [
        'deepseek-chat',
        'deepseek-reasoner'
    ]
