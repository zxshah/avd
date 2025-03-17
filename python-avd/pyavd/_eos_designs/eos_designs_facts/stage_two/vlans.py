# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from pyavd._eos_designs.eos_designs_facts.facts_generator import facts_contributor
from pyavd.j2filters import list_compress, natural_sort, range_expand

if TYPE_CHECKING:
    from . import FactsStageTwoProtocol


class VlansMixin(Protocol):
    """
    Mixin Class used to generate some of the EosDesignsFacts.

    Class should only be used as Mixin to the EosDesignsFacts class.
    Using type-hint on self to get proper type-hints on attributes across all Mixins.
    """

    def get_endpoint_vlans_and_trunk_groups_for_one_peer(
        self: FactsStageTwoProtocol, peer_name: str, only_port_channel_uplink: bool = True
    ) -> tuple[set[int], set[str]]:
        """
        Helper to recursively retrieve 'local_endpoint_vlans' and 'local_endpoint_trunk_groups' facts from a peer and it's downstream peers.

        Args:
            peer_name: Hostname of device to get from.
            only_port_channel_uplink: Check if uplink type is port-channel *for the first device*. All nested devices are always checked.
        """
        peer_facts = self.shared_utils.get_peer_facts(peer_name)
        if only_port_channel_uplink and peer_facts.only_used_for_peer_facts.uplink_type != "port-channel":
            return set(), set()

        vlans = set(map(int, range_expand(peer_facts.local_endpoint_vlans or "")))
        trunk_groups = set(peer_facts.local_endpoint_trunk_groups)
        for downstream_peer in peer_facts.downlink_switches:
            downstream_vlans, downstream_trunk_groups = self.get_endpoint_vlans_and_trunk_groups_for_one_peer(downstream_peer)
            vlans.update(downstream_vlans)
            trunk_groups.update(downstream_trunk_groups)
        return vlans, trunk_groups

    @facts_contributor
    def endpoint_vlans_trunk_groups(self: FactsStageTwoProtocol) -> None:
        """
        Set facts for vlans and trunk_groups in use by endpoints connected to this switch, downstream switches or MLAG peer.

        Used for filtering which vlans we configure on the device. This is a superset of local_endpoint_trunk_groups.
        """
        if not self.shared_utils.any_network_services or not self.shared_utils.node_config.filter.only_vlans_in_use:
            return

        endpoint_vlans, endpoint_trunk_groups = self.get_endpoint_vlans_and_trunk_groups_for_one_peer(
            self.shared_utils.hostname, only_port_channel_uplink=False
        )
        if self.shared_utils.mlag:
            mlag_peer_endpoint_vlans, mlag_peer_endpoint_trunk_groups = self.get_endpoint_vlans_and_trunk_groups_for_one_peer(
                self.shared_utils.mlag_peer, only_port_channel_uplink=False
            )
            # Using union instead of update to avoid changing the cached property
            endpoint_vlans = endpoint_vlans.union(mlag_peer_endpoint_vlans)
            endpoint_trunk_groups = endpoint_trunk_groups.union(mlag_peer_endpoint_trunk_groups)

        self.facts.endpoint_vlans = list_compress(list(endpoint_vlans))
        self.facts.endpoint_trunk_groups.extend(natural_sort(endpoint_trunk_groups))
