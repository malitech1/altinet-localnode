"""CLI entrypoint for Altinet LocalNode."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from altinet.context.contextualiser import build_context_block
from altinet.context.schemas import HouseState, PossibleAction
from altinet.decision.mock_engine import decide_action
from altinet.decision.openai_engine import decide_action_with_openai
from altinet.decision.prompt_builder import build_decision_prompt
from altinet.events.models import PersonEnteredRoom, TimeTick
from altinet.events.processor import EventProcessor
from altinet.events.queue import EventQueue
from altinet.memory import EpisodicMemory, MemoryContext, MemorySystem
from altinet.runtime.runtime_loop import run_runtime_loop
from altinet.perception.capture import capture_room_image
from altinet.perception.room_context import analyse_room_image_with_openai


DEFAULT_SAMPLE_PATH = Path("examples/sample_house_state.json")


DEFAULT_ROOM_CONTEXT_OUTPUT_PATH = Path("data/context/latest_room_context.json")
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

    decide_parser = subparsers.add_parser(
        "decide", help="Run a decision engine against a HouseState JSON file."
    )
    decide_parser.add_argument(
        "sample_path",
        type=Path,
        help="Path to a HouseState JSON file, e.g. examples/sample_house_state.json.",
    )
    decide_parser.add_argument(
        "--engine",
        choices=["mock_engine", "openai"],
        default="mock_engine",
        help="Decision engine to use (default: mock_engine).",
    )

    subparsers.add_parser(
        "capture-room",
        help="Capture a single image from the default webcam for perception testing.",
    )

    analyse_room_image_parser = subparsers.add_parser(
        "analyse-room-image",
        help="Extract room context JSON from an image using OpenAI Vision.",
    )
    analyse_room_image_parser.add_argument(
        "image_path",
        type=Path,
        help="Path to input room image, e.g. data/captures/latest.jpg.",
    )


    subparsers.add_parser(
        "simulate-events",
        help="Simulate a sequence of events and print contextual decision output.",
    )

    subparsers.add_parser(
        "memory-demo",
        help="Run a simple episodic memory retrieval demo.",
    )

    runtime_parser = subparsers.add_parser("runtime", help="Run the continuous LocalNode runtime loop.")
    runtime_parser.add_argument("--sample-path", type=Path, default=DEFAULT_SAMPLE_PATH)
    runtime_parser.add_argument("--tick-rate", type=float, default=1.0, help="Tick rate in Hz.")
    runtime_parser.add_argument("--max-ticks", type=int, default=None, help="Optional max ticks for bounded runs.")

    args = parser.parse_args(argv)

    if args.command == "contextualise":
        print(_contextualise_from_path(args.sample_path, args.event))
        return

    if args.command == "build-prompt":
        print(_build_prompt_from_path(args.sample_path, args.event))
        return

    if args.command == "decide":
        try:
            print(_decide_from_path(args.sample_path, engine=args.engine))
        except RuntimeError as exc:
            print(f"Decision error: {exc}")
        return


    if args.command == "simulate-events":
        print(_simulate_events_demo())
        return

    if args.command == "memory-demo":
        print(_memory_demo())
        return

    if args.command == "runtime":
        stats = run_runtime_loop(args.sample_path, tick_rate_hz=args.tick_rate, max_ticks=args.max_ticks)
        print(f"Runtime stopped after {stats.ticks} ticks; events={stats.events_processed}; decisions={stats.decisions_made}; errors={stats.loop_errors}")
        return

    if args.command == "capture-room":
        success, message = capture_room_image()
        prefix = "Capture complete:" if success else "Capture skipped:"
        print(f"{prefix} {message}")
        return


    if args.command == "analyse-room-image":
        try:
            context = analyse_room_image_with_openai(args.image_path)
            DEFAULT_ROOM_CONTEXT_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
            DEFAULT_ROOM_CONTEXT_OUTPUT_PATH.write_text(context.model_dump_json(indent=2), encoding="utf-8")
            print(f"Room context saved to {DEFAULT_ROOM_CONTEXT_OUTPUT_PATH}")
            print(context.model_dump_json(indent=2))
        except RuntimeError as exc:
            print(f"Room context error: {exc}")
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


def _decide_from_path(sample_path: Path, *, engine: str = "mock_engine") -> str:
    with sample_path.open("r", encoding="utf-8") as fh:
        house_state = HouseState.model_validate(json.load(fh))
    if engine == "openai":
        prompt = build_decision_prompt(
            house_state=house_state,
            possible_actions=DEFAULT_ACTIONS,
            recent_events=[],
        )
        decision = decide_action_with_openai(prompt)
        return decision.model_dump_json(indent=2)

    decision = decide_action(house_state)
    return decision.model_dump_json(indent=2)



def _simulate_events_demo() -> str:
    with DEFAULT_SAMPLE_PATH.open("r", encoding="utf-8") as fh:
        house_state = HouseState.model_validate(json.load(fh))

    queue = EventQueue()
    processor = EventProcessor()

    simulated_time = house_state.current_time.replace(hour=20, minute=0, second=0, microsecond=0)
    queue.push(
        PersonEnteredRoom(
            timestamp=simulated_time,
            source="simulation",
            confidence=0.99,
            person_id="resident_elliot",
            room_id="bedroom",
            metadata={"demo": "elliot_enters_bedroom"},
        )
    )
    queue.push(
        TimeTick(
            timestamp=simulated_time,
            source="clock",
            confidence=1.0,
            metadata={"tick": "8pm"},
        )
    )

    processor.process_all(house_state, queue)
    context = processor.contextualise(
        house_state,
        events=["Elliot entered bedroom at 8:00 PM"],
    )
    decision = processor.decide(house_state)

    return "\n".join(
        [
            "Simulated event: Elliot enters bedroom at 8:00 PM",
            "Updated context:",
            context,
            "Mock decision:",
            decision.model_dump_json(indent=2),
        ]
    )


def _memory_demo() -> str:
    memory_system = MemorySystem()

    memory_system.add_memory(
        EpisodicMemory(
            event="Elliot read a bedtime story to Mia.",
            importance=1.9,
            timestamp=datetime(2026, 5, 20, 20, 10),
            residents=["elliot", "mia"],
            rooms=["bedroom"],
            tags=["bedtime", "family", "reading"],
        )
    )
    memory_system.add_memory(
        EpisodicMemory(
            event="A package was delivered at the front door.",
            importance=1.2,
            timestamp=datetime(2026, 5, 20, 14, 45),
            residents=["elliot"],
            rooms=["entryway"],
            tags=["delivery", "door"],
        )
    )
    memory_system.add_memory(
        EpisodicMemory(
            event="Mia spilled juice in the kitchen.",
            importance=1.5,
            timestamp=datetime(2026, 5, 20, 8, 30),
            residents=["mia"],
            rooms=["kitchen"],
            tags=["cleanup", "kitchen"],
        )
    )

    context = MemoryContext(
        current_time=datetime(2026, 5, 21, 20, 0),
        residents=["mia", "elliot"],
        room="bedroom",
        tags=["bedtime", "family"],
    )

    memories = memory_system.retrieve_relevant_memories(context)
    lines = ["Memory demo: relevant episodic memories"]
    for idx, memory in enumerate(memories, start=1):
        lines.append(f"{idx}. {memory.event} (importance={memory.importance})")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
