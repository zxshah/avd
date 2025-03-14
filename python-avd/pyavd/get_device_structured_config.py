# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyavd._eos_designs.eos_designs_facts.schema import EosDesignsFacts


def get_device_structured_config(hostname: str, inputs: dict, avd_facts: dict[str, EosDesignsFacts]) -> dict:
    """
    Build and return the AVD structured configuration for one device.

    Args:
        hostname: Hostname of device.
        inputs: Dictionary with inputs for "eos_designs".
            Variables should be converted and validated according to AVD `eos_designs` schema first using `pyavd.validate_inputs`.
        avd_facts: Dictionary of avd_facts as returned from `pyavd.get_avd_facts`.

    Returns:
        Device Structured Configuration as a dictionary
    """
    # pylint: disable=import-outside-toplevel
    from pyavd._eos_designs.schema import EosDesigns
    from pyavd._eos_designs.structured_config import get_structured_config

    # pylint: enable=import-outside-toplevel

    # Load input vars into the EosDesigns data class.
    loaded_inputs = EosDesigns._from_dict(inputs)

    # We do not validate input variables in this stage (done in "validate_inputs")
    structured_config = get_structured_config(
        hostname=hostname,
        hostvars=inputs,
        inputs=loaded_inputs,
        all_facts=avd_facts,
        templar=None,
    )

    return structured_config._as_dict()
