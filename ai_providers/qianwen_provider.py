#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通义千问提供商实现
支持阿里云通义千问系列模型
使用OpenAI SDK格式统一接口
"""

from .openai_compatible_provider import OpenAICompatibleProvider

class QianwenProvider(OpenAICompatibleProvider):
    """通义千问提供商实现类 - 使用OpenAI兼容格式"""

    # 提供商配置
    DEFAULT_BASE_URL = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
    DEFAULT_MODEL = 'qwen-turbo'
    PROVIDER_NAME = '通义千问'
    AVAILABLE_MODELS = [
        'qwen-plus',
    ]
