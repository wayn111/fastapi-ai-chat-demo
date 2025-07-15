#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kimi (Moonshot AI) Provider
"""

from .openai_compatible_provider import OpenAICompatibleProvider

class KimiProvider(OpenAICompatibleProvider):
    """
    Kimi (Moonshot AI) Provider
    API文档: https://platform.moonshot.cn/docs/api-reference
    """

    # Kimi的默认配置
    DEFAULT_BASE_URL = "https://api.moonshot.cn/v1"
    DEFAULT_MODEL = "moonshot-v1-8k"
    PROVIDER_NAME = "kimi"

    # Kimi支持的模型列表
    AVAILABLE_MODELS = [
        "moonshot-v1-8k",
        "moonshot-v1-32k",
        "moonshot-v1-128k",
    ]

    def __init__(self, config: dict):
        """
        初始化Kimi提供商

        Args:
            config: 提供商配置字典
        """
        super().__init__(config)