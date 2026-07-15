"""Run the repository-owned synthetic Inspection Copilot demo."""

from __future__ import annotations

import argparse
from pathlib import Path

from inspection_copilot.domain import (
    SOP,
    Assessment,
    InspectionCase,
    InspectionRequest,
    InspectionResult,
)
from inspection_copilot.service import FixtureInspector, run_inspection


def _demo_directory(repo_root: Path) -> Path:
    return (repo_root / "examples" / "synthetic").resolve(strict=True)


def load_demo_request(repo_root: Path) -> InspectionRequest:
    demo_directory = _demo_directory(repo_root)
    sop = SOP.model_validate_json((demo_directory / "sop.json").read_text(encoding="utf-8"))
    case = InspectionCase.model_validate_json(
        (demo_directory / "case.json").read_text(encoding="utf-8")
    )
    image_path = (demo_directory / case.image_ref).resolve(strict=True)
    try:
        image_path.relative_to(demo_directory)
    except ValueError as exc:
        raise ValueError("demo image must stay inside examples/synthetic") from exc
    if not image_path.is_file() or image_path.suffix.lower() != ".png":
        raise ValueError("demo image must be a PNG file")
    return InspectionRequest(sop=sop, case=case)


def run_demo(repo_root: Path) -> InspectionResult:
    demo_directory = _demo_directory(repo_root)
    request = load_demo_request(repo_root)
    assessment = Assessment.model_validate_json(
        (demo_directory / "assessment.json").read_text(encoding="utf-8")
    )
    return run_inspection(request, provider=FixtureInspector(assessment))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(run_demo(args.repo_root).model_dump_json(indent=2))


if __name__ == "__main__":
    main()
