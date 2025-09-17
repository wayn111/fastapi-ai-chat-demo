#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI提供商抽象基类
定义所有AI提供商必须实现的接口
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncGenerator, Optional
from dataclasses import dataclass

@dataclass
class AIMessage:
    """AI消息数据类"""
    role: str
    content: str
    timestamp: float
    image_data: Optional[str] = None  # Base64编码的图片数据
    image_type: Optional[str] = None  # 图片类型 (jpeg, png, gif)

@dataclass
class AIResponse:
    """AI响应数据类"""
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None

@dataclass
class ImageGenerationRequest:
    """图片生成请求数据类"""
    prompt: str
    size: Optional[str] = "1024x1024"  # 图片尺寸
    quality: Optional[str] = "standard"  # 图片质量
    style: Optional[str] = None  # 图片风格
    response_format: Optional[str] = "url"  # 响应格式: url 或 b64_json
    image_data: Optional[str] = None  # 用于图片生成图片的输入图片URL
    image_type: Optional[str] = None  # 用于图片生成图片的输入图片URL
    watermark: Optional[bool] = True  # 是否添加水印

@dataclass
class ImageGenerationResponse:
    """图片生成响应数据类"""
    url: Optional[str] = None  # 图片URL
    b64_json: Optional[str] = None  # Base64编码的图片数据
    revised_prompt: Optional[str] = None  # 修订后的提示词
    model: Optional[str] = None  # 使用的模型
    provider: Optional[str] = None  # 提供商

class BaseAIProvider(ABC):
    """AI提供商抽象基类"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化AI提供商

        Args:
            config: 提供商配置字典
        """
        self.config = config
        self.provider_name = self.__class__.__name__.replace('Provider', '').lower()

    @abstractmethod
    async def generate_response(self, messages: List[AIMessage], **kwargs) -> AIResponse:
        """
        生成AI响应

        Args:
            messages: 对话历史消息列表
            **kwargs: 其他参数（如temperature、max_tokens等）

        Returns:
            AIResponse: AI响应对象
        """
        pass

    @abstractmethod
    async def generate_streaming_response(
        self,
        messages: List[AIMessage],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        生成流式AI响应

        Args:
            messages: 对话历史消息列表
            **kwargs: 其他参数

        Yields:
            str: 流式响应内容片段
        """
        pass

    @abstractmethod
    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResponse:
        """
        生成图片

        Args:
            request: 图片生成请求

        Returns:
            ImageGenerationResponse: 图片生成响应
        """
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """
        验证配置是否有效

        Returns:
            bool: 配置是否有效
        """
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        获取可用的模型列表

        Returns:
            List[str]: 可用模型列表
        """
        pass

    def get_provider_name(self) -> str:
        """
        获取提供商名称

        Returns:
            str: 提供商名称
        """
        return self.provider_name

    def format_messages(self, messages: List[AIMessage], system_prompt: str = None) -> List[Dict[str, str]]:
        """
        格式化消息为提供商特定格式

        Args:
            messages: 消息列表
            system_prompt: 系统提示词

        Returns:
            List[Dict[str, str]]: 格式化后的消息列表
        """
        formatted_messages = []

        # 添加系统提示
        if system_prompt:
            formatted_messages.append({
                "role": "system",
                "content": system_prompt
            })

        # 添加历史消息
        for msg in messages:
            if msg.role in ["user", "assistant"]:
                formatted_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        return formatted_messages

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            Any: 配置值
        """
        return self.config.get(key, default)
