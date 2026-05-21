"""Event system primitives for Altinet LocalNode."""

from altinet.events.models import (
    AudioDetected,
    DeviceStateChanged,
    MotionDetected,
    PersonEnteredRoom,
    PersonLeftRoom,
    TimeTick,
)
from altinet.events.processor import EventProcessor
from altinet.events.queue import EventQueue

__all__ = [
    "AudioDetected",
    "DeviceStateChanged",
    "MotionDetected",
    "PersonEnteredRoom",
    "PersonLeftRoom",
    "TimeTick",
    "EventProcessor",
    "EventQueue",
]
