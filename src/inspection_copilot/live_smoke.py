"""One-request live validation orchestration for repository-owned synthetic data."""

from __future__ import annotations

import argparse
import os
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Protocol

from openai import OpenAIError
from pydantic import Field

from inspection_copilot.demo import DemoScenario, load_demo_request
from inspection_copilot.domain import Decision, ProviderStatus, StrictModel
from inspection_copilot.live_evidence import (
    LiveEvidenceWriteStatus,
    build_live_evidence,
    write_live_evidence,
)
from inspection_copilot.openai_provider import build_openai_inspector
from inspection_copilot.service import Inspector, execute_inspection

DEFAULT_LIVE_EVIDENCE_RELATIVE_PATH = Path("evidence/live_validation_evidence.json")
_RESERVED_MARKER = b"reserved-before-provider-construction\n"
_REQUEST_BOUNDARY_MARKER = b"request-may-have-started\n"


class LiveProviderFactory(Protocol):
    def __call__(self, *, image_root: Path) -> Inspector: ...


class LiveSmokeReceipt(StrictModel):
    """Sanitized CLI output proving where the persisted record can be found."""

    schema_version: Literal["1.0"] = "1.0"
    record_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    provider_status: ProviderStatus
    final_decision: Decision
    write_status: LiveEvidenceWriteStatus


def live_smoke_marker_path(evidence_path: Path) -> Path:
    return evidence_path.with_name(f".{evidence_path.name}.request")


def run_live_smoke(
    *,
    repo_root: Path,
    evidence_path: Path,
    live_provider_factory: LiveProviderFactory = build_openai_inspector,
    scenario: DemoScenario = DemoScenario.BRIDGE_FAIL,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> LiveSmokeReceipt:
    """Run at most one provider inspection and persist only sanitized evidence."""

    request = load_demo_request(repo_root, scenario=scenario)
    image_root = (repo_root / "examples" / "synthetic").resolve(strict=True)
    marker_path = live_smoke_marker_path(evidence_path)
    _reserve_request(evidence_path, marker_path)

    try:
        provider = live_provider_factory(image_root=image_root)
    except Exception:
        marker_path.unlink(missing_ok=True)
        raise

    if _path_entry_exists(evidence_path):
        marker_path.unlink(missing_ok=True)
        raise FileExistsError("live evidence already exists")

    try:
        _mark_request_boundary(marker_path)
    except Exception:
        marker_path.unlink(missing_ok=True)
        raise

    execution = execute_inspection(request, provider=provider)
    record = build_live_evidence(
        execution.result,
        provider_status=execution.outcome.status,
        recorded_at=clock(),
    )
    write_result = write_live_evidence(evidence_path, record)
    marker_path.unlink(missing_ok=True)
    return LiveSmokeReceipt(
        record_id=record.record_id,
        provider_status=record.provider_status,
        final_decision=record.final_decision,
        write_status=write_result.status,
    )


def _reserve_request(evidence_path: Path, marker_path: Path) -> None:
    if not evidence_path.parent.is_dir():
        raise FileNotFoundError("live evidence parent directory must exist")
    if _path_entry_exists(evidence_path):
        raise FileExistsError("live evidence already exists")
    try:
        descriptor = os.open(marker_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise FileExistsError("live smoke reservation already exists") from exc
    try:
        with os.fdopen(descriptor, "wb") as marker_file:
            marker_file.write(_RESERVED_MARKER)
            marker_file.flush()
            os.fsync(marker_file.fileno())
    except Exception:
        marker_path.unlink(missing_ok=True)
        raise
    if _path_entry_exists(evidence_path):
        marker_path.unlink(missing_ok=True)
        raise FileExistsError("live evidence already exists")


def _path_entry_exists(path: Path) -> bool:
    return os.path.lexists(path)


def _mark_request_boundary(marker_path: Path) -> None:
    with marker_path.open("wb") as marker_file:
        marker_file.write(_REQUEST_BOUNDARY_MARKER)
        marker_file.flush()
        os.fsync(marker_file.fileno())


def main(
    argv: Sequence[str] | None = None,
    *,
    live_provider_factory: LiveProviderFactory = build_openai_inspector,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--scenario",
        type=DemoScenario,
        choices=tuple(DemoScenario),
        default=DemoScenario.BRIDGE_FAIL,
    )
    parser.add_argument(
        "--evidence-path",
        type=Path,
        help="no-clobber output path; defaults inside the repository evidence directory",
    )
    parser.add_argument(
        "--confirm-one-live-request",
        action="store_true",
        help="authorize at most one OpenAI API request that may incur cost",
    )
    args = parser.parse_args(argv)

    if not args.confirm_one_live_request:
        parser.error("live smoke requires --confirm-one-live-request")
    evidence_path = args.evidence_path or args.repo_root / DEFAULT_LIVE_EVIDENCE_RELATIVE_PATH
    try:
        receipt = run_live_smoke(
            repo_root=args.repo_root,
            evidence_path=evidence_path,
            live_provider_factory=live_provider_factory,
            scenario=args.scenario,
            clock=clock,
        )
    except OpenAIError:
        parser.error("Live provider unavailable; verify OPENAI_API_KEY")
    except (FileExistsError, FileNotFoundError) as exc:
        parser.error(str(exc))
    except Exception:
        parser.error("Live smoke stopped; inspect the reservation before any retry")
    print(receipt.model_dump_json(indent=2))


if __name__ == "__main__":
    main()


__all__ = [
    "DEFAULT_LIVE_EVIDENCE_RELATIVE_PATH",
    "LiveSmokeReceipt",
    "live_smoke_marker_path",
    "main",
    "run_live_smoke",
]
