from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import List, Optional

from sim.model import Multiverse


@dataclass
class History:
    """Stack of full multiverse snapshots for rewind. Includes RNG state via deepcopy."""

    snapshots: List[Multiverse] = field(default_factory=list)
    snapshot_every: int = 1
    max_history: Optional[int] = None

    def record(self, m: Multiverse) -> None:
        if m.global_tick % self.snapshot_every != 0:
            return
        self.snapshots.append(copy.deepcopy(m))
        if self.max_history is not None and len(self.snapshots) > self.max_history:
            overflow = len(self.snapshots) - self.max_history
            self.snapshots = self.snapshots[overflow:]

    def record_initial(self, m: Multiverse) -> None:
        """Call before first step; tick 0 state."""
        self.snapshots.append(copy.deepcopy(m))

    def truncate_after(self, step_index: int) -> None:
        """After rewind, drop future timeline. step_index is inclusive snapshot index."""
        self.snapshots = self.snapshots[: step_index + 1]

    def get_step_count(self) -> int:
        return len(self.snapshots)

    def restore(self, step_index: int) -> Multiverse:
        if step_index < 0 or step_index >= len(self.snapshots):
            raise IndexError("step_index out of range")
        return copy.deepcopy(self.snapshots[step_index])
