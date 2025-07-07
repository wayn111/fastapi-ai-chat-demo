#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI提供商工厂类
统一管理和创建不同的AI提供商实例
"""

import logging
import inspect
import importlib
import pkgutil
from typing import Dict, Any, Optional, List, Type

from .base import BaseAIProvider
from .openai_compatible_provider import OpenAICompatibleProvider

logger = logging.getLogger(__name__)


class AIProviderFactory:
    """AI提供商工厂类"""

    # 提供商实例缓存
    _instances: Dict[str, BaseAIProvider] = {}
    # 动态发现的提供商类缓存
    _discovered_providers: Optional[Dict[str, Type[BaseAIProvider]]] = None

    @classmethod
    def _discover_providers(cls) -> Dict[str, Type[BaseAIProvider]]:
        """
        动态发现所有OpenAICompatibleProvider的子类
        
        Returns:
            Dict[str, Type[BaseAIProvider]]: 提供商名称到类的映射
        """
        if cls._discovered_providers is not None:
            return cls._discovered_providers
            
        providers = {}
        
        # 获取当前包的路径
        import ai_providers
        package_path = ai_providers.__path__
        
        # 遍历包中的所有模块
        for importer, modname, ispkg in pkgutil.iter_modules(package_path):
            if modname.endswith('_provider') and modname != 'openai_compatible_provider':
                try:
                    # 动态导入模块
                    module = importlib.import_module(f'ai_providers.{modname}')
                    
                    # 查找模块中所有继承自OpenAICompatibleProvider的类
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, OpenAICompatibleProvider) and 
                            obj != OpenAICompatibleProvider and
                            hasattr(obj, 'PROVIDER_NAME')):
                            
                            # 使用类名去掉Provider后缀作为提供商名称
                            provider_key = name.lower().replace('provider', '')
                            providers[provider_key] = obj
                            logger.debug(f"发现提供商: {provider_key} -> {name}")
                            
                except Exception as e:
                    logger.warning(f"导入模块 {modname} 时出错: {e}")
                    
        cls._discovered_providers = providers
        logger.info(f"动态发现 {len(providers)} 个提供商: {list(providers.keys())}")
        return providers

    @classmethod
    def create_provider(cls, provider_name: str, config: Dict[str, Any]) -> BaseAIProvider:
        """
        创建AI提供商实例

        Args:
            provider_name: 提供商名称
            config: 配置字典

        Returns:
            BaseAIProvider: AI提供商实例

        Raises:
            ValueError: 当提供商不存在时
        """
        provider_name = provider_name.lower()
        providers = cls._discover_providers()

        if provider_name not in providers:
            raise ValueError(f"未知的AI提供商: {provider_name}，可用提供商: {list(providers.keys())}")

        # 检查是否已有实例
        cache_key = f"{provider_name}_{hash(str(sorted(config.items())))}"
        if cache_key in cls._instances:
            logger.debug(f"返回缓存的{provider_name}提供商实例")
            return cls._instances[cache_key]

        try:
            # 创建新实例
            provider_class = providers[provider_name]
            provider_instance = provider_class(config)

            # 缓存实例
            cls._instances[cache_key] = provider_instance
            logger.info(f"成功创建并缓存{provider_name}提供商实例")
            return provider_instance

        except Exception as e:
            logger.error(f"创建{provider_name}提供商实例失败: {e}")
            raise

    @classmethod
    def get_available_providers(cls) -> List[str]:
        """
        获取所有可用的提供商名称

        Returns:
            List[str]: 可用提供商名称列表
        """
        providers = cls._discover_providers()
        return list(providers.keys())

    @classmethod
    def register_provider(cls, name: str, provider_class: type):
        """
        注册新的AI提供商

        Args:
            name: 提供商名称
            provider_class: 提供商类（必须继承BaseAIProvider）
        """
        if not issubclass(provider_class, BaseAIProvider):
            raise ValueError(f"提供商类必须继承BaseAIProvider")

        # 确保已发现的提供商字典已初始化
        if cls._discovered_providers is None:
            cls._discover_providers()
        
        cls._discovered_providers[name.lower()] = provider_class
        logger.info(f"注册新的AI提供商: {name}")

    @classmethod
    def clear_cache(cls):
        """
        清除提供商实例缓存
        """
        cls._instances.clear()
        logger.info("AI提供商实例缓存已清除")

    @classmethod
    def get_provider_info(cls, provider_name: str) -> Dict[str, Any]:
        """
        获取提供商信息

        Args:
            provider_name: 提供商名称

        Returns:
            Dict[str, Any]: 提供商信息字典，包含名称、模型等
        """
        provider_name = provider_name.lower()
        providers = cls._discover_providers()

        if provider_name not in providers:
            return {}

        provider_class = providers[provider_name]

        return {
            'name': provider_name,
            'display_name': getattr(provider_class, 'PROVIDER_NAME', provider_name),
            'default_model': getattr(provider_class, 'DEFAULT_MODEL', ''),
            'available_models': getattr(provider_class, 'AVAILABLE_MODELS', []),
            'base_url': getattr(provider_class, 'DEFAULT_BASE_URL', ''),
        }

    @classmethod
    def create_multi_provider_manager(cls, configs: Dict[str, Dict[str, Any]]) -> 'MultiProviderManager':
        """
        创建多提供商管理器

        Args:
            configs: 多个提供商的配置字典，格式为 {provider_name: config}

        Returns:
            MultiProviderManager: 多提供商管理器实例
        """
        return MultiProviderManager(configs)


class MultiProviderManager:
    """多提供商管理器"""

    def __init__(self, configs: Dict[str, Dict[str, Any]]):
        """
        初始化多提供商管理器

        Args:
            configs: 多个提供商的配置字典
        """
        self.providers: Dict[str, BaseAIProvider] = {}
        self.default_provider: Optional[str] = None

        # 初始化所有提供商
        for provider_name, config in configs.items():
            try:
                provider = AIProviderFactory.create_provider(provider_name, config)
                self.providers[provider_name] = provider

                # 设置第一个成功初始化的提供商为默认提供商
                if self.default_provider is None:
                    self.default_provider = provider_name

                logger.info(f"多提供商管理器: {provider_name}提供商初始化成功")

            except Exception as e:
                logger.warning(f"多提供商管理器: {provider_name}提供商初始化失败: {e}")

    def get_provider(self, provider_name: str = None) -> Optional[BaseAIProvider]:
        """
        获取指定的提供商实例

        Args:
            provider_name: 提供商名称，如果为None则返回默认提供商

        Returns:
            Optional[BaseAIProvider]: 提供商实例，如果不存在则返回None
        """
        if provider_name is None:
            provider_name = self.default_provider

        return self.providers.get(provider_name)

    def get_available_providers(self) -> List[str]:
        """
        获取当前可用的提供商列表

        Returns:
            List[str]: 可用提供商名称列表
        """
        return list(self.providers.keys())

    def set_default_provider(self, provider_name: str) -> bool:
        """
        设置默认提供商

        Args:
            provider_name: 提供商名称

        Returns:
            bool: 设置是否成功
        """
        if provider_name in self.providers:
            self.default_provider = provider_name
            logger.info(f"默认提供商设置为: {provider_name}")
            return True
        else:
            logger.warning(f"设置默认提供商失败: {provider_name}不存在")
            return False

    def get_all_available_models(self) -> Dict[str, List[str]]:
        """
        获取所有提供商的可用模型

        Returns:
            Dict[str, List[str]]: 提供商名称到模型列表的映射
        """
        all_models = {}

        for provider_name, provider in self.providers.items():
            try:
                models = provider.get_available_models()
                all_models[provider_name] = models
            except Exception as e:
                logger.warning(f"获取{provider_name}可用模型失败: {e}")
                all_models[provider_name] = []

        return all_models

    async def generate_response_with_fallback(
            self,
            messages: List,
            preferred_provider: str = None,
            **kwargs
    ):
        """
        使用回退机制生成响应

        Args:
            messages: 消息列表
            preferred_provider: 首选提供商
            **kwargs: 其他参数

        Returns:
            响应结果
        """
        # 确定尝试顺序
        providers_to_try = []

        if preferred_provider and preferred_provider in self.providers:
            providers_to_try.append(preferred_provider)

        # 添加其他提供商作为备选
        for provider_name in self.providers.keys():
            if provider_name not in providers_to_try:
                providers_to_try.append(provider_name)

        # 依次尝试提供商
        last_error = None
        for provider_name in providers_to_try:
            try:
                provider = self.providers[provider_name]
                logger.info(f"尝试使用{provider_name}提供商生成响应")

                response = await provider.generate_response(messages, **kwargs)

                # 检查响应是否成功
                if response.finish_reason != 'error':
                    logger.info(f"使用{provider_name}提供商生成响应成功")
                    return response
                else:
                    logger.warning(f"{provider_name}提供商返回错误响应，尝试下一个提供商")

            except Exception as e:
                logger.warning(f"{provider_name}提供商生成响应失败: {e}")
                last_error = e
                continue

        # 所有提供商都失败
        logger.error(f"所有AI提供商都无法生成响应，最后错误: {last_error}")
        raise Exception(f"所有AI提供商都无法生成响应: {last_error}")

    async def generate_streaming_response(
            self,
            messages: List,
            provider: str = None,
            model: str = None,
            **kwargs
    ):
        """
        生成流式响应

        Args:
            messages: 消息列表
            provider: 指定提供商
            model: 指定模型
            **kwargs: 其他参数

        Yields:
            流式响应数据
        """
        # 确定使用的提供商
        provider_name = provider if provider and provider in self.providers else self.default_provider

        if not provider_name or provider_name not in self.providers:
            raise Exception("没有可用的AI提供商")

        provider_instance = self.providers[provider_name]
        logger.info(f"使用{provider_name}提供商生成流式响应，模型: {model or '默认'}")

        # 如果指定了模型，添加到kwargs中
        if model:
            kwargs['model'] = model

        try:
            async for chunk in provider_instance.generate_streaming_response(messages, **kwargs):
                yield chunk
        except Exception as e:
            logger.error(f"{provider_name}提供商生成流式响应失败: {e}")
            raise

    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有提供商的状态信息

        Returns:
            Dict[str, Dict[str, Any]]: 提供商状态信息
        """
        status = {}

        for provider_name, provider in self.providers.items():
            try:
                # 检查提供商是否可用
                is_available = provider.validate_config()
                status[provider_name] = {
                    'available': is_available,
                    'is_default': provider_name == self.default_provider,
                    'class_name': provider.__class__.__name__
                }
            except Exception as e:
                status[provider_name] = {
                    'available': False,
                    'is_default': provider_name == self.default_provider,
                    'error': str(e)
                }

        return status
