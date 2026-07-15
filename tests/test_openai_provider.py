import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import httpx
import pytest
from openai import DefaultHttpxClient, OpenAI, OpenAIError

from inspection_copilot.demo import load_demo_request
from inspection_copilot.domain import Assessment, Decision, InspectionRequest
from inspection_copilot.openai_provider import (
    MAX_IMAGE_BYTES,
    OpenAIInspector,
    build_openai_inspector,
)
from inspection_copilot.service import run_inspection

REPO_ROOT = Path(__file__).resolve().parents[1]
IMAGE_ROOT = REPO_ROOT / "examples" / "synthetic"


class FakeResponses:
    def __init__(
        self,
        *,
        parsed: Assessment | None = None,
        error: Exception | None = None,
    ) -> None:
        self.parsed = parsed
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def parse(self, **kwargs: Any) -> SimpleNamespace:
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(output_parsed=self.parsed)


def _client(responses: FakeResponses) -> OpenAI:
    return cast(OpenAI, SimpleNamespace(responses=responses))


def _assessment() -> Assessment:
    return Assessment.model_validate_json(
        (IMAGE_ROOT / "assessment.json").read_text(encoding="utf-8")
    )


def test_provider_sends_bounded_strict_vision_request() -> None:
    responses = FakeResponses(parsed=_assessment())
    provider = OpenAIInspector(client=_client(responses), image_root=IMAGE_ROOT)

    assessment = provider.inspect(load_demo_request(REPO_ROOT))

    assert assessment == _assessment()
    assert len(responses.calls) == 1
    call = responses.calls[0]
    assert call["model"] == "gpt-5.6"
    assert call["store"] is False
    assert call["max_output_tokens"] == 2000
    assert call["timeout"] == 60.0
    assert call["reasoning"] == {"effort": "medium"}
    assert call["text_format"] is Assessment
    assert "SOLDER-BRIDGE-001" in call["input"][0]["content"][0]["text"]
    image_input = call["input"][0]["content"][1]
    assert image_input["type"] == "input_image"
    assert image_input["detail"] == "high"
    assert image_input["image_url"].startswith("data:image/png;base64,")


def test_sdk_serializes_strict_schema_at_http_boundary() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "id": "resp_test",
                "object": "response",
                "created_at": 1,
                "status": "completed",
                "error": None,
                "incomplete_details": None,
                "instructions": None,
                "max_output_tokens": 2000,
                "model": "gpt-5.6",
                "output": [
                    {
                        "id": "msg_test",
                        "type": "message",
                        "status": "completed",
                        "role": "assistant",
                        "content": [
                            {
                                "type": "output_text",
                                "annotations": [],
                                "logprobs": [],
                                "text": _assessment().model_dump_json(),
                            }
                        ],
                    }
                ],
                "parallel_tool_calls": True,
                "previous_response_id": None,
                "reasoning": {"effort": "medium", "summary": None},
                "store": False,
                "temperature": 1.0,
                "text": {"format": {"type": "text"}},
                "tool_choice": "auto",
                "tools": [],
                "top_logprobs": 0,
                "top_p": 1.0,
                "truncation": "disabled",
                "usage": None,
            },
            request=request,
        )

    http_client = DefaultHttpxClient(transport=httpx.MockTransport(handler))
    with OpenAI(api_key="test-key", max_retries=0, http_client=http_client) as client:
        provider = OpenAIInspector(client=client, image_root=IMAGE_ROOT)
        assessment = provider.inspect(load_demo_request(REPO_ROOT))

    assert assessment == _assessment()
    assert captured["model"] == "gpt-5.6"
    assert captured["store"] is False
    assert captured["max_output_tokens"] == 2000
    assert captured["text"]["format"]["type"] == "json_schema"
    assert captured["text"]["format"]["strict"] is True
    assert captured["text"]["format"]["schema"]["additionalProperties"] is False
    image_input = captured["input"][0]["content"][1]
    assert image_input["detail"] == "high"
    assert image_input["image_url"].startswith("data:image/png;base64,")


def test_default_builder_disables_sdk_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    constructor_kwargs: dict[str, object] = {}

    class FakeOpenAI:
        def __init__(self, **kwargs: object) -> None:
            constructor_kwargs.update(kwargs)

    monkeypatch.setattr("inspection_copilot.openai_provider.OpenAI", FakeOpenAI)

    provider = build_openai_inspector(image_root=IMAGE_ROOT, api_key="test-key")

    assert provider.model == "gpt-5.6"
    assert constructor_kwargs == {
        "api_key": "test-key",
        "max_retries": 0,
        "timeout": 60.0,
    }


def test_provider_rejects_image_path_escape_before_request(tmp_path: Path) -> None:
    image_root = tmp_path / "images"
    image_root.mkdir()
    (tmp_path / "outside.png").write_bytes(b"not-an-image")
    request = load_demo_request(REPO_ROOT).model_copy(deep=True)
    request.case.image_ref = "../outside.png"
    responses = FakeResponses(parsed=_assessment())
    provider = OpenAIInspector(client=_client(responses), image_root=image_root)

    with pytest.raises(ValueError, match="inside the configured image root"):
        provider.inspect(cast(InspectionRequest, request))

    assert responses.calls == []


def test_provider_rejects_oversized_image_before_request(tmp_path: Path) -> None:
    image_root = tmp_path / "images"
    image_root.mkdir()
    (image_root / "large.png").write_bytes(b"0" * (MAX_IMAGE_BYTES + 1))
    request = load_demo_request(REPO_ROOT).model_copy(deep=True)
    request.case.image_ref = "large.png"
    responses = FakeResponses(parsed=_assessment())
    provider = OpenAIInspector(client=_client(responses), image_root=image_root)

    with pytest.raises(ValueError, match="10 MiB"):
        provider.inspect(cast(InspectionRequest, request))

    assert responses.calls == []


@pytest.mark.parametrize(
    "responses",
    [
        FakeResponses(parsed=None),
        FakeResponses(error=OpenAIError("private provider detail")),
    ],
)
def test_provider_failure_becomes_sanitized_human_review(responses: FakeResponses) -> None:
    provider = OpenAIInspector(client=_client(responses), image_root=IMAGE_ROOT)

    result = run_inspection(load_demo_request(REPO_ROOT), provider=provider)

    assert result.final_decision is Decision.NEEDS_REVIEW
    assert result.evidence_complete is False
    assert result.assessment.proposed_decision is Decision.NEEDS_REVIEW
    assert result.assessment.evidence == []
    assert result.assessment.confidence == 0.0
    assert result.assessment.summary == "Inspection provider did not return a valid assessment."
    assert "private provider detail" not in result.model_dump_json()
