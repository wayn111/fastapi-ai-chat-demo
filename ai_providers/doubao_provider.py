#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Doubao提供商实现
支持Doubao系列模型
使用OpenAI SDK格式统一接口
"""

from .openai_compatible_provider import OpenAICompatibleProvider

class DoubaoProvider(OpenAICompatibleProvider):
    """Doubao提供商实现类 - 使用OpenAI兼容格式"""

    # 提供商配置
    DEFAULT_BASE_URL = 'https://ark.cn-beijing.volces.com/api/v3'
    DEFAULT_MODEL = 'doubao-seed-1-6-250615'
    PROVIDER_NAME = 'Doubao'
    AVAILABLE_MODELS = [
        'doubao-seed-1-6-250615',
    ]
