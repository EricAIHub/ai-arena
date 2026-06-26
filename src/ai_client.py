"""AI Arena - 统一 AI 调用接口

支持重试机制、指数退避、详细错误分类、连接池复用、请求并发控制。
"""

import httpx
import json
import asyncio
from typing import Optional
from dataclasses import dataclass, field
from .logger import arena_logger


class AIError(Exception):
    """AI 调用异常基类"""

    def __init__(self, message: str, code: str = "AI_ERROR", retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.retryable = retryable


class AITimeoutError(AIError):
    """请求超时"""

    def __init__(self, model_name: str, timeout: float):
        super().__init__(
            f"AI 调用超时 ({model_name})，超过 {timeout}s",
            code="TIMEOUT",
            retryable=True,
        )


class AIRateLimitError(AIError):
    """限流错误（429）"""

    def __init__(self, model_name: str, retry_after: Optional[float] = None):
        msg = f"AI 调用被限流 ({model_name})"
        if retry_after:
            msg += f"，{retry_after}s 后可重试"
        super().__init__(msg, code="RATE_LIMIT", retryable=True)
        self.retry_after = retry_after


class AIAPIError(AIError):
    """API 错误（4xx/5xx）"""

    def __init__(self, model_name: str, status_code: int, detail: str = ""):
        super().__init__(
            f"AI API 错误 ({model_name}): HTTP {status_code} {detail}",
            code=f"API_{status_code}",
            retryable=500 <= status_code < 600,
        )
        self.status_code = status_code


class AINetworkError(AIError):
    """网络连接错误"""

    def __init__(self, model_name: str, detail: str = ""):
        super().__init__(
            f"AI 网络错误 ({model_name}): {detail}",
            code="NETWORK_ERROR",
            retryable=True,
        )


@dataclass
class ModelConfig:
    """模型配置"""
    name: str
    base_url: str
    api_key: str
    model_name: str
    emoji: str = "🤖"
    color: str = "#666666"


@dataclass
class ChatMessage:
    """对话消息"""
    role: str  # "system" | "user" | "assistant"
    content: str


class AIClient:
    """统一的 AI 调用接口，支持所有 OpenAI 兼容 API

    特性：
    - 连接池复用（httpx.AsyncClient）
    - 重试机制（最多 3 次，指数退避）
    - 请求超时可配置
    - 并发请求队列（防止同时发起太多 API 调用）
    - 详细错误分类
    """

    def __init__(self, timeout: float = 60.0, max_retries: int = 3, max_concurrent: int = 10):
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None
        # 并发信号量，限制同时进行的 API 调用数
        self._semaphore = asyncio.Semaphore(max_concurrent)

    def _get_client(self) -> httpx.AsyncClient:
        """获取或创建复用的 HTTP 客户端（连接池复用）"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout, connect=10.0),
                limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
            )
            arena_logger.debug(f"创建新的 httpx.AsyncClient，超时={self.timeout}s")
        return self._client

    async def chat(
        self,
        model: ModelConfig,
        system_prompt: str,
        messages: list[ChatMessage],
        temperature: float = 0.8,
        max_tokens: int = 500,
        timeout: Optional[float] = None,
    ) -> str:
        """
        调用 AI 模型，返回回复文本。

        Args:
            model: 模型配置（base_url, api_key, model_name）
            system_prompt: 系统提示词（角色设定）
            messages: 对话历史
            temperature: 温度（0-1），越高越随机
            max_tokens: 最大输出 token 数
            timeout: 可选的请求超时覆盖（秒）

        Returns:
            AI 回复的文本内容

        Raises:
            AIError: API 调用失败时抛出（含子类：AITimeoutError, AIRateLimitError 等）
        """
        url = f"{model.base_url.rstrip('/')}/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {model.api_key}",
        }

        # 构建消息列表
        api_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            api_messages.append({"role": msg.role, "content": msg.content})

        payload = {
            "model": model.model_name,
            "messages": api_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        request_timeout = timeout or self.timeout
        last_error: Optional[Exception] = None

        # 并发控制
        async with self._semaphore:
            for attempt in range(self.max_retries):
                try:
                    client = self._get_client()
                    response = await client.post(
                        url, headers=headers, json=payload,
                        timeout=request_timeout,
                    )

                    # 处理限流
                    if response.status_code == 429:
                        retry_after = response.headers.get("Retry-After")
                        retry_after_s = float(retry_after) if retry_after else None
                        raise AIRateLimitError(model.name, retry_after_s)

                    response.raise_for_status()
                    data = response.json()
                    result = data["choices"][0]["message"]["content"]

                    if attempt > 0:
                        arena_logger.info(f"AI 调用重试成功 ({model.name})，第 {attempt + 1} 次尝试")

                    return result

                except (httpx.TimeoutException, httpx.ConnectTimeout, httpx.ReadTimeout) as e:
                    last_error = AITimeoutError(model.name, request_timeout)
                    arena_logger.warning(f"AI 调用超时 ({model.name})，第 {attempt + 1}/{self.max_retries} 次")

                except AIRateLimitError as e:
                    last_error = e
                    arena_logger.warning(f"AI 调用限流 ({model.name})，第 {attempt + 1}/{self.max_retries} 次")
                    # 如果有 Retry-After，等待指定时间
                    if e.retry_after:
                        await asyncio.sleep(min(e.retry_after, 30))

                except httpx.HTTPStatusError as e:
                    last_error = AIAPIError(model.name, e.response.status_code, e.response.text[:200])
                    arena_logger.warning(f"AI API 错误 ({model.name}): HTTP {e.response.status_code}，第 {attempt + 1}/{self.max_retries} 次")
                    # 4xx 非 429 错误不重试
                    if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                        raise last_error

                except httpx.NetworkError as e:
                    last_error = AINetworkError(model.name, str(e))
                    arena_logger.warning(f"AI 网络错误 ({model.name}): {e}，第 {attempt + 1}/{self.max_retries} 次")

                except AIError:
                    raise  # 已经是 AIError，直接抛出

                except Exception as e:
                    last_error = AIError(f"AI 调用异常 ({model.name}): {str(e)}", code="UNKNOWN")
                    arena_logger.error(f"AI 调用未知异常 ({model.name}): {e}", exc_info=True)

                # 指数退避（不等待最后一次失败）
                if attempt < self.max_retries - 1:
                    wait_time = min(2 ** attempt, 10)  # 1s, 2s, 4s，最多 10s
                    arena_logger.debug(f"等待 {wait_time}s 后重试 ({model.name})")
                    await asyncio.sleep(wait_time)

            # 所有重试都失败
            if last_error:
                raise last_error
            raise AIError(f"AI 调用失败 ({model.name})：未知错误", code="UNKNOWN")

    async def test_connection(self, model: ModelConfig) -> tuple[bool, str]:
        """
        测试 AI 模型连接。

        Returns:
            (成功与否, 消息)
        """
        try:
            result = await self.chat(
                model=model,
                system_prompt="你是一个测试助手。",
                messages=[ChatMessage(role="user", content="你好，请回复'连接成功'。")],
                max_tokens=50,
            )
            return True, f"连接成功！{model.name} 回复: {result[:50]}"
        except AITimeoutError:
            return False, f"连接超时：请检查 base_url 和网络"
        except AINetworkError:
            return False, f"网络错误：无法连接到 {model.base_url}"
        except AIAPIError as e:
            return False, f"API 错误：{str(e)}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"

    async def close(self):
        """关闭 HTTP 客户端，释放连接池"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            arena_logger.debug("httpx.AsyncClient 已关闭")


# 全局客户端实例
ai_client = AIClient()
