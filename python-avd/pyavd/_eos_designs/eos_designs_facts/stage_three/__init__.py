# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from typing import TYPE_CHECKING

from pyavd._eos_designs.eos_designs_facts.facts_generator import FactsGenerator, facts_contributor
from pyavd._eos_designs.eos_designs_facts.schema import EosDesignsFacts

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pyavd._eos_designs.eos_designs_facts.schema import EosDesignsFacts
    from pyavd._eos_designs.schema import EosDesigns
    from pyavd._eos_designs.shared_utils import SharedUtilsProtocol


class FactsStageThree(FactsGenerator):
    """
    `FactsStageTwo` is based on `FactsGenerator`, so make sure to read the description there first.

    All methods is adding itself to *other* device's facts, so this class has an extra argument of peer_facts, which is a dictionary
    with facts set during Stage One and Two for all other devices.
    """

    peer_facts: dict[str, EosDesignsFacts]

    @facts_contributor
    def update_downlink_switches_on_peers(self) -> None:
        for uplink_switch in self.facts.uplink_peers:
            if uplink_switch not in self.peer_facts:
                raise Exception("TODO make a good error message")
            self.peer_facts[uplink_switch].downlink_switches.append_unique(self.shared_utils.hostname)

    @facts_contributor
    def update_evpn_route_server_clients_on_peers(self) -> None:
        for evpn_route_server in self.facts.evpn_route_servers:
            if evpn_route_server not in self.peer_facts:
                raise Exception("TODO make a good error message")
            self.peer_facts[evpn_route_server].evpn_route_server_clients.append_unique(self.shared_utils.hostname)

    @facts_contributor
    def update_mpls_route_reflector_clients_on_peers(self) -> None:
        for mpls_route_reflector in self.facts.mpls_route_reflectors:
            if mpls_route_reflector not in self.peer_facts:
                raise Exception("TODO make a good error message")
            self.peer_facts[mpls_route_reflector].mpls_route_reflector_clients.append_unique(self.shared_utils.hostname)

    def __init__(
        self, hostvars: Mapping, inputs: EosDesigns, facts: EosDesignsFacts, shared_utils: SharedUtilsProtocol, peer_facts: dict[str, EosDesignsFacts]
    ) -> None:
        self.peer_facts = peer_facts
        super().__init__(hostvars, inputs, facts, shared_utils)
