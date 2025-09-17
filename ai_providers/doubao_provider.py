#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Doubao提供商实现
支持Doubao系列模型
使用OpenAI SDK格式统一接口
支持文生图功能
"""

import logging
from .openai_compatible_provider import OpenAICompatibleProvider
from .base import ImageGenerationRequest, ImageGenerationResponse

logger = logging.getLogger(__name__)

class DoubaoProvider(OpenAICompatibleProvider):
    """Doubao提供商实现类 - 使用OpenAI兼容格式"""

    # 提供商配置
    DEFAULT_BASE_URL = 'https://ark.cn-beijing.volces.com/api/v3'
    DEFAULT_MODEL = 'doubao-seed-1-6-250615'
    PROVIDER_NAME = 'Doubao'
    AVAILABLE_MODELS = [
        'doubao-seed-1-6-250615',
    ]

    # 图片生成专用模型
    IMAGE_GENERATION_MODEL = 'doubao-seedream-4-0-250828'

    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResponse:
        """
        生成图片功能实现
        支持纯文本生成图片和图片生成图片两种模式

        Args:
            request: 图片生成请求对象

        Returns:
            ImageGenerationResponse: 图片生成响应对象
        """
        try:
            if not self.client:
                logger.error("Doubao客户端未初始化，无法生成图片")
                return ImageGenerationResponse(
                    url=None,
                    b64_json=None,
                    revised_prompt=None,
                    model=self.IMAGE_GENERATION_MODEL,
                    provider=self.PROVIDER_NAME
                )

            # 构建图片生成请求参数
            image_params = {
                'model': self.IMAGE_GENERATION_MODEL,
                'prompt': request.prompt,
                'size': request.size or "2K",  # 豆包支持的尺寸格式
                'response_format': request.response_format or "url",
                'extra_body': {
                    'watermark': request.watermark if request.watermark is not None else True
                }
            }

            # 如果提供了输入图片URL，则为图片生成图片模式
            if request.image_data:
                image_params['extra_body']['image'] = f"data:image/{request.image_type};base64,{request.image_data}"
                logger.info(f"Doubao图片生成图片模式 - 输入图片: {request.image_data}")
            else:
                logger.info("Doubao纯文本生成图片模式")

            logger.info(f"调用Doubao图片生成API - 模型: {self.IMAGE_GENERATION_MODEL}, 提示词: {request.prompt[:50]}...")

            # 调用豆包图片生成API
            response = self.client.images.generate(**image_params)

            # 构建响应对象
            if response.data and len(response.data) > 0:
                image_data = response.data[0]

                image_response = ImageGenerationResponse(
                    url=getattr(image_data, 'url', None),
                    b64_json=getattr(image_data, 'b64_json', None),
                    revised_prompt=getattr(image_data, 'revised_prompt', request.prompt),
                    model=self.IMAGE_GENERATION_MODEL,
                    provider=self.PROVIDER_NAME
                )

                logger.info(f"Doubao图片生成成功 - URL: {image_response.url is not None}")
                return image_response
            else:
                logger.error("Doubao图片生成响应为空")
                return ImageGenerationResponse(
                    url=None,
                    b64_json=None,
                    revised_prompt=request.prompt,
                    model=self.IMAGE_GENERATION_MODEL,
                    provider=self.PROVIDER_NAME
                )

        except Exception as e:
            logger.error(f"Doubao图片生成失败: {e}")
            return ImageGenerationResponse(
                url=None,
                b64_json=None,
                revised_prompt=request.prompt,
                model=self.IMAGE_GENERATION_MODEL,
                provider=self.PROVIDER_NAME
            )
