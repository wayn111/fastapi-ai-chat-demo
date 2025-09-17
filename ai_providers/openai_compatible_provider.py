#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAI兼容提供商基类
为所有使用OpenAI SDK格式的提供商提供通用实现
消除重复代码，简化配置
"""

import logging
from typing import List, Dict, Any, AsyncGenerator
from openai import OpenAI
from .base import BaseAIProvider, AIMessage, AIResponse

logger = logging.getLogger(__name__)

class OpenAICompatibleProvider(BaseAIProvider):
    """
    OpenAI兼容提供商基类
    为所有使用OpenAI SDK格式的提供商提供通用实现
    """

    # 子类需要重写的配置
    DEFAULT_BASE_URL = None
    DEFAULT_MODEL = None
    PROVIDER_NAME = None
    AVAILABLE_MODELS = []

    def __init__(self, config: Dict[str, Any]):
        """
        初始化OpenAI兼容提供商

        Args:
            config: 提供商配置字典，包含api_key、base_url、model等
        """
        super().__init__(config)
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """
        初始化OpenAI兼容客户端
        """
        try:
            api_key = self.get_config_value('api_key')
            if not api_key:
                logger.error(f"{self.get_provider_display_name()}API密钥为空，无法初始化客户端")
                self.client = None
                return

            self.client = OpenAI(
                api_key=api_key,
                base_url=self.get_config_value('base_url', self.DEFAULT_BASE_URL)
            )
            logger.info(f"{self.get_provider_display_name()}客户端初始化成功 - 基础URL: {self.get_config_value('base_url', self.DEFAULT_BASE_URL)}")
        except Exception as e:
            logger.error(f"{self.get_provider_display_name()}客户端初始化失败: {e}")
            self.client = None

    def get_provider_display_name(self) -> str:
        """
        获取提供商显示名称

        Returns:
            str: 提供商显示名称
        """
        return self.PROVIDER_NAME or self.provider_name

    async def generate_response(self, messages: List[AIMessage], **kwargs) -> AIResponse:
        """
        生成AI响应（使用OpenAI SDK格式）

        Args:
            messages: 对话历史消息列表
            **kwargs: 其他参数（temperature、max_tokens等）

        Returns:
            AIResponse: AI响应对象
        """
        try:
            # 格式化消息
            system_prompt = kwargs.get('system_prompt')
            formatted_messages = self.format_messages(messages, system_prompt)

            # 构建请求参数
            request_params = self._build_request_params(formatted_messages, **kwargs)

            logger.info(f"调用{self.get_provider_display_name()}API - 模型: {request_params['model']}, 消息数: {len(formatted_messages)}")

            # 调用API
            response = self.client.chat.completions.create(**request_params)

            # 构建响应对象
            ai_response = AIResponse(
                content=response.choices[0].message.content,
                model=response.model,
                provider=self.provider_name,
                usage={
                    'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
                    'completion_tokens': response.usage.completion_tokens if response.usage else 0,
                    'total_tokens': response.usage.total_tokens if response.usage else 0
                },
                finish_reason=response.choices[0].finish_reason
            )

            logger.info(f"{self.get_provider_display_name()}响应生成成功 - 响应长度: {len(ai_response.content)}")
            return ai_response

        except Exception as e:
            logger.error(f"{self.get_provider_display_name()}响应生成失败: {e}")
            return AIResponse(
                content=f"抱歉，{self.get_provider_display_name()}服务暂时不可用：{str(e)}",
                model=kwargs.get('model', 'unknown'),
                provider=self.provider_name,
                finish_reason='error'
            )

    async def generate_streaming_response(
        self,
        messages: List[AIMessage],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        生成流式AI响应（使用OpenAI SDK格式）

        Args:
            messages: 对话历史消息列表
            **kwargs: 其他参数

        Yields:
            str: 流式响应内容片段
        """
        try:
            # 格式化消息
            system_prompt = kwargs.get('system_prompt')
            formatted_messages = self.format_messages(messages, system_prompt)

            # 构建请求参数
            request_params = self._build_request_params(formatted_messages, stream=True, **kwargs)

            logger.info(f"调用{self.get_provider_display_name()}流式API - 模型: {request_params['model']}, 消息数: {len(formatted_messages)}")

            # 调用流式API
            response = self.client.chat.completions.create(**request_params)

            chunk_count = 0
            import json
            for chunk in response:
                if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content:
                    content = chunk.choices[0].delta.reasoning_content
                    chunk_count += 1
                    # 返回带类型标识的数据，区分深度思考内容
                    yield f"data: {json.dumps({'type': 'reasoning', 'content': content})}\n\n"
                elif hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    chunk_count += 1
                    # 返回带类型标识的数据，区分普通内容
                    yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"

            logger.info(f"{self.get_provider_display_name()}流式响应完成 - 块数: {chunk_count}")

        except Exception as e:
            logger.error(f"{self.get_provider_display_name()}流式响应失败: {e}")
            yield f"抱歉，{self.get_provider_display_name()}流式服务暂时不可用：{str(e)}\n\n"

    def format_messages(self, messages: List[AIMessage], system_prompt: str = None) -> List[Dict[str, Any]]:
        """
        格式化消息为提供商特定格式，支持多模态内容

        Args:
            messages: 消息列表
            system_prompt: 系统提示词

        Returns:
            List[Dict[str, Any]]: 格式化后的消息列表
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
                # 检查是否包含图片数据
                if msg.image_data:
                    # 多模态消息格式
                    content = [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{msg.image_type};base64,{msg.image_data}"
                            }
                        },
                        {
                            "type": "text",
                            "text": msg.content
                        },
                    ]
                    formatted_messages.append({
                        "role": msg.role,
                        "content": content
                    })
                else:
                    # 纯文本消息格式
                    formatted_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })

        return formatted_messages

    def _build_request_params(self, formatted_messages: List[Dict[str, Any]], stream: bool = False, **kwargs) -> Dict[str, Any]:
        """
        构建API请求参数

        Args:
            formatted_messages: 格式化后的消息列表
            stream: 是否为流式请求
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: 请求参数字典
        """
        request_params = {
            'model': kwargs.get('model', self.get_config_value('model', self.DEFAULT_MODEL)),
            'messages': formatted_messages,
            'max_tokens': kwargs.get('max_tokens', self.get_config_value('max_tokens', 1000)),
            'extra_body': {"enable_thinking": True},
            'temperature': kwargs.get('temperature', self.get_config_value('temperature', 0.7))
        }

        if stream:
            request_params['stream'] = True

        return request_params

    def generate_image(self, request: 'ImageGenerationRequest') -> 'ImageGenerationResponse':
        """
        生成图片（默认实现，子类需要重写）
        
        Args:
            request: 图片生成请求
            
        Returns:
            ImageGenerationResponse: 图片生成响应
            
        Raises:
            NotImplementedError: 当前提供商不支持图片生成功能
        """
        raise NotImplementedError(f"{self.__class__.__name__} 不支持图片生成功能")
    
    def validate_config(self) -> bool:
        """
        验证配置是否有效

        Returns:
            bool: 配置是否有效
        """
        api_key = self.get_config_value('api_key')
        if not api_key:
            logger.error(f"{self.get_provider_display_name()}API密钥未配置")
            return False

        if not self.client:
            logger.error(f"{self.get_provider_display_name()}客户端未初始化")
            return False

        try:
            logger.info(f"{self.get_provider_display_name()}配置验证成功")
            return True
        except Exception as e:
            logger.error(f"{self.get_provider_display_name()}配置验证失败: {e}")
            return False

    def get_available_models(self) -> List[str]:
        """
        获取可用的模型列表

        Returns:
            List[str]: 可用模型列表
        """
        logger.info(f"获取{self.get_provider_display_name()}可用模型成功 - 模型数: {len(self.AVAILABLE_MODELS)}")
        return self.AVAILABLE_MODELS.copy()
