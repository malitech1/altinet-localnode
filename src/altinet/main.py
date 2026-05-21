"""CLI entrypoint for Altinet LocalNode."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from altinet.context.contextualiser import build_context_block
from altinet.context.schemas import HouseState, PossibleAction
from altinet.decision.prompt_builder import build_decision_prompt


DEFAULT_SAMPLE_PATH = Path("examples/sample_house_state.json")
DEFAULT_ACTIONS = [
    PossibleAction.TURN_LIGHT_ON,
    PossibleAction.TURN_LIGHT_OFF,
    PossibleAction.DO_NOTHING,
]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="altinet-localnode")
    subparsers = parser.add_subparsers(dest="command")

    contextualise_parser = subparsers.add_parser(
        "contextualise", help="Render a natural-language context block from a HouseState JSON file."
    )
    contextualise_parser.add_argument(
        "--sample-path",
        type=Path,
        default=DEFAULT_SAMPLE_PATH,
        help="Path to a HouseState JSON file (default: examples/sample_house_state.json).",
    )
    contextualise_parser.add_argument(
        "--event",
        action="append",
        default=[],
        help="Recent event text. Can be provided multiple times.",
    )

    build_prompt_parser = subparsers.add_parser(
        "build-prompt", help="Build a complete decision prompt from a HouseState JSON file."
    )
    build_prompt_parser.add_argument(
        "sample_path",
        type=Path,
        help="Path to a HouseState JSON file, e.g. examples/sample_house_state.json.",
    )
    build_prompt_parser.add_argument(
        "--event",
        action="append",
        default=[],
        help="Recent event text. Can be provided multiple times.",
    )

    args = parser.parse_args(argv)

    if args.command == "contextualise":
        print(_contextualise_from_path(args.sample_path, args.event))
        return

    if args.command == "build-prompt":
        print(_build_prompt_from_path(args.sample_path, args.event))
        return

    print("Altinet LocalNode running")


def _contextualise_from_path(sample_path: Path, events: list[str]) -> str:
    with sample_path.open("r", encoding="utf-8") as fh:
        house_state = HouseState.model_validate(json.load(fh))
    return build_context_block(house_state=house_state, recent_events=events)


def _build_prompt_from_path(sample_path: Path, events: list[str]) -> str:
    with sample_path.open("r", encoding="utf-8") as fh:
        house_state = HouseState.model_validate(json.load(fh))
    return build_decision_prompt(house_state=house_state, possible_actions=DEFAULT_ACTIONS, recent_events=events)


if __name__ == "__main__":
    main()
