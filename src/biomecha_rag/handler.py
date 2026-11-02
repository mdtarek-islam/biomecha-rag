"""AWS Lambda handler for API Gateway HTTP API proxy events (payload v2.0).

Request: ``POST /ask`` with JSON ``{"question": str, "top_n": int (optional)}``.
Responses: 200 answer, 400 invalid input, 500 internal error.
Lambda only orchestrates. Embedding, reranking and generation run on
Hugging Face Inference Endpoints.
"""

from __future__ import annotations

import base64
import json
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

MAX_QUESTION_CHARS = 2000
MAX_TOP_N = 10


class BadRequest(ValueError):
    pass


def _response(status: int, body: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def parse_request(event: dict) -> tuple[str, int | None]:
    raw = event.get("body")
    if raw is None or raw == "":
        raise BadRequest("request body is required")
    if event.get("isBase64Encoded"):
        try:
            raw = base64.b64decode(raw).decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise BadRequest("body is not valid base64 UTF-8") from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise BadRequest("body is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise BadRequest("body must be a JSON object")

    question = payload.get("question")
    if not isinstance(question, str) or not question.strip():
        raise BadRequest("'question' must be a non-empty string")
    if len(question) > MAX_QUESTION_CHARS:
        raise BadRequest(f"'question' exceeds {MAX_QUESTION_CHARS} characters")

    top_n = payload.get("top_n")
    if top_n is not None and (isinstance(top_n, bool) or not isinstance(top_n, int)
                              or not 1 <= top_n <= MAX_TOP_N):
        raise BadRequest(f"'top_n' must be an integer from 1 to {MAX_TOP_N}")
    return question.strip(), top_n


def make_handler(pipeline_factory: Callable[[], Any]) -> Callable[[dict, Any], dict]:
    """Build a handler that creates the pipeline once per warm container."""
    cache: dict[str, Any] = {}

    def handler(event: dict, context: Any = None) -> dict:
        try:
            question, top_n = parse_request(event or {})
        except BadRequest as exc:
            return _response(400, {"error": "bad_request", "message": str(exc)})
        try:
            if "pipeline" not in cache:
                cache["pipeline"] = pipeline_factory()
            answer = cache["pipeline"].ask(question, top_n=top_n)
        except Exception:
            logger.exception("pipeline failure")
            return _response(500, {"error": "internal_error",
                                   "message": "the answer could not be generated"})
        return _response(200, answer.as_dict())

    return handler


def _default_factory():
    from biomecha_rag.pipeline import build_pipeline

    return build_pipeline()


lambda_handler = make_handler(_default_factory)
