from datetime import datetime

from altinet.memory import EpisodicMemory, MemoryContext, MemorySystem


def test_retrieve_relevant_memories_prioritizes_matching_room_resident_time_and_tags():
    system = MemorySystem()
    system.add_memory(
        EpisodicMemory(
            event="Read bedtime story",
            importance=1.0,
            timestamp=datetime(2026, 5, 20, 20, 0),
            residents=["elliot", "mia"],
            rooms=["bedroom"],
            tags=["bedtime", "reading"],
        )
    )
    system.add_memory(
        EpisodicMemory(
            event="Cooked lunch",
            importance=2.0,
            timestamp=datetime(2026, 5, 20, 12, 0),
            residents=["elliot"],
            rooms=["kitchen"],
            tags=["cooking"],
        )
    )

    context = MemoryContext(
        current_time=datetime(2026, 5, 21, 20, 15),
        residents=["mia"],
        room="bedroom",
        tags=["bedtime"],
    )

    memories = system.retrieve_relevant_memories(context)

    assert memories[0].event == "Read bedtime story"


def test_retrieve_relevant_memories_honors_limit():
    system = MemorySystem()
    for idx in range(10):
        system.add_memory(
            EpisodicMemory(
                event=f"Event {idx}",
                importance=float(idx),
                timestamp=datetime(2026, 5, 20, 8, 0),
            )
        )

    context = MemoryContext(current_time=datetime(2026, 5, 20, 8, 0))
    memories = system.retrieve_relevant_memories(context, limit=3)

    assert len(memories) == 3
