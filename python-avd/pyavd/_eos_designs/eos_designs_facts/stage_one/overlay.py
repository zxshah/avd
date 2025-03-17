# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from pyavd._eos_designs.eos_designs_facts.facts_generator import facts_contributor

if TYPE_CHECKING:
    from . import FactsStageOneProtocol


class OverlayMixin(Protocol):
    """
    Mixin Class used to generate some of the EosDesignsFacts.

    Class should only be used as Mixin to the EosDesignsFacts class.
    Using type-hint on self to get proper type-hints on attributes across all Mixins.
    """

    @facts_contributor
    def evpn_role(self: FactsStageOneProtocol) -> None:
        """Exposed in avd_switch_facts."""
        self.facts.evpn_role = self.shared_utils.evpn_role

    @facts_contributor
    def mpls_overlay_role(self: FactsStageOneProtocol) -> None:
        """Exposed in avd_switch_facts."""
        self.facts.mpls_overlay_role = self.shared_utils.mpls_overlay_role

    @facts_contributor
    def evpn_route_servers(self: FactsStageOneProtocol) -> None:
        """
        Exposed in avd_switch_facts.

        For evpn clients the default value for EVPN Route Servers is the content of the uplink_switches variable set elsewhere.
        For all other evpn roles there is no default.
        """
        if self.shared_utils.underlay_router is True:
            if self.shared_utils.evpn_role == "client":
                self.facts.evpn_route_servers.extend(self.shared_utils.node_config.evpn_route_servers or self.shared_utils.uplink_switches)
            else:
                self.facts.evpn_route_servers.extend(self.shared_utils.node_config.evpn_route_servers)

    @facts_contributor
    def mpls_route_reflectors(self: FactsStageOneProtocol) -> None:
        """Exposed in avd_switch_facts."""
        if self.shared_utils.underlay_router is True and (
            self.shared_utils.mpls_overlay_role in ["client", "server"]
            or (self.shared_utils.evpn_role in ["client", "server"] and self.shared_utils.overlay_evpn_mpls)
        ):
            self.facts.mpls_route_reflectors.extend(self.shared_utils.node_config.mpls_route_reflectors)

    @facts_contributor
    def overlay_rd_type_admin_subfield(self: FactsStageOneProtocol) -> None:
        """Exposed in avd_switch_facts."""
        if "evpn" not in self.shared_utils.overlay_address_families:
            return
        if self.inputs.evpn_multicast and self.shared_utils.vtep:
            self.facts.only_used_for_peer_facts.overlay_rd_type_admin_subfield = self.shared_utils.overlay_rd_type_admin_subfield
