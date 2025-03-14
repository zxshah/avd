# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from functools import cached_property
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

    @cached_property
    def _vlans(self: FactsStageTwoProtocol) -> set[int]:
        """
        Decompressed list of vlans to be defined on this switch after filtering network services.

        The filter is based on filter.tenants, filter.tags and filter.only_vlans_in_use.
        """
        return set(map(int, range_expand(self.facts.vlans)))

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

    @cached_property
    def _mlag_peer_endpoint_vlans_and_trunk_groups(self: FactsStageTwoProtocol) -> tuple[set[int], set[str]]:
        """
        Return set of vlans and set of trunk groups used by connected_endpoints on the MLAG peer and it's downstream switches.

        This could differ from local vlans and trunk groups if a connected endpoint or a downstream switch is only connected to one leaf.
        """
        if not self.shared_utils.mlag:
            return set(), set()

        return self.get_endpoint_vlans_and_trunk_groups_for_one_peer(self.shared_utils.mlag_peer, only_port_channel_uplink=False)

    @cached_property
    def _endpoint_vlans_and_trunk_groups(self: FactsStageTwoProtocol) -> tuple[set[int], set[str]]:
        """
        Return set of vlans and set of trunk groups.

        The trunk groups are those used by connected_endpoints on this switch,
        downstream switches but NOT mlag peer (since we would have circular references then).
        """
        if not self.shared_utils.any_network_services:
            return set(), set()

        return self.get_endpoint_vlans_and_trunk_groups_for_one_peer(self.shared_utils.hostname, only_port_channel_uplink=False)

    @cached_property
    def _endpoint_vlans(self: FactsStageTwoProtocol) -> set[int]:
        """
        Return set of vlans in use by endpoints connected to this switch, downstream switches or MLAG peer.

        Ex: {1, 20, 21, 22, 23} or set().
        """
        if not self.shared_utils.node_config.filter.only_vlans_in_use:
            return set()

        endpoint_vlans, _ = self._endpoint_vlans_and_trunk_groups
        if not self.shared_utils.mlag:
            return endpoint_vlans

        mlag_peer_endpoint_vlans, _mlag_peer_endpoint_trunk_groups = self._mlag_peer_endpoint_vlans_and_trunk_groups

        return endpoint_vlans.union(mlag_peer_endpoint_vlans)

    @facts_contributor
    def endpoint_vlans(self: FactsStageTwoProtocol) -> None:
        """
        Return compressed list of vlans in use by endpoints connected to this switch, downstream switches or MLAG peer.

        Ex: "1,20-30" or "".
        """
        if self.shared_utils.node_config.filter.only_vlans_in_use:
            self.facts.endpoint_vlans = list_compress(list(self._endpoint_vlans))

    @cached_property
    def _endpoint_trunk_groups(self: FactsStageTwoProtocol) -> set[str]:
        """Return set of trunk_groups in use by endpoints connected to this switch, downstream switches or MLAG peer."""
        if not self.shared_utils.node_config.filter.only_vlans_in_use:
            return set()

        _, endpoint_trunk_groups = self._endpoint_vlans_and_trunk_groups
        if not self.shared_utils.mlag:
            return endpoint_trunk_groups

        _mlag_peer_endpoint_vlans, mlag_peer_endpoint_trunk_groups = self._mlag_peer_endpoint_vlans_and_trunk_groups

        return endpoint_trunk_groups.union(mlag_peer_endpoint_trunk_groups)

    @facts_contributor
    def endpoint_trunk_groups(self: FactsStageTwoProtocol) -> None:
        """
        Return list of trunk_groups in use by endpoints connected to this switch, downstream switches or MLAG peer.

        Used for filtering which vlans we configure on the device. This is a superset of local_endpoint_trunk_groups.
        """
        self.facts.endpoint_trunk_groups.extend(natural_sort(self._endpoint_trunk_groups))
