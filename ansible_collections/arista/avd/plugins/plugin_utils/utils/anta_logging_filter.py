# Copyright (c) 2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
import logging


class AntaLibrariesFilter(logging.Filter):
    """Filter logs from ANTA and its underlying libraries."""

    _anta_libraries = ("anta", "asyncio", "asyncssh", "httpcore", "httpx")

    def __init__(self, mode: str = "exclude_all", *, tracker: dict | None = None) -> None:
        """Initialize filter with specific mode and optional warning tracker.

        Args:
            mode: Either 'exclude_all' or 'warnings_only'
            tracker: Optional dictionary to track if warnings occur
        """
        super().__init__()
        self.mode = mode
        self.tracker = tracker

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter logs based on configured mode.

        - exclude_all: Filter out all logs from ANTA libraries
        - warnings_only: Allow only warnings and above from ANTA libraries
        """
        is_anta_library = any(record.name.startswith(name) for name in self._anta_libraries)

        # Update the warning tracker if this is a warning or above from an ANTA library
        if self.tracker is not None and is_anta_library and record.levelno >= logging.WARNING:
            self.tracker["has_warnings"] = True

        if not is_anta_library:
            # Always include non-ANTA library logs
            return True

        if self.mode == "exclude_all":
            # Filter out all ANTA library logs
            return False
        if self.mode == "warnings_only":
            # Include only warnings and above from ANTA libraries
            return record.levelno >= logging.WARNING
        # Default: exclude all ANTA library logs
        return False
