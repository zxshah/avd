# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.

# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pyavd._eos_designs.shared_utils import SharedUtils

from .schema import EosDesignsFacts
from .stage_four import FactsStageFour
from .stage_one import FactsStageOne
from .stage_one_and_a_half import FactsStageOneAndAHalf
from .stage_three import FactsStageThree
from .stage_two import FactsStageTwo

if TYPE_CHECKING:
    from collections.abc import Mapping

    from ansible.template import Templar

    from pyavd._eos_designs.schema import EosDesigns
    from pyavd.api.pool_manager import PoolManager


@dataclass
class OneDeviceData:
    facts: EosDesignsFacts
    hostvars: Mapping
    inputs: EosDesigns
    shared_utils: SharedUtils


def get_facts(
    *,
    all_inputs: dict[str, EosDesigns],
    pool_manager: PoolManager | None = None,
    all_hostvars: dict[str, dict] | None = None,
    templar: Templar | None = None,
) -> dict[str, EosDesignsFacts]:
    """
    Generate structured_config for a device.

    Args:
        all_inputs:
            Dict of inputs loaded into the EosDesigns class keyed by hostnames.
        pool_manager:
            Optional instance of PoolManager for assigning resourrces from a pool.
        all_hostvars:
            Dict of dicts with raw inputs keys by hostnames.
        templar:
            The templar to use for rendering templates. If templar is unset, any calls to jinja templates will fail with Nonetype has no "_loader" attribute


    Returns:
        Dict of EosDesignsFacts instances keyed by hostnames.
    """
    if all_hostvars is None:
        all_hostvars = {}

    all_devices_data: dict[str, OneDeviceData] = {}
    all_facts: dict[str, EosDesignsFacts] = {}
    for hostname, inputs in all_inputs.items():
        hostvars = all_hostvars.get(hostname, {})

        # Initialize SharedUtils class to be passed to each python_module below.
        shared_utils = SharedUtils(hostname=hostname, hostvars=hostvars, inputs=inputs, templar=templar, pool_manager=pool_manager, peer_facts=all_facts)

        all_facts[hostname] = EosDesignsFacts()

        # Generate Stage One facts - TODO: evaluate if it is worth doing this with multiprocessing.
        FactsStageOne(hostvars=hostvars, inputs=inputs, facts=all_facts[hostname], shared_utils=shared_utils).render_facts()

        all_devices_data[hostname] = OneDeviceData(
            facts=all_facts[hostname],
            hostvars=hostvars,
            inputs=inputs,
            shared_utils=shared_utils,
        )

    # TODO: Rename things.
    for device_data in all_devices_data.values():
        # Generate Stage OneAndAHalf facts - TODO: evaluate if it is worth doing this with multiprocessing.
        FactsStageOneAndAHalf(
            hostvars=device_data.hostvars,
            inputs=device_data.inputs,
            facts=device_data.facts,
            shared_utils=device_data.shared_utils,
            peer_facts=all_facts,
        ).render_facts()

    for device_data in all_devices_data.values():
        # Generate Stage Three facts - NOTE: Not possible to do with multiprocessing.
        FactsStageThree(
            hostvars=device_data.hostvars,
            inputs=device_data.inputs,
            facts=device_data.facts,
            shared_utils=device_data.shared_utils,
            peer_facts=all_facts,
        ).render_facts()

    for device_data in all_devices_data.values():
        # Generate Stage Two facts - TODO: evaluate if it is worth doing this with multiprocessing.
        FactsStageTwo(
            hostvars=device_data.hostvars,
            inputs=device_data.inputs,
            facts=device_data.facts,
            shared_utils=device_data.shared_utils,
            peer_facts=all_facts,
        ).render_facts()

    for device_data in all_devices_data.values():
        # Generate Stage Four facts - TODO: evaluate if it is worth doing this with multiprocessing.
        FactsStageFour(
            hostvars=device_data.hostvars,
            inputs=device_data.inputs,
            facts=device_data.facts,
            shared_utils=device_data.shared_utils,
            peer_facts=all_facts,
        ).render_facts()

    return all_facts
