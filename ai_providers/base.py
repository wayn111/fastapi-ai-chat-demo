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

@dataclass
class AIResponse:
    """AI响应数据类"""
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None

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