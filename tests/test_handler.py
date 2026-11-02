import base64
import json

import pytest

from biomecha_rag.handler import make_handler
from biomecha_rag.pipeline import Answer


class FakePipeline:
    def __init__(self, fail=False):
        self.fail = fail
        self.calls = []

    def ask(self, question, top_n=None):
        self.calls.append((question, top_n))
        if self.fail:
            raise RuntimeError("endpoint down")
        return Answer("Use trunk rotation [smash::0].", ["smash::0"], ["smash::0"])


def _event(body, b64=False):
    if b64:
        body = base64.b64encode(body.encode()).decode()
    return {"version": "2.0", "routeKey": "POST /ask", "body": body, "isBase64Encoded": b64}


def _call(handler, event):
    response = handler(event, None)
    return response["statusCode"], json.loads(response["body"])


def test_good_request_returns_answer():
    pipe = FakePipeline()
    status, body = _call(make_handler(lambda: pipe), _event('{"question": " smash? "}'))
    assert status == 200
    assert body["citations"] == ["smash::0"]
    assert pipe.calls == [("smash?", None)]


def test_base64_body_and_top_n():
    pipe = FakePipeline()
    event = _event(json.dumps({"question": "drag", "top_n": 3}), b64=True)
    status, _ = _call(make_handler(lambda: pipe), event)
    assert status == 200
    assert pipe.calls == [("drag", 3)]


def test_bad_json_returns_400():
    status, body = _call(make_handler(FakePipeline), _event("{not json"))
    assert status == 400
    assert body["error"] == "bad_request"


@pytest.mark.parametrize("body", ['{"top_n": 2}', '{"question": "   "}', '{"question": 5}',
                                  "[]", ""])
def test_missing_or_invalid_question_returns_400(body):
    status, _ = _call(make_handler(FakePipeline), _event(body))
    assert status == 400


@pytest.mark.parametrize("top_n", [0, 11, "3", True])
def test_invalid_top_n_returns_400(top_n):
    status, _ = _call(make_handler(FakePipeline),
                      _event(json.dumps({"question": "q", "top_n": top_n})))
    assert status == 400


def test_pipeline_error_returns_500_without_detail():
    status, body = _call(make_handler(lambda: FakePipeline(fail=True)), _event('{"question": "q"}'))
    assert status == 500
    assert "endpoint down" not in body["message"]


def test_pipeline_built_once_per_container():
    built = []

    def factory():
        built.append(1)
        return FakePipeline()

    handler = make_handler(factory)
    handler(_event('{"question": "a"}'))
    handler(_event('{"question": "b"}'))
    assert len(built) == 1


def test_module_handler_imports_without_cloud_sdks():
    from biomecha_rag import handler

    assert callable(handler.lambda_handler)
