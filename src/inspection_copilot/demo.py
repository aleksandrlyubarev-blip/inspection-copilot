"""Run the repository-owned synthetic Inspection Copilot demo."""

from __future__ import annotations

import argparse
from enum import StrEnum
from pathlib import Path

from inspection_copilot.domain import (
    SOP,
    Assessment,
    InspectionCase,
    InspectionRequest,
    InspectionResult,
)
from inspection_copilot.service import FixtureInspector, run_inspection


class DemoScenario(StrEnum):
    """Repository-owned scenarios available to the offline demo."""

    BRIDGE_FAIL = "bridge_fail"
    AMBIGUOUS = "ambiguous"


_SCENARIO_FILES = {
    DemoScenario.BRIDGE_FAIL: ("case.json", "assessment.json"),
    DemoScenario.AMBIGUOUS: ("case_ambiguous.json", "assessment_ambiguous.json"),
}


def _demo_directory(repo_root: Path) -> Path:
    return (repo_root / "examples" / "synthetic").resolve(strict=True)


def load_demo_request(
    repo_root: Path,
    *,
    scenario: DemoScenario = DemoScenario.BRIDGE_FAIL,
) -> InspectionRequest:
    demo_directory = _demo_directory(repo_root)
    case_file, _ = _SCENARIO_FILES[scenario]
    sop = SOP.model_validate_json((demo_directory / "sop.json").read_text(encoding="utf-8"))
    case = InspectionCase.model_validate_json(
        (demo_directory / case_file).read_text(encoding="utf-8")
    )
    image_path = (demo_directory / case.image_ref).resolve(strict=True)
    try:
        image_path.relative_to(demo_directory)
    except ValueError as exc:
        raise ValueError("demo image must stay inside examples/synthetic") from exc
    if not image_path.is_file() or image_path.suffix.lower() != ".png":
        raise ValueError("demo image must be a PNG file")
    return InspectionRequest(sop=sop, case=case)


def run_demo(
    repo_root: Path,
    *,
    scenario: DemoScenario = DemoScenario.BRIDGE_FAIL,
) -> InspectionResult:
    demo_directory = _demo_directory(repo_root)
    _, assessment_file = _SCENARIO_FILES[scenario]
    request = load_demo_request(repo_root, scenario=scenario)
    assessment = Assessment.model_validate_json(
        (demo_directory / assessment_file).read_text(encoding="utf-8")
    )
    return run_inspection(request, provider=FixtureInspector(assessment))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--scenario",
        type=DemoScenario,
        choices=tuple(DemoScenario),
        default=DemoScenario.BRIDGE_FAIL,
    )
    args = parser.parse_args()
    print(run_demo(args.repo_root, scenario=args.scenario).model_dump_json(indent=2))


if __name__ == "__main__":
    main()


__all__ = ["DemoScenario", "load_demo_request", "run_demo"]
