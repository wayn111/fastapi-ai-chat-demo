在前面的文章中，我们已经构建了一个支持多模型厂商的 FastAPI AI 聊天应用架构。今天我们来实战演示如何在现有架构基础上快速新增两个热门的 AI 模型：字节跳动的豆包（Doubao-Seed-1.6）和月之暗面的 Kimi k2。通过这个案例，你将知道在我们的 ai chat 应用中，新增厂商只需要几行代码就行。

> 📖 项目地址：https://github.com/wayn111/fastapi-ai-chat-demo
>
> 温馨提示：本文全文约八千字，看完约需 12 分钟。
>
> 上文链接：[FastAPI开发AI应用三：添加深度思考功能]()

## API Key 获取方式

在开始集成之前，你需要先获取相应的 API Key：

**豆包（字节跳动）API Key 获取：**

1. 访问火山引擎方舟控制台：https://console.volcengine.com/ark/region:ark+cn-beijing/overview
2. 注册并完成实名认证
3. 进入「火山方舟」→「系统管理」→「API Key 管理」
4. 在 API 密钥管理中创建新的 API Key
5. 复制 API Key，格式通常为：`vol-xxx`
6. 进入「火山方舟」→「系统管理」→「开通管理」，开通最新 Doubao-Seed-1.6 模型即可。

**Kimi（月之暗面）API Key 获取：**

1. 访问月之暗面开放平台：https://platform.moonshot.cn/console/account
2. 注册账号并完成手机验证
3. 进入「组织管理」→「API Key 管理」
4. 点击「新建」创建新的 API Key
5. 复制 API Key，格式通常为：`sk-xxx`
6. 注意：Kimi 新用户有 15 元的免费额度，可以直接测试 kimi k2 模型

## 新增厂商概览

**豆包（Doubao）**

字节跳动推出的 AI 大模型，具有强大的中文理解能力，在中文语境下表现优异；支持文本、图像等多种输入形式的多模态功能；相比国外厂商具有明显的成本优势；完全兼容 OpenAI API 格式。

最新的 doubao-seed-1.6 是豆包 1.6 系列中的 All - in - One 综合模型。它是国内首个支持 256K 上下文的思考模型，具备深度思考、多模态理解、图形界面操作等能力。其特点在于支持 thinking/non - thinking / 自适应思考三种模式，自适应思考模式可根据提示词难度自动决定是否开启思考，能在保证效果的同时大幅减少 tokens 消耗，且针对前端编程能力做了加强。

**Kimi（月之暗面）**

月之暗面公司开发的长文本 AI 助手，支持最高 128k tokens 的超长上下文长度；擅长处理长文档和复杂推理任务；能够获取和处理最新的网络信息；同样支持 OpenAI API 标准。主要模型包括 `kimi-k2-0711-preview`（最新预览版）和 `moonshot-v1-8k/32k/128k`（不同上下文长度版本），图标使用 🌙（月亮，呼应"月之暗面"品牌）。

最新的 Kimi K2 是月之暗面发布的开源大语言模型，具备超强代码和 Agent 能力的 MoE 架构基础模型，总参数 1T，激活参数 32B，上下文长度为 128k。在通用知识推理、编程、数学、Agent 等主要类别的基准性能测试中，K2 模型的性能超过其他主流开源模型。

## 新增厂商

### 第一步：创建提供商实现类

得益于我们之前设计的 `OpenAICompatibleProvider` 基类，新增提供商变得极其简单。

在 `ai_providers` 目录下创建 `doubao_provider.py`：

```python
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
        'doubao-1-5-pro-32k-250115'
    ]
```

#### 2. 创建 Kimi 提供商

同样在 `ai_providers` 目录下创建 `kimi_provider.py`：

```python
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
        "kimi-k2-0711-preview",
        "moonshot-v1-8k",
        "moonshot-v1-32k",
        "moonshot-v1-128k",
    ]
```

两个提供商都继承自 `OpenAICompatibleProvider`，自动获得所有通用功能；只需要配置几个类变量就完成了集成；所有提供商都使用相同的方法签名和返回格式，实现了真正的标准化接口。

### 第二步：更新配置管理

在项目根目录的 `.env` 文件中添加新厂商的配置：

```bash
# 豆包配置
DOUBAO_API_KEY=your-doubao-api-key
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
DOUBAO_MODEL=doubao-seed-1-6-250615

# Kimi配置
KIMI_API_KEY=your-kimi-api-key
KIMI_BASE_URL=https://api.moonshot.cn/v1
KIMI_MODEL=moonshot-v1-8k
```

在 `config.py` 中的 `_AI_PROVIDERS_INFO` 字典中添加新厂商信息：

```python
class Config:
    # AI提供商基础信息
    _AI_PROVIDERS_INFO = {
        'openai': {
            'icon': '🤖'
        },
        'deepseek': {
            'icon': '🧠'
        },
        'qianwen': {
            'icon': '🌟'
        },
        'doubao': {  # 新增豆包
            'icon': '🔥'
        },
        'kimi': {    # 新增Kimi
            'icon': '🌙'
        }
    }
```

同时在 `_build_provider_config` 方法中添加默认配置：

```python
@classmethod
def _build_provider_config(cls, provider: str) -> dict:
    """构建单个AI提供商配置"""
    provider_upper = provider.upper()

    # 默认配置映射
    default_configs = {
        'openai': {'base_url': 'https://api.openai.com/v1', 'model': 'gpt-4o'},
        'deepseek': {'base_url': 'https://api.deepseek.com/v1', 'model': 'deepseek-chat'},
        'qianwen': {'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1', 'model': 'qwen-turbo'},
        'doubao': {'base_url': 'https://ark.cn-beijing.volces.com/api/v3', 'model': 'doubao-seed-1-6-250615'},  # 新增
        'kimi': {'base_url': 'https://api.moonshot.cn/v1', 'model': 'moonshot-v1-8k'}  # 新增
    }

    provider_defaults = default_configs.get(provider, {})
    # ... 其余配置逻辑
```

### 第三步：前后端图标管理优化

在新增厂商的过程中，我们发现前端硬编码图标的方式不够优雅。让我们将图标管理迁移到后端统一处理。修改 `main.py` 中的 `/providers` 端点，添加图标信息：

```python
@app.get("/providers")
async def get_providers():
    """获取可用的AI提供商列表"""
    logger.info("获取AI提供商列表")
    try:
        configured_providers = Config.get_configured_providers()
        all_models = ai_manager.get_all_available_models()

        providers_info = []
        for provider in configured_providers:
            provider_obj = ai_manager.get_provider(provider)
            if provider_obj:
                providers_info.append({
                    "id": provider,
                    "name": provider_obj.get_provider_name(),
                    "models": provider_obj.get_available_models(),
                    "is_default": provider == Config.DEFAULT_AI_PROVIDER,
                    "icon": Config.get_provider_icon(provider)  # 新增图标字段
                })

        return {
            "providers": providers_info,
            "default_provider": Config.DEFAULT_AI_PROVIDER,
            "all_models": all_models,
            "provider_icons": Config.get_all_provider_icons()  # 新增图标映射
        }
    except Exception as e:
        logger.error(f"获取AI提供商列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取提供商列表失败: {str(e)}")
```

在 `config.py` 中添加图标获取方法：

```python
@classmethod
def get_provider_icon(cls, provider: str) -> str:
    """获取提供商图标"""
    return cls._AI_PROVIDERS_INFO.get(provider, {}).get('icon', '🤖')

@classmethod
def get_all_provider_icons(cls) -> dict:
    """获取所有提供商图标映射"""
    return {provider: info.get('icon', '🤖') for provider, info in cls._AI_PROVIDERS_INFO.items()}
```

修改前端的 `getProviderIcon` 函数，从硬编码改为使用后端数据：

```javascript
// 全局变量存储提供商图标
let providerIcons = {};

// 简化的图标获取函数
function getProviderIcon(provider) {
    return providerIcons[provider] || '🤖';
}

// 在loadProviders函数中获取图标数据
async function loadProviders() {
    try {
        const response = await fetch('/providers');
        const data = await response.json();

        // 存储图标映射
        providerIcons = data.provider_icons || {};

        // ... 其余逻辑
    } catch (error) {
        console.error('加载提供商失败:', error);
    }
}
```

## 🔧 系统自动发现机制

我们的 ai-chat 应用中采用了**自动发现机制**。当你添加新的提供商文件后，系统会自动扫描并注册，无需手动配置。具体逻辑在 `AIProviderFactory` 中的 `_discover_providers` 方法：

```python
@classmethod
def _discover_providers(cls) -> Dict[str, Type[BaseAIProvider]]:
    """动态发现所有提供商类 - 这是魔法发生的地方"""
    if cls._discovered_providers is not None:
        return cls._discovered_providers

    providers = {}

    # 扫描 ai_providers 包中的所有模块
    import ai_providers
    package_path = ai_providers.__path__

    for importer, modname, ispkg in pkgutil.iter_modules(package_path):
        if modname.endswith('_provider') and modname != 'openai_compatible_provider':
            try:
                # 动态导入模块
                module = importlib.import_module(f'ai_providers.{modname}')

                # 查找继承自OpenAICompatibleProvider的类
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, OpenAICompatibleProvider) and
                        obj != OpenAICompatibleProvider and
                        hasattr(obj, 'PROVIDER_NAME')):

                        provider_key = name.lower().replace('provider', '')
                        providers[provider_key] = obj
                        logger.debug(f"发现提供商: {provider_key} -> {name}")

            except Exception as e:
                logger.warning(f"导入模块 {modname} 时出错: {e}")

    cls._discovered_providers = providers
    logger.info(f"动态发现 {len(providers)} 个提供商: {list(providers.keys())}")
    return providers
```

系统启动时自动扫描 `ai_providers` 目录；只加载符合命名规范的提供商文件；确保加载的类继承自正确的基类；单个提供商加载失败不影响其他提供商，实现了完全的自动化管理。

## 🧪 测试新增厂商

1. .env 文件新增豆包、Kimi 的 apikey 配置

```
DOUBAO_MODEL=doubao-seed-1.6-flash
DOUBAO_API_KEY="xxxxx"
DOUBAO_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"

# Kimi (Moonshot AI)
KIMI_MODEL=kimi-k2-0711-preview
KIMI_API_KEY="xxxxx"
KIMI_BASE_URL="https://api.moonshot.cn/v1"
```

2. 启动应用进行验证：

```bash
# 启动应用
python start_server.py
```

启动日志应该显示：

```
2025-07-15 20:19:15,152 - ai_providers.factory - INFO - 成功创建并缓存kimi提供商实例
2025-07-15 20:19:15,152 - ai_providers.factory - INFO - 多提供商管理器: kimi提供商初始化成功
2025-07-15 20:19:15,152 - main - INFO - AI提供商管理器初始化成功，默认提供商: deepseek
2025-07-15 20:19:15,152 - main - INFO - 可用提供商: ['deepseek', 'qianwen', 'doubao', 'kimi']
```

打开浏览器访问 `http://localhost:8000` 进行前端界面验证，你应该能看到提供商选择器中出现豆包和 Kimi 选项.

## 📚 总结

现在我们的 AI 聊天应用已经支持了 5 个主流的 AI 厂商，用户可以根据不同的需求场景选择最合适的模型。无论是追求性价比的 DeepSeek，还是长文本处理的 Kimi，或是中文优化的豆包，都能在同一个应用中无缝使用。

最后觉得本文写的不错的话，可以关注我，我会继续更新 FastAPI 框架开发 AI 聊天应用的相关内容。
