# Copyright (c) 2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

import json
from collections import defaultdict
from typing import TYPE_CHECKING, Any

from ansible_collections.arista.avd.plugins.plugin_utils.pyavd_wrappers import RaiseOnUse

from .read_json_file import read_json_file

try:
    from pyavd._eos_designs.eos_designs_facts.schema import EosDesignsFacts
except ImportError as e:
    EosDesignsFacts = RaiseOnUse(ImportError(f"The 'arista.avd' collection requires the 'pyavd' Python library. Got import error {e}"))

if TYPE_CHECKING:
    from pathlib import Path


class AvdSwitchFactsDefaultDict(defaultdict):
    tmp_path: Path

    def __init__(self, tmp_path: Path, fabric_hosts: list[str]) -> None:
        self.fabric_hosts = fabric_hosts
        self.tmp_path = tmp_path

    def __contains__(self, key: object) -> bool:
        try:
            _dummy = self[key]
        except (OSError, json.JSONDecodeError):
            return False
        return True

    def get(self, key: str, default: Any = None) -> dict:
        try:
            return self[key]
        except (OSError, json.JSONDecodeError):
            return default

    def __missing__(self, key: str) -> dict:
        self[key] = EosDesignsFacts._from_dict(read_json_file(self.tmp_path / "device_facts" / f"{key}.json", f"AVD device facts for {key}"))
        return self[key]

    def keys(self) -> list[str]:
        return self.fabric_hosts
