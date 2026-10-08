"""
Factory tạo LLM và Embeddings cho 6 providers: openai, gemini, anthropic, ollama, openrouter, huggingface.

Cách dùng:
    from utils.llm_factory import get_llm, get_embeddings

    llm        = get_llm()            # dùng PROVIDER từ .env
    embeddings = get_embeddings()     # dùng PROVIDER từ .env

    llm_gemini = get_llm("gemini")    # chỉ định provider cụ thể
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config
from langchain_core.embeddings import Embeddings


def get_llm(provider: str = None, temperature: float = 0.0):
    """
    Trả về BaseChatModel tương ứng với provider được chọn.

    Args:
        provider    : "openai" | "gemini" | "anthropic" | "ollama" | "openrouter"
                      Mặc định: đọc PROVIDER từ .env (config.PROVIDER)
        temperature : độ ngẫu nhiên (0.0 = tất định, 1.0 = sáng tạo)

    Returns:
        BaseChatModel instance sẵn sàng sử dụng

    Raises:
        ValueError nếu provider không hợp lệ
        ImportError nếu package tương ứng chưa được cài đặt
    """
    provider = (provider or config.PROVIDER).lower()

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        kwargs = {
            "model": config.OPENAI_MODEL,
            "api_key": config.OPENAI_API_KEY,
            "temperature": temperature,
        }
        if config.OPENAI_BASE_URL:
            kwargs["base_url"] = config.OPENAI_BASE_URL
        return ChatOpenAI(**kwargs)

    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=config.GEMINI_MODEL,
            google_api_key=config.GOOGLE_API_KEY,
            temperature=temperature,
        )

    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=config.ANTHROPIC_MODEL,
            api_key=config.ANTHROPIC_API_KEY,
            temperature=temperature,
        )

    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=config.OLLAMA_MODEL,
            base_url=config.OLLAMA_BASE_URL,
            temperature=temperature,
        )

    elif provider == "openrouter":
        # OpenRouter dùng OpenAI-compatible API
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=config.OPENROUTER_MODEL,
            api_key=config.OPENROUTER_API_KEY,
            base_url=config.OPENROUTER_BASE_URL,
            temperature=temperature,
        )

    elif provider == "huggingface":
        # HF Inference Providers router là OpenAI-compatible API
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=config.HF_MODEL,
            api_key=config.HF_TOKEN,
            base_url=config.HF_BASE_URL,
            temperature=temperature,
        )

    else:
        raise ValueError(
            f"Provider không hợp lệ: '{provider}'. "
            "Chọn một trong: openai, gemini, anthropic, ollama, openrouter, huggingface"
        )


def get_embeddings(provider: str = None):
    """
    Trả về Embeddings instance tương ứng với provider được chọn.

    Lưu ý quan trọng:
        - Anthropic KHÔNG có Embeddings API → tự động fallback về OpenAI embeddings
        - OpenRouter cũng dùng OpenAI embeddings (không có API embeddings riêng)
        - Ollama cần model embedding riêng (mặc định: nomic-embed-text)
          Cài đặt: ollama pull nomic-embed-text

    Args:
        provider: "openai" | "gemini" | "anthropic" | "ollama" | "openrouter" | "huggingface"
                  Mặc định: đọc EMBEDDING_PROVIDER từ .env (trống → PROVIDER)

    Returns:
        Embeddings instance sẵn sàng sử dụng
    """
    provider = (provider or config.EMBEDDING_PROVIDER).lower()
    return RetryingEmbeddings(_build_embeddings(provider))


def _build_embeddings(provider: str):
    """Tạo Embeddings instance gốc của provider (chưa có retry)."""
    if provider in ("openai", "openrouter"):
        from langchain_openai import OpenAIEmbeddings
        kwargs = {
            "model": config.OPENAI_EMBEDDING_MODEL,
            "api_key": config.OPENAI_API_KEY,
        }
        if config.OPENAI_BASE_URL:
            kwargs["base_url"] = config.OPENAI_BASE_URL
        return OpenAIEmbeddings(**kwargs)

    elif provider == "gemini":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(
            model=config.GEMINI_EMBEDDING_MODEL,
            google_api_key=config.GOOGLE_API_KEY,
        )

    elif provider == "anthropic":
        # Anthropic không cung cấp Embeddings API → dùng OpenAI thay thế
        print("⚠️  Anthropic không có Embeddings API — đang dùng OpenAI embeddings thay thế.")
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(
            model=config.OPENAI_EMBEDDING_MODEL,
            api_key=config.OPENAI_API_KEY,
        )

    elif provider == "ollama":
        from langchain_ollama import OllamaEmbeddings
        return OllamaEmbeddings(
            model=config.OLLAMA_EMBEDDING_MODEL,
            base_url=config.OLLAMA_BASE_URL,
        )

    elif provider == "huggingface":
        return HFInferenceEmbeddings(
            model=config.HF_EMBEDDING_MODEL,
            token=config.HF_TOKEN,
            provider=config.HF_EMBEDDING_PROVIDER,
        )

    else:
        raise ValueError(
            f"Provider không hợp lệ: '{provider}'. "
            "Chọn một trong: openai, gemini, anthropic, ollama, openrouter, huggingface"
        )


def is_retryable_error(error: Exception) -> bool:
    """
    Lỗi tạm thời đáng thử lại: timeout, mất kết nối, 5xx, rate limit (429).
    Lỗi cố định (401 sai key, 402 hết credit, 404 sai model) → không retry.
    """
    msg = f"{type(error).__name__}: {error}".lower()
    if any(code in msg for code in ("401", "402", "403", "404")):
        return False
    markers = ("timeout", "timed out", "deadline_exceeded", "connect", "remoteprotocol",
               "429", "resource_exhausted", "rate limit", "500", "502", "503", "504",
               "unavailable", "internal")
    return any(m in msg for m in markers)


class RetryingEmbeddings(Embeddings):
    """
    Bọc một Embeddings bất kỳ, tự thử lại khi gặp lỗi tạm thời (timeout, 5xx, 429).

    Cần thiết vì GoogleGenerativeAIEmbeddings không tự retry: chỉ 1 lần embed_content
    bị timeout là cả pipeline dừng. Backoff: 5s, 10s, 20s, 40s; riêng rate limit chờ 60s.
    """

    def __init__(self, inner: Embeddings, max_retries: int = 5, base_delay: float = 5.0):
        self.inner = inner
        self.max_retries = max_retries
        self.base_delay = base_delay

    def __getattr__(self, name):
        # Cho phép đọc thuộc tính của embeddings gốc (vd. .model)
        return getattr(self.inner, name)

    def _with_retry(self, fn, *args):
        import time
        for attempt in range(1, self.max_retries + 1):
            try:
                return fn(*args)
            except Exception as e:
                if not is_retryable_error(e) or attempt == self.max_retries:
                    raise
                msg = str(e).lower()
                rate_limited = "429" in msg or "resource_exhausted" in msg or "rate limit" in msg
                delay = 60 if rate_limited else self.base_delay * 2 ** (attempt - 1)
                print(f"⏳ Embedding lỗi tạm thời ({type(e).__name__}), "
                      f"thử lại sau {delay:.0f}s ({attempt}/{self.max_retries - 1}) ...")
                time.sleep(delay)

    def embed_documents(self, texts: list) -> list:
        return self._with_retry(self.inner.embed_documents, texts)

    def embed_query(self, text: str) -> list:
        return self._with_retry(self.inner.embed_query, text)


class HFInferenceEmbeddings(Embeddings):
    """
    LangChain-compatible Embeddings gọi Hugging Face Inference API (task feature-extraction).

    Không cần cài thêm langchain-huggingface: dùng trực tiếp huggingface_hub.InferenceClient.
    Mặc định model intfloat/multilingual-e5-large (đa ngôn ngữ, hỗ trợ tiếng Việt, 1024 chiều).
    """

    def __init__(self, model: str, token: str, provider: str = "hf-inference", batch_size: int = 32):
        from huggingface_hub import InferenceClient
        self.model = model
        self.batch_size = batch_size
        self.client = InferenceClient(provider=provider, api_key=token)

    def _embed(self, texts: list) -> list:
        import numpy as np
        vectors = np.asarray(self.client.feature_extraction(texts, model=self.model, normalize=True))
        if vectors.ndim == 1:          # 1 văn bản có thể trả về vector 1 chiều
            vectors = vectors[None, :]
        return vectors.tolist()

    def embed_documents(self, texts: list) -> list:
        """Embed danh sách văn bản theo lô `batch_size` để tránh request quá lớn."""
        result = []
        for start in range(0, len(texts), self.batch_size):
            result.extend(self._embed(texts[start:start + self.batch_size]))
        return result

    def embed_query(self, text: str) -> list:
        return self._embed([text])[0]

    async def aembed_documents(self, texts: list) -> list:
        import asyncio
        return await asyncio.to_thread(self.embed_documents, texts)

    async def aembed_query(self, text: str) -> list:
        import asyncio
        return await asyncio.to_thread(self.embed_query, text)
