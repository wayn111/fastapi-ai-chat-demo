#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAI提供商实现
支持OpenAI GPT系列模型
使用OpenAI SDK格式统一接口
"""

from .openai_compatible_provider import OpenAICompatibleProvider

class OpenAIProvider(OpenAICompatibleProvider):
    """OpenAI提供商实现类 - 使用OpenAI兼容格式"""

    # 提供商配置
    DEFAULT_BASE_URL = 'https://api.openai.com/v1'
    DEFAULT_MODEL = 'gpt-4o'
    PROVIDER_NAME = 'OpenAI'
    AVAILABLE_MODELS = [
        'gpt-4o-mini',
    ]
