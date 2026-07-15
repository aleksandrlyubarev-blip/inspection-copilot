import json
import subprocess
import sys
from pathlib import Path

from inspection_copilot.demo import load_demo_request, run_demo
from inspection_copilot.domain import Decision, InspectionResult

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_demo_uses_repository_owned_synthetic_image() -> None:
    request = load_demo_request(REPO_ROOT)
    image_path = REPO_ROOT / "examples" / "synthetic" / request.case.image_ref

    assert image_path.is_file()
    assert image_path.suffix == ".png"
    assert "synthetic" in request.case.context.lower()


def test_fixture_demo_is_deterministic_and_evidence_backed() -> None:
    first = run_demo(REPO_ROOT)
    second = run_demo(REPO_ROOT)

    assert first == second
    assert first.final_decision is Decision.FAIL
    assert first.evidence_complete is True
    assert first.assessment.evidence[0].sop_rule_id == "SOLDER-BRIDGE-001"


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
