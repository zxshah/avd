# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from pyavd._eos_designs.eos_designs_facts.facts_generator import FactsGenerator, FactsGeneratorProtocol, facts_contributor
from pyavd._eos_designs.eos_designs_facts.schema import EosDesignsFacts
from pyavd.j2filters import natural_sort

from .uplinks import UplinksMixin

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pyavd._eos_designs.eos_designs_facts.schema import EosDesignsFacts
    from pyavd._eos_designs.schema import EosDesigns
    from pyavd._eos_designs.shared_utils import SharedUtilsProtocol


class FactsStageFourProtocol(UplinksMixin, FactsGeneratorProtocol, Protocol):
    peer_facts: dict[str, EosDesignsFacts]

    @facts_contributor
    def uplink_switch_vrfs(self: FactsStageFourProtocol) -> None:
        """
        Return the list of VRF names present on uplink switches.

        NOTE: This must be above the `uplinks` and `overlay` to ensure the fact has been set before filtered_tenants are parsed again.
        """
        if self.shared_utils.uplink_type != "p2p-vrfs":
            return

        vrfs = set()
        for uplink_switch in self.facts.uplink_peers:
            uplink_switch_facts = self.shared_utils.get_peer_facts(uplink_switch)
            vrfs.update(uplink_switch_facts.only_used_for_peer_facts.local_vrfs_in_use)

        self.facts.uplink_switch_vrfs.extend(natural_sort(vrfs))

    @facts_contributor
    def overlay(self: FactsStageFourProtocol) -> None:
        """Exposed in avd_switch_facts."""
        if self.shared_utils.underlay_router is True:
            self.facts.overlay._update(
                peering_address=self.shared_utils.overlay_peering_address,
                evpn_mpls=self.shared_utils.overlay_evpn_mpls,
            )


class FactsStageFour(FactsGenerator, FactsStageFourProtocol):
    """
    `FactsStageFour` is based on `FactsGeneratorProtocol`, so make sure to read the description there first.

    All methods relies on other device's facts either directly or indirectly, so this class has an extra argument of peer_facts, which is a dictionary
    with facts set during Stage One for all all other devices.
    """

    def __init__(
        self, hostvars: Mapping, inputs: EosDesigns, facts: EosDesignsFacts, shared_utils: SharedUtilsProtocol, peer_facts: dict[str, EosDesignsFacts]
    ) -> None:
        self.peer_facts = peer_facts
        super().__init__(hostvars, inputs, facts, shared_utils)

        if self.shared_utils.uplink_type == "p2p-vrfs":
            # Reset the cache of filtered tenants to allow to add in VRFs attracted from the uplink.
            self.shared_utils.__dict__.pop("filtered_tenants")
            self.shared_utils.__dict__.pop("vrfs")
