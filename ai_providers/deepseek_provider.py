#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通义千问提供商实现
支持阿里云通义千问系列模型
使用OpenAI SDK格式统一接口
"""

import json
import logging
from typing import List, Dict, Any, AsyncGenerator
from openai import OpenAI
from .base import BaseAIProvider, AIMessage, AIResponse

logger = logging.getLogger(__name__)

class QianwenProvider(BaseAIProvider):
    """通义千问提供商实现类 - 使用OpenAI SDK格式"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化通义千问提供商
        
        Args:
            config: 通义千问配置字典，包含api_key、base_url、model等
        """
        super().__init__(config)
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """
        初始化通义千问客户端（使用OpenAI SDK格式）
        """
        try:
            api_key = self.get_config_value('api_key')
            if not api_key:
                logger.error("通义千问API密钥为空，无法初始化客户端")
                self.client = None
                return

            self.client = OpenAI(
                api_key=api_key,
                base_url=self.get_config_value('base_url', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
            )
            logger.info(f"通义千问客户端初始化成功 - 基础URL: {self.get_config_value('base_url')}")
        except Exception as e:
            logger.error(f"通义千问客户端初始化失败: {e}")
            self.client = None
    
    async def generate_response(self, messages: List[AIMessage], **kwargs) -> AIResponse:
        """
        生成通义千问响应（使用OpenAI SDK格式）
        
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
            request_params = {
                'model': kwargs.get('model', self.get_config_value('model', 'qwen-turbo')),
                'messages': formatted_messages,
                'max_tokens': kwargs.get('max_tokens', self.get_config_value('max_tokens', 1000)),
                'temperature': kwargs.get('temperature', self.get_config_value('temperature', 0.7))
            }
            
            logger.info(f"调用通义千问API - 模型: {request_params['model']}, 消息数: {len(formatted_messages)}")
            
            # 调用通义千问API（使用OpenAI SDK格式）
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
            
            logger.info(f"通义千问响应生成成功 - 响应长度: {len(ai_response.content)}")
            return ai_response
            
        except Exception as e:
            logger.error(f"通义千问响应生成失败: {e}")
            return AIResponse(
                content=f"抱歉，通义千问服务暂时不可用：{str(e)}",
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
        生成通义千问流式响应（使用OpenAI SDK格式）
        
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
            request_params = {
                'model': kwargs.get('model', self.get_config_value('model', 'qwen-turbo')),
                'messages': formatted_messages,
                'max_tokens': kwargs.get('max_tokens', self.get_config_value('max_tokens', 1000)),
                'temperature': kwargs.get('temperature', self.get_config_value('temperature', 0.7)),
                'stream': True
            }
            
            logger.info(f"调用通义千问流式API - 模型: {request_params['model']}, 消息数: {len(formatted_messages)}")
            
            # 调用通义千问流式API（使用OpenAI SDK格式）
            response = self.client.chat.completions.create(**request_params)
            
            chunk_count = 0
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    chunk_count += 1
                    yield content
            
            logger.info(f"通义千问流式响应完成 - 块数: {chunk_count}")
            
        except Exception as e:
            logger.error(f"通义千问流式响应失败: {e}")
            yield f"抱歉，通义千问流式服务暂时不可用：{str(e)}"
    
    def validate_config(self) -> bool:
        """
        验证通义千问配置是否有效
        
        Returns:
            bool: 配置是否有效
        """
        api_key = self.get_config_value('api_key')
        if not api_key:
            logger.error("通义千问API密钥未配置")
            return False
        
        if not self.client:
            logger.error("通义千问客户端未初始化")
            return False
        
        try:
            logger.info(f"通义千问配置验证成功")
            return True
        except Exception as e:
            logger.error(f"通义千问配置验证失败: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """
        获取通义千问可用的模型列表
        
        Returns:
            List[str]: 可用模型列表
        """
        # 通义千问的可用模型列表
        models = [
            'qwen-turbo',
            'qwen-plus',
            'qwen-max',
            'qwen-max-1201',
            'qwen-max-longcontext',
            'qwen1.5-72b-chat',
            'qwen1.5-32b-chat',
            'qwen1.5-14b-chat',
            'qwen1.5-7b-chat'
        ]
        
        logger.info(f"获取通义千问可用模型成功 - 模型数: {len(models)}")
        return models