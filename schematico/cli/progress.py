from __future__ import annotations

import sys


class ProgressReporter:
    def __init__(self, table: str) -> None:
        self._table = table
        self._last_len = 0
        print(
            f"Generating data for table: '{table}'...",
            file=sys.stderr,
            flush=True,
        )

    def update(self, found: int, total: int, event: str) -> None:
        if event == "duplicate":
            msg = f"\r  Found duplicate — retrying...         "
        else:
            msg = f"\r  {found} of {total} entries found        "

        print(msg, end="", file=sys.stderr, flush=True)
        self._last_len = len(msg)

    def done(self, count: int) -> None:
        print(
            f"\r  Found data — {count} records generated.          ",
            file=sys.stderr,
            flush=True,
        )
        print("", file=sys.stderr)
