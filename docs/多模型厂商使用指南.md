本文将深入讲解如何在 FastAPI AI 聊天应用中设计和实现多模型厂商架构，让你的应用能够灵活切换不同的 AI 提供商，提升系统的可靠性和成本效益。即使你是架构设计新手，也能跟着本教程掌握多厂商集成的核心技术。

> 📖 项目地址：https://github.com/wayn111/fastapi-ai-chat-demo
>
> 温馨提示：本文全文约一万字，看完约需 15 分钟。
>
> 上文链接：[FastAPI开发AI应用一：实现连续多轮对话](https://mp.weixin.qq.com/s?__biz=MzU4NjMyMjM1Nw==&mid=2247491908&idx=1&sn=b062a5f0f6e4b9479ce3a51f0ba09282&scene=21#wechat_redirect)

## 项目概述

想象一下，你的 AI 聊天应用不再依赖单一的 AI 提供商，而是能够智能地在 OpenAI、DeepSeek、通义千问等多个厂商之间切换。当某个服务出现问题时，可以切换到备用提供商；当需要降低成本时，可以选择性价比更高的模型。这就是我们要构建的多模型厂商架构！

![图片](https://p0-xtjj-private.juejin.cn/tos-cn-i-73owjymdk6/b7dcb083fbf04609bcc67bf37fce2cc4~tplv-73owjymdk6-jj-mark-v1:0:0:0:0:5o6Y6YeR5oqA5pyv56S-5Yy6IEAg56iL5bqP5ZGYd2F5bg==:q75.awebp?policy=eyJ2bSI6MywidWlkIjoiNDQwNjQ5ODMzNjk4MDEwMyJ9&rk3s=e9ecf3d6&x-orig-authkey=f32326d3454f2ac7e96d3d06cdbb035152127018&x-orig-expires=1752031405&x-orig-sign=19ouIZ0WsCqVxEs1MXydV0dmqyo%3D)![图片](https://p0-xtjj-private.juejin.cn/tos-cn-i-73owjymdk6/86015007ddb949519ef07adbab260807~tplv-73owjymdk6-jj-mark-v1:0:0:0:0:5o6Y6YeR5oqA5pyv56S-5Yy6IEAg56iL5bqP5ZGYd2F5bg==:q75.awebp?policy=eyJ2bSI6MywidWlkIjoiNDQwNjQ5ODMzNjk4MDEwMyJ9&rk3s=e9ecf3d6&x-orig-authkey=f32326d3454f2ac7e96d3d06cdbb035152127018&x-orig-expires=1752031405&x-orig-sign=0ufyXQ2l34Uclmo2v%2BX866Qu%2BcA%3D)

> 在本章节中，我们重构了前端界面，使其更加美观，参考 lobechat 界面风格。

### 核心功能

-   **多厂商统一管理**：一套代码支持多个 AI 提供商，无需重复开发
-   **智能故障转移**：主提供商不可用时自动切换到备用提供商
-   **成本优化策略**：根据不同场景选择最经济的模型
-   **动态提供商发现**：新增提供商无需修改核心代码
-   **统一接口设计**：所有提供商使用相同的调用方式

### 技术栈

-   **核心框架**：FastAPI（高性能异步 Web 框架）
-   **AI 集成**：OpenAI SDK（统一的 AI 接口标准）
-   **设计模式**：工厂模式 + 抽象工厂模式
-   **配置管理**：环境变量 + 动态配置
-   **数据存储**：Redis（会话和配置缓存）

### 🤖 支持的 AI 厂商

| 厂商           | 代表模型                          | 特色          | 成本水平 |
| ------------ | ----------------------------- | ----------- | ---- |
| **OpenAI**   | GPT-4, GPT-3.5-turbo          | 综合能力强，生态完善  | 较高   |
| **DeepSeek** | deepseek-chat, deepseek-coder | 性价比高，推理能力强  | 低    |
| **通义千问**     | qwen-turbo, qwen-plus         | 中文理解优秀，阿里生态 | 中等   |

## 🏗️ 核心架构设计

### 🎯 设计理念

我们的多模型厂商架构基于三个核心设计原则：

**1. 统一接口原则**所有 AI 提供商都遵循相同的接口规范，就像不同品牌的手机都使用相同的充电接口一样。这样可以确保切换提供商时不需要修改业务代码。

**2. 开放扩展原则**新增 AI 提供商时，只需要继承基类并配置几个参数，系统会自动发现并集成新的提供商。

**3. 故障隔离原则**每个提供商都是独立的实例，一个提供商的故障不会影响其他提供商的正常工作。

### 🏛️ 架构层次

![图片](https://p0-xtjj-private.juejin.cn/tos-cn-i-73owjymdk6/b61bb29ea2ed49c2808011722dc29cbe~tplv-73owjymdk6-jj-mark-v1:0:0:0:0:5o6Y6YeR5oqA5pyv56S-5Yy6IEAg56iL5bqP5ZGYd2F5bg==:q75.awebp?policy=eyJ2bSI6MywidWlkIjoiNDQwNjQ5ODMzNjk4MDEwMyJ9&rk3s=e9ecf3d6&x-orig-authkey=f32326d3454f2ac7e96d3d06cdbb035152127018&x-orig-expires=1752031405&x-orig-sign=3ppraLcPG%2BXzIWUtjU%2BcQRnU8eY%3D)

###

我们的架构分为四个清晰的层次，每一层都有明确的职责：

#### 1. 抽象接口层（BaseAIProvider）

这是整个架构的"宪法"，定义了所有 AI 提供商必须遵循的接口规范：

```
from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncGenerator

class BaseAIProvider(ABC):
    """AI提供商抽象基类 - 定义统一接口规范"""

    def __init__(self, config: Dict[str, Any]):
        """初始化提供商配置"""
        self.config = config
        self.provider_name = self.__class__.__name__.replace('Provider', '').lower()

    @abstractmethod
    asyncdef generate_response(self, messages: List[AIMessage], **kwargs) -> AIResponse:
        """生成AI响应 - 所有提供商必须实现"""
        pass

    @abstractmethod
    asyncdef generate_streaming_response(self, messages: List[AIMessage], **kwargs) -> AsyncGenerator[str, None]:
        """生成流式响应 - 支持实时对话"""
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置有效性"""
        pass
```

**为什么这样设计？**

-   **强制规范**：所有提供商都必须实现这些方法
-   **统一流式响应**：所有厂商使用同一套流式响应
-   **安全性**：每个厂商都需要验证配置有效性

#### 2. 兼容适配层（OpenAICompatibleProvider）

这一层是我们架构的"翻译官"，将 OpenAI 的接口标准适配给所有提供商：

```
class OpenAICompatibleProvider(BaseAIProvider):
    """OpenAI兼容提供商基类 - 统一OpenAI SDK调用方式"""

    # 子类需要重写的配置
    DEFAULT_BASE_URL = None
    DEFAULT_MODEL = None
    PROVIDER_NAME = None
    AVAILABLE_MODELS = []

    def __init__(self, config: Dict[str, Any]):
        """初始化OpenAI兼容客户端"""
        super().__init__(config)
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """初始化OpenAI SDK客户端"""
        try:
            api_key = self.get_config_value('api_key')
            ifnot api_key:
                logger.error(f"{self.get_provider_display_name()}API密钥为空")
                return

            # 使用OpenAI SDK，但指向不同厂商的API端点
            self.client = OpenAI(
                api_key=api_key,
                base_url=self.get_config_value('base_url', self.DEFAULT_BASE_URL)
            )
            logger.info(f"{self.get_provider_display_name()}客户端初始化成功")
        except Exception as e:
            logger.error(f"客户端初始化失败: {e}")
            self.client = None
```

**核心优势：**

-   **代码复用**：所有兼容 OpenAI 接口的厂商都可以复用这套代码
-   **维护简单**：所有厂商共用一套 openai 的 api 接口调用逻辑
-   **标准统一**：所有厂商都使用同一套流式响应，使用相同的消息格式和参数

#### 3. 具体提供商实现层

这一层是各个 AI 厂商的"身份证"，每个提供商只需要声明自己的基本信息，继承 OpenAICompatibleProvider 即可。

```
class DeepseekProvider(OpenAICompatibleProvider):
    """DeepSeek提供商实现 - 只需配置基本信息"""

    # 提供商配置 - 这就是全部需要的代码！
    DEFAULT_BASE_URL = 'https://api.deepseek.com/v1'
    DEFAULT_MODEL = 'deepseek-chat'
    PROVIDER_NAME = 'DeepSeek'
    AVAILABLE_MODELS = [
        'deepseek-chat',      # 通用对话模型
        'deepseek-coder',     # 代码专用模型
        'deepseek-math',      # 数学推理模型
        'deepseek-reasoner'   # 深度推理模型
    ]
```

**实现原理：**

-   **继承复用**：继承 `OpenAICompatibleProvider` 获得所有通用功能
-   **配置驱动**：只需要配置几个类变量就完成了集成
-   **自动发现**：系统会自动扫描并注册这个提供商

#### 4. 工厂管理层（AIProviderFactory）

这是整个架构的"大脑"，负责动态发现、创建和管理所有提供商：

```
class AIProviderFactory:
    """AI提供商工厂 - 统一管理所有提供商"""

    # 提供商实例缓存
    _instances: Dict[str, BaseAIProvider] = {}
    # 动态发现的提供商类缓存
    _discovered_providers: Optional[Dict[str, Type[BaseAIProvider]]] = None

    @classmethod
    def _discover_providers(cls) -> Dict[str, Type[BaseAIProvider]]:
        """动态发现所有提供商类 - 这是魔法发生的地方"""
        if cls._discovered_providers isnotNone:
            return cls._discovered_providers

        providers = {}

        # 扫描 ai_providers 包中的所有模块
        import ai_providers
        package_path = ai_providers.__path__

        for importer, modname, ispkg in pkgutil.iter_modules(package_path):
            if modname.endswith('_provider') and modname != 'openai_compatible_provider':
                try:
                    # 动态导入模块
                    module = importlib.import_module(f'ai_providers.{modname}')

                    # 查找继承自OpenAICompatibleProvider的类
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, OpenAICompatibleProvider) and
                            obj != OpenAICompatibleProvider and
                            hasattr(obj, 'PROVIDER_NAME')):

                            provider_key = name.lower().replace('provider', '')
                            providers[provider_key] = obj
                            logger.debug(f"发现提供商: {provider_key} -> {name}")

                except Exception as e:
                    logger.warning(f"导入模块 {modname} 时出错: {e}")

        cls._discovered_providers = providers
        logger.info(f"动态发现 {len(providers)} 个提供商: {list(providers.keys())}")
        return providers
```

**工厂模式的威力：**

-   **动态发现**：自动扫描并注册新的提供商，无需手动配置
-   **实例缓存**：相同配置的提供商实例会被缓存，提高性能
-   **统一创建**：所有提供商都通过工厂创建，确保一致性

#### 🔄 多提供商管理器

在工厂的基础上，我们还提供了多提供商管理器，让你可以同时管理多个提供商：

```
class MultiProviderManager:
    """多提供商管理器 - 统一管理多个AI提供商实例"""

    def __init__(self, configs: Dict[str, Dict[str, Any]]):
        """初始化多提供商管理器

        Args:
            configs: 多个提供商的配置，格式：{provider_name: config}
        """
        self.providers: Dict[str, BaseAIProvider] = {}
        self.default_provider = None

        # 初始化所有配置的提供商
        for provider_name, config in configs.items():
            try:
                provider = AIProviderFactory.create_provider(provider_name, config)
                if provider.validate_config():
                    self.providers[provider_name] = provider
                    logger.info(f"提供商 {provider_name} 初始化成功")

                    # 设置默认提供商
                    if self.default_provider isNone:
                        self.default_provider = provider_name
                else:
                    logger.warning(f"提供商 {provider_name} 配置验证失败")
            except Exception as e:
                logger.error(f"提供商 {provider_name} 初始化失败: {e}")

    def get_available_providers(self) -> List[str]:
        """获取所有可用的提供商列表"""
        return list(self.providers.keys())
```

#### 🔧 环境变量配置

在项目根目录创建 `.env` 文件：

```
REDIS_HOST="127.0.0.1"
REDIS_PORT=6379
REDIS_PASSWORD=""

# ===========================================
# AI 提供商配置（至少配置一个）
# ===========================================

# OpenAI 配置
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1  # 可选，默认官方地址
OPENAI_MODEL=gpt-4o  # 可选，默认模型

# DeepSeek 配置
DEEPSEEK_API_KEY=sk-your-deepseek-api-key
DEEPSEEK_MODEL=deepseek-chat  # 可选

# 通义千问配置
QIANWEN_API_KEY=sk-your-qianwen-api-key
QIANWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# ===========================================
# 应用配置
# ===========================================
DEFAULT_AI_PROVIDER=deepseek  # 默认使用的提供商
MAX_TOKENS=1000               # 最大生成长度
TEMPERATURE=0.7              # 创造性参数
```

##### 🏗️ 配置类设计

我们使用配置类来统一管理所有配置项：

```
class Config:
    """应用配置管理类"""

    # 应用基础配置
    APP_NAME = "FastAPI AI Chat Demo"
    # ...

    # 新增AI提供商基础信息
    _AI_PROVIDERS_INFO = {
        'openai': {
            'base_url': 'https://api.openai.com/v1',
            'model': 'gpt-4o'
        },
        'deepseek': {
            'base_url': 'https://api.deepseek.com/v1',
            'model': 'deepseek-chat'
        },
        'qianwen': {
            'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
            'model': 'qwen-turbo'
        }
    }

    # AI提供商配置 - 动态生成
    @classmethod
    def _get_ai_providers_config(cls) -> dict:
        """获取所有AI提供商配置"""
        return {provider: cls._build_provider_config(provider) for provider in cls._AI_PROVIDERS_INFO.keys()}

    # 延迟初始化AI提供商配置
    @property
    def AI_PROVIDERS_CONFIG(self) -> dict:
        ifnot hasattr(self, '_ai_providers_config'):
            self._ai_providers_config = self._get_ai_providers_config()
        return self._ai_providers_config

    @classmethod
    def get_all_ai_configs(cls) -> dict:
        """获取所有已配置API Key的AI提供商配置"""
        configs = cls._get_ai_providers_config()
        return {name: config for name, config in configs.items() if config.get('api_key')}
```

在 Config 配置中新增 AI 提供商核心配置。

### 📡 核心 API 接口

#### 1. 获取可用提供商列表

```
@app.get("/providers")
asyncdef get_providers():
    """获取可用的AI提供商列表"""
    logger.info("获取AI提供商列表")
    try:
        configured_providers = Config.get_configured_providers()
        all_models = ai_manager.get_all_available_models()

        providers_info = []
        for provider in configured_providers:
            provider_obj = ai_manager.get_provider(provider)
            if provider_obj:
                providers_info.append({
                    "id": provider,
                    "name": provider_obj.get_provider_name(),
                    "models": provider_obj.get_available_models(),
                    "is_default": provider == Config.DEFAULT_AI_PROVIDER
                })

        return {
            "providers": providers_info,
            "default_provider": Config.DEFAULT_AI_PROVIDER,
            "all_models": all_models
        }
    except Exception as e:
        logger.error(f"获取AI提供商列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取提供商列表失败: {str(e)}")
```

/providers 接口会返回所有可用 AI 提供商，以及对应模型。

#### 2. 流式聊天接口（支持提供商选择）

```
@app.get("/chat/stream")
asyncdef chat_stream(
    user_id: str = Query(..., description="用户ID"),
    session_id: str = Query(..., description="会话ID"),
    message: str = Query(..., description="用户消息"),
    role: str = Query("assistant", description="AI角色"),
    provider: Optional[str] = Query(None, description="AI提供商"),
    model: Optional[str] = Query(None, description="AI模型")
):
    """流式聊天接口"""
    logger.info(f"流式聊天请求 - 用户: {user_id}, 会话: {session_id[:8]}..., 角色: {role}, 消息长度: {len(message)}, 提供商: {provider}")

    if role notin AI_ROLES:
        logger.warning(f"不支持的AI角色: {role}")
        raise HTTPException(status_code=400, detail="不支持的AI角色")

    return StreamingResponse(
        generate_streaming_response(user_id, session_id, message, role, provider, model),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )
```

流式聊天接口参数中新增 AI 提供商以及 AI 模型参数。

## 🛠️ 扩展新提供商实现

### 🚀 快速添加新提供商

对于支持 OpenAI API 格式的提供商，只需几行代码即可集成：

这里用 moonshot 作为新厂商接入，在 ai_providers 目录下新增 moonshot_provider.py 文件，

```
# ai_providers/moonshot_provider.py
from ai_providers.openai_compatible_provider import OpenAICompatibleProvider

class MoonshotProvider(OpenAICompatibleProvider):
    """月之暗面 Kimi 提供商"""
    DEFAULT_BASE_URL = "https://api.moonshot.cn/v1"
    DEFAULT_MODEL = "moonshot-v1-8k"
    PROVIDER_NAME = "moonshot"
    AVAILABLE_MODELS = [
        "moonshot-v1-8k",
        "moonshot-v1-32k",
        "moonshot-v1-128k"
    ]
```

#### 环境变量配置

在 .env 文件中新增 moonshot 配置

```
# Moonshot (月之暗面)
MOONSHOT_API_KEY=sk-your-moonshot-api-key
MOONSHOT_BASE_URL=https://api.moonshot.cn/v1  # 可选
MOONSHOT_MODEL=moonshot-v1-8k  # 可选
```

#### 配置类更新

config.py 中添加 moonshot 配置，

```
class Config:
    # ... 现有配置 ...

    # AI提供商基础信息
    _AI_PROVIDERS_INFO = {
        'openai': {
            'base_url': 'https://api.openai.com/v1',
            'model': 'gpt-4o'
        },
        'deepseek': {
            'base_url': 'https://api.deepseek.com/v1',
            'model': 'deepseek-chat'
        },
        'qianwen': {
            'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
            'model': 'qwen-turbo'
        },
        'moonshot': {
            'base_url': 'https://api.moonshot.cn/v1',
            'model': 'moonshot-v1-8k'
        }
    }
```

通过以上步骤，您可以轻松扩展支持任何新的 AI 提供商，系统会自动发现并集成新的提供商，无需修改核心代码。

## 📚 总结

本文详细介绍了如何在 FastAPI 应用中构建一个灵活、可扩展的多模型厂商架构。通过抽象接口层、兼容适配层、具体实现层和工厂管理层的四层架构设计，实现了所有 AI 提供商的统一接口调用，支持 OpenAI、DeepSeek、通义千问等多个厂商的无缝集成。核心采用工厂模式和抽象工厂模式，配合动态提供商发现机制，新增厂商只需几行代码即可完成集成。

最后觉得本文写的不错的话，可以关注我，我会继续更新 FastAPI 框架开发 AI 聊天应用代码。
