"""
Run expectancy (RE24) utilities.

Run expectancy answers "how many runs do we expect to score from this base state?"
Given the base occupation (first/second/third base runners) and the number of outs,
the RE24 matrix returns the expected runs scored for the rest of the inning.

The matrix below is the standard, season-long MLB average RE24 table indexed by
base state (8 states: empty, 1b, 2b, 12b, 3b, 13b, 23b, 123b) and outs (0, 1, 2).
"""

from __future__ import annotations

from typing import List, Optional, Tuple

# Base-state encoding: (on_first, on_second, on_third)
BASE_STATES: Tuple[Tuple[bool, bool, bool], ...] = (
    (False, False, False),  # 0
    (True, False, False),   # 1b
    (False, True, False),   # 2b
    (True, True, False),    # 12b
    (False, False, True),   # 3b
    (True, False, True),    # 13b
    (False, True, True),    # 23b
    (True, True, True),     # 123b
)

# Standard MLB-average RE24 run-expectancy values.
# Row = outs (0, 1, 2); column = base state (empty -> loaded).
_RUN_EXPECTANCY_TABLE: List[List[float]] = [
    # 0 outs : empty, 1b, 2b, 12b, 3b, 13b, 23b, 123b
    [0.515, 0.888, 1.171, 1.430, 1.171, 1.483, 1.755, 2.476],
    # 1 out
    [0.251, 0.517, 0.764, 1.008, 0.764, 1.027, 1.279, 1.755],
    # 2 outs
    [0.099, 0.195, 0.308, 0.424, 0.308, 0.432, 0.551, 0.772],
]


def _encode_bases(on_first: bool, on_second: bool, on_third: bool) -> int:
    """Return the base-state index for a given occupation."""
    for idx, (f, s, t) in enumerate(BASE_STATES):
        if (f, s, t) == (on_first, on_second, on_third):
            return idx
    raise ValueError(f"Invalid base state: {(on_first, on_second, on_third)}")


def get_expected_runs(on_first: bool, on_second: bool, on_third: bool, outs: int) -> float:
    """Expected runs scored from a base state with the given number of outs."""
    if outs < 0 or outs > 2:
        raise ValueError("outs must be 0, 1, or 2")
    idx = _encode_bases(on_first, on_second, on_third)
    return _RUN_EXPECTANCY_TABLE[outs][idx]


class RunExpectancyMatrix:
    """Container over the RE24 run-expectancy table."""

    def __init__(self, table: Optional[List[List[float]]] = None):
        self.table = table if table is not None else [row[:] for row in _RUN_EXPECTANCY_TABLE]

    def get_expected_runs(self, on_first: bool, on_second: bool, on_third: bool, outs: int) -> float:
        idx = _encode_bases(on_first, on_second, on_third)
        return self.table[outs][idx]

    def transition(self, on_first: bool, on_second: bool, on_third: bool, outs: int,
                    advance_runners: int, score: int) -> Tuple[int, int, bool, bool, bool]:
        """
        Advance runners by ``advance_runners`` bases and return the new state.

        Returns (runs_scored, new_outs, on_first, on_second, on_third).
        A hit with all bases empty and <3 bases to advance places the runner
        appropriately; otherwise runners are cleared past the hit distance.
        """
        runs = 0
        new = [on_first, on_second, on_third]

        # Advance existing runners past the hit distance.
        for i in range(2, -1, -1):
            if new[i]:
                pos = i + advance_runners
                if pos >= 3:
                    runs += 1
                else:
                    new[pos] = True

        # Place the batter.
        if advance_runners >= 3:
            runs += 1
        else:
            new[advance_runners] = True

        return runs, outs, new[0], new[1], new[2]


def calculate_wpa(on_first: bool, on_second: bool, on_third: bool, outs: int,
                  new_on_first: bool, new_on_second: bool, new_on_third: bool,
                  new_outs: int) -> float:
    """Win-probability-adjacent helper: the run swing from one base state to the next."""
    return get_expected_runs(on_first, on_second, on_third, outs) - get_expected_runs(
        new_on_first, new_on_second, new_on_third, new_outs
    )
