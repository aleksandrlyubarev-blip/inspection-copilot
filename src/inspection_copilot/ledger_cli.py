"""Build the repository-owned sanitized offline inspection ledger."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from inspection_copilot.demo import DemoScenario, run_demo
from inspection_copilot.ledger import InspectionLedger, entry_from_result, write_ledger

_OFFLINE_SCENARIOS = (
    DemoScenario.BRIDGE_FAIL,
    DemoScenario.AMBIGUOUS,
)


def build_offline_ledger(repo_root: Path) -> InspectionLedger:
    return InspectionLedger(
        entries=[
            entry_from_result(run_demo(repo_root, scenario=scenario))
            for scenario in _OFFLINE_SCENARIOS
        ]
    )


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="existing-parent path for the sanitized deterministic JSON ledger",
    )
    args = parser.parse_args(argv)
    ledger = build_offline_ledger(args.repo_root)
    write_ledger(args.output, ledger)
    print(ledger.model_dump_json(indent=2))


if __name__ == "__main__":
    main()


__all__ = ["build_offline_ledger", "main"]
