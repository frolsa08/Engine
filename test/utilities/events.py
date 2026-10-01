"""Common event shape emitted by passive verification monitors."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MonitorEvent:
    cycle: int
    source: str
    kind: str
    payload: dict[str, Any]