# Copyright (c) 2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def read_json_file(file: Path, file_context: str) -> dict:
    try:
        with file.open("r") as stream:
            data = json.load(stream)
            if not isinstance(data, dict):
                msg = f"Expected a 'dict' when reading data from {file_context}. Got {type(data)}."
            return data
    except OSError as e:
        msg = f"Unable to read {file_context}: {e}"
        raise type(e)(msg) from e
    except json.JSONDecodeError as e:
        msg = f"Unable to decode {file_context}: {e}"
        raise type(e)(msg, e.doc, e.pos) from e
