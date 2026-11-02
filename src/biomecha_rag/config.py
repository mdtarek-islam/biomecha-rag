"""Runtime settings read from environment variables.

Secrets come from the environment. In AWS Lambda the function reads them from
SSM Parameter Store by parameter name, so no secret value lives in Terraform state
or in the deployment package.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass


def _float(env: Mapping[str, str], key: str, default: float) -> float:
    raw = env.get(key)
    return default if raw in (None, "") else float(raw)


def _int(env: Mapping[str, str], key: str, default: int) -> int:
    raw = env.get(key)
    return default if raw in (None, "") else int(raw)


def _secret(env: Mapping[str, str], key: str) -> str:
    """Return a secret from ``key`` or from the SSM parameter named in ``key_SSM_PARAM``."""
    value = env.get(key, "")
    if value:
        return value
    param = env.get(f"{key}_SSM_PARAM", "")
    if not param:
        return ""
    import boto3  # available in the AWS Lambda Python runtime

    response = boto3.client("ssm").get_parameter(Name=param, WithDecryption=True)
    return response["Parameter"]["Value"]


@dataclass(frozen=True)
class Settings:
    hf_token: str = ""
    embed_endpoint_url: str = ""
    rerank_endpoint_url: str = ""
    llm_endpoint_url: str = ""
    pinecone_api_key: str = ""
    pinecone_index: str = "biomecha-rag"
    pinecone_namespace: str = "sports-science"
    bm25_params_path: str = "bm25_params.json"
    alpha: float = 0.5
    top_k: int = 20
    rerank_top_n: int = 5
    max_new_tokens: int = 512
    temperature: float = 0.1

    def __post_init__(self) -> None:
        if not 0.0 <= self.alpha <= 1.0:
            raise ValueError("alpha must be between 0 and 1")
        if self.top_k < 1 or self.rerank_top_n < 1:
            raise ValueError("top_k and rerank_top_n must be positive")

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        env = os.environ if env is None else env
        return cls(
            hf_token=_secret(env, "HF_TOKEN"),
            embed_endpoint_url=env.get("EMBED_ENDPOINT_URL", ""),
            rerank_endpoint_url=env.get("RERANK_ENDPOINT_URL", ""),
            llm_endpoint_url=env.get("LLM_ENDPOINT_URL", ""),
            pinecone_api_key=_secret(env, "PINECONE_API_KEY"),
            pinecone_index=env.get("PINECONE_INDEX", cls.pinecone_index),
            pinecone_namespace=env.get("PINECONE_NAMESPACE", cls.pinecone_namespace),
            bm25_params_path=env.get("BM25_PARAMS_PATH", cls.bm25_params_path),
            alpha=_float(env, "HYBRID_ALPHA", cls.alpha),
            top_k=_int(env, "RETRIEVE_TOP_K", cls.top_k),
            rerank_top_n=_int(env, "RERANK_TOP_N", cls.rerank_top_n),
            max_new_tokens=_int(env, "MAX_NEW_TOKENS", cls.max_new_tokens),
            temperature=_float(env, "TEMPERATURE", cls.temperature),
        )
