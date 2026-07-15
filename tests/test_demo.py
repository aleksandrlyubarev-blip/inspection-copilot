import json
import subprocess
import sys
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest
from openai import OpenAIError

from inspection_copilot.demo import DemoScenario, load_demo_request, main, run_demo
from inspection_copilot.domain import Decision, InspectionResult
from inspection_copilot.live_evidence import load_live_evidence
from inspection_copilot.live_smoke import LiveSmokeReceipt, live_smoke_marker_path
from inspection_copilot.service import FixtureInspector

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_demo_uses_repository_owned_synthetic_image() -> None:
    request = load_demo_request(REPO_ROOT)
    image_path = REPO_ROOT / "examples" / "synthetic" / request.case.image_ref

    assert image_path.is_file()
    assert image_path.suffix == ".png"
    assert "synthetic" in request.case.context.lower()
    assert request.image_sha256 == sha256(image_path.read_bytes()).hexdigest()


def test_fixture_demo_is_deterministic_and_evidence_backed() -> None:
    first = run_demo(REPO_ROOT)
    second = run_demo(REPO_ROOT)

    assert first == second
    assert first.final_decision is Decision.FAIL
    assert first.evidence_complete is True
    assert first.assessment.evidence[0].sop_rule_id == "SOLDER-BRIDGE-001"
    assert first.model == "fixture-inspector-v1"
    assert first.provenance.schema_version == "1.0"
    assert first.provenance.requested_model == "fixture-inspector-v1"
    assert first.provenance.effective_model == "fixture-inspector-v1"
    assert first.provenance.prompt_version == "fixture-v1"
    assert first.provenance.policy_version == "evidence-policy-v1"
    assert first.provenance.image_sha256 == load_demo_request(REPO_ROOT).image_sha256

    canonical_sop = json.dumps(
        load_demo_request(REPO_ROOT).sop.model_dump(mode="json"),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    assert first.provenance.sop_sha256 == sha256(canonical_sop).hexdigest()


def test_ambiguous_demo_fails_closed_to_human_review() -> None:
    result = run_demo(REPO_ROOT, scenario=DemoScenario.AMBIGUOUS)

    assert result.final_decision is Decision.NEEDS_REVIEW
    assert result.evidence_complete is False
    assert result.review_reasons


def test_demo_cli_outputs_schema_valid_json_without_credentials() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "inspection_copilot.demo", "--repo-root", str(REPO_ROOT)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    result = InspectionResult.model_validate_json(completed.stdout)
    payload = json.loads(completed.stdout)
    assert result.final_decision is Decision.FAIL
    assert payload["model"] == "fixture-inspector-v1"


def test_ambiguous_cli_is_deterministic() -> None:
    command = [
        sys.executable,
        "-m",
        "inspection_copilot.demo",
        "--repo-root",
        str(REPO_ROOT),
        "--scenario",
        "ambiguous",
    ]

    first = subprocess.run(command, cwd=REPO_ROOT, check=True, capture_output=True, text=True)
    second = subprocess.run(command, cwd=REPO_ROOT, check=True, capture_output=True, text=True)

    assert first.stdout == second.stdout
    assert (
        InspectionResult.model_validate_json(first.stdout).final_decision is Decision.NEEDS_REVIEW
    )


def test_live_cli_requires_explicit_confirmation(capsys: Any) -> None:
    def forbidden_factory(*, image_root: Path) -> FixtureInspector:
        raise AssertionError(f"live provider must not be built for {image_root}")

    with pytest.raises(SystemExit) as error:
        main(
            ["--repo-root", str(REPO_ROOT), "--provider", "openai"],
            live_provider_factory=forbidden_factory,
        )

    assert error.value.code == 2
    assert "--confirm-live-request" in capsys.readouterr().err


def test_confirmed_live_cli_routes_through_one_request_runner(
    tmp_path: Path,
    capsys: Any,
) -> None:
    evidence_path = tmp_path / "live_validation_evidence.json"
    image_roots: list[Path] = []
    inspected_cases: list[str] = []

    class CountingInspector(FixtureInspector):
        def inspect(self, request: Any) -> Any:
            inspected_cases.append(request.case.case_id)
            return super().inspect(request)

    def fixture_factory(*, image_root: Path) -> FixtureInspector:
        image_roots.append(image_root)
        assessment = run_demo(REPO_ROOT).assessment
        return CountingInspector(assessment)

    main(
        [
            "--repo-root",
            str(REPO_ROOT),
            "--provider",
            "openai",
            "--confirm-live-request",
            "--live-evidence-path",
            str(evidence_path),
        ],
        live_provider_factory=fixture_factory,
    )

    assert image_roots == [(REPO_ROOT / "examples" / "synthetic").resolve()]
    assert inspected_cases == ["synthetic-bridge-001"]
    receipt = LiveSmokeReceipt.model_validate_json(capsys.readouterr().out)
    assert receipt.final_decision is Decision.FAIL
    assert load_live_evidence(evidence_path).record_id == receipt.record_id
    assert not live_smoke_marker_path(evidence_path).exists()


def test_live_cli_sanitizes_provider_construction_error(
    tmp_path: Path,
    capsys: Any,
) -> None:
    evidence_path = tmp_path / "live_validation_evidence.json"

    def unavailable_factory(*, image_root: Path) -> FixtureInspector:
        raise OpenAIError(f"private credential detail for {image_root}")

    with pytest.raises(SystemExit) as error:
        main(
            [
                "--repo-root",
                str(REPO_ROOT),
                "--provider",
                "openai",
                "--confirm-live-request",
                "--live-evidence-path",
                str(evidence_path),
            ],
            live_provider_factory=unavailable_factory,
        )

    stderr = capsys.readouterr().err
    assert error.value.code == 2
    assert "Live provider unavailable; verify OPENAI_API_KEY" in stderr
    assert "private credential detail" not in stderr
    assert not evidence_path.exists()
    assert not live_smoke_marker_path(evidence_path).exists()
