# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

import re
from hashlib import sha256
from typing import TYPE_CHECKING

from pyavd._eos_designs.eos_designs_facts.facts_generator import FactsGenerator, facts_contributor
from pyavd._utils import default
from pyavd.j2filters import natural_sort

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pyavd._eos_designs.eos_designs_facts.schema import EosDesignsFacts
    from pyavd._eos_designs.schema import EosDesigns
    from pyavd._eos_designs.shared_utils import SharedUtilsProtocol


class FactsStageOneAndAHalf(FactsGenerator):
    """
    `FactsStageOne` is based on `FactsGeneratorProtocol`, so make sure to read the description there first.

    All methods should only rely on the device's own inputs.
    """

    @facts_contributor
    def uplink_peers(self: FactsStageOneAndAHalf) -> None:
        """
        Exposed in avd_switch_facts.

        Sorted list of all **unique** uplink peers.
        These are used to generate the "avd_topology_peers" fact covering downlinks for all devices.
        """
        # Since uplinks logic silently skips extra entries in uplink vars, we only need to parse shortest list.
        min_length = min(len(self.shared_utils.uplink_switch_interfaces), len(self.shared_utils.uplink_interfaces), len(self.shared_utils.uplink_switches))

        # Using set to only get unique uplink switches
        unique_uplink_switches = set(self.shared_utils.uplink_switches[:min_length])
        self.facts.uplink_peers.extend(natural_sort(unique_uplink_switches))

    @facts_contributor
    def local_short_esi(self: FactsStageOneAndAHalf) -> None:
        """
        If short_esi is set to "auto" we will use sha256 to create a unique short_esi value based on various uplink information.

        Note: Secondary MLAG switch should have the same short-esi value
        as primary MLAG switch.
        """
        short_esi = self.shared_utils.node_config.short_esi
        if short_esi == "auto":
            esi_seed_1 = "".join(self.shared_utils.uplink_switches[:2])
            esi_seed_2 = "".join(self.shared_utils.uplink_switch_interfaces[:2])
            esi_seed_3 = "".join(self.shared_utils.uplink_interfaces[:2])
            esi_seed_4 = default(self.shared_utils.group, "")
            esi_hash = sha256(f"{esi_seed_1}{esi_seed_2}{esi_seed_3}{esi_seed_4}".encode()).hexdigest()
            short_esi = re.sub(r"([0-9a-f]{4})", r"\1:", esi_hash)[:14]

        self.facts.local_short_esi = short_esi

    @facts_contributor
    def bgp_as(self) -> None:
        """Exposed in avd_switch_facts."""
        if self.shared_utils.underlay_router is True:
            self.facts.bgp_as = self.shared_utils.bgp_as

    def __init__(
        self, hostvars: Mapping, inputs: EosDesigns, facts: EosDesignsFacts, shared_utils: SharedUtilsProtocol, peer_facts: dict[str, EosDesignsFacts]
    ) -> None:
        self.peer_facts = peer_facts
        super().__init__(hostvars, inputs, facts, shared_utils)
