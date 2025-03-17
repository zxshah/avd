# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

import re
from functools import cached_property
from typing import TYPE_CHECKING, Protocol

from pyavd._eos_designs.eos_designs_facts.facts_generator import facts_contributor
from pyavd.j2filters import list_compress, natural_sort, range_expand

if TYPE_CHECKING:
    from pyavd._eos_designs.schema import EosDesigns

    from . import FactsStageOneProtocol


class VlansMixin(Protocol):
    """
    Mixin Class used to generate some of the EosDesignsFacts.

    Class should only be used as Mixin to the EosDesignsFacts class.
    Using type-hint on self to get proper type-hints on attributes across all Mixins.
    """

    @facts_contributor
    def vlans(self: FactsStageOneProtocol) -> None:
        """
        Return the compressed list of vlans allowed on this switch after filtering network services.

        The filter is based on filter.tenants, filter.tags and filter.only_vlans_in_use.

        Ex. "1-100, 201-202"
        """
        if not self.shared_utils.any_network_services:
            return

        vlans = []
        for network_services_key in self.inputs._dynamic_keys.network_services:
            tenants = network_services_key.value
            for tenant in tenants:
                if not set(self.shared_utils.node_config.filter.tenants).intersection([tenant.name, "all"]):
                    # Not matching tenant filters. Skipping this tenant.
                    continue

                vlans.extend(svi.id for vrf in tenant.vrfs for svi in vrf.svis if self._is_accepted_vlan(svi))
                vlans.extend(l2vlan.id for l2vlan in tenant.l2vlans if self._is_accepted_vlan(l2vlan))

        self.facts.vlans = list_compress(vlans)

    def _is_accepted_vlan(
        self: FactsStageOneProtocol,
        vlan: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.SvisItem
        | EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.L2vlansItem,
    ) -> bool:
        return "all" in self.shared_utils.filter_tags or bool(set(vlan.tags).intersection(self.shared_utils.filter_tags))

    @facts_contributor
    def local_endpoint_vlans(self: FactsStageOneProtocol) -> None:
        if self.shared_utils.node_config.filter.only_vlans_in_use:
            self.facts.local_endpoint_vlans = list_compress(list(self._local_endpoint_vlans))

    @facts_contributor
    def local_endpoint_trunk_groups(self: FactsStageOneProtocol) -> None:
        if self.shared_utils.node_config.filter.only_vlans_in_use:
            self.facts.local_endpoint_trunk_groups.extend(natural_sort(self._local_endpoint_trunk_groups))

    @cached_property
    def _local_endpoint_vlans(self: FactsStageOneProtocol) -> set[int]:
        vlans, _trunk_groups = self._local_endpoint_vlans_and_trunk_groups
        return vlans

    @cached_property
    def _local_endpoint_trunk_groups(self: FactsStageOneProtocol) -> set[str]:
        _vlans, trunk_groups = self._local_endpoint_vlans_and_trunk_groups
        return trunk_groups

    @cached_property
    def _local_endpoint_vlans_and_trunk_groups(self: FactsStageOneProtocol) -> tuple[set[int], set[str]]:
        """
        Return list of vlans and list of trunk groups used by connected_endpoints on this switch.

        Also includes the inband_mgmt_vlan.
        """
        if not (self.shared_utils.any_network_services and self.shared_utils.connected_endpoints):
            return set(), set()

        vlans: set[int] = set()
        trunk_groups: set[str] = set()

        if self.shared_utils.configure_inband_mgmt:
            vlans.add(self.shared_utils.node_config.inband_mgmt_vlan)

        for connected_endpoints_key in self.inputs._dynamic_keys.connected_endpoints:
            for connected_endpoint in connected_endpoints_key.value:
                for index, adapter in enumerate(connected_endpoint.adapters):
                    adapter._internal_data.context = f"{connected_endpoints_key.key}[name={connected_endpoint.name}].adapters[{index}]"
                    adapter_settings = self.shared_utils.get_merged_adapter_settings(adapter)
                    if self.shared_utils.hostname not in adapter_settings.switches:
                        # This switch is not connected to this endpoint. Skipping.
                        continue

                    adapter_vlans, adapter_trunk_groups = self._parse_adapter_settings(adapter_settings)
                    vlans.update(adapter_vlans)
                    trunk_groups.update(adapter_trunk_groups)
                    if len(vlans) >= 4094:
                        # No need to check further, since the set is now containing all vlans.
                        # The trunk group list may not be complete, but it will not matter, since we will
                        # configure all vlans anyway.
                        return vlans, trunk_groups

        for index, network_port_item in enumerate(self.inputs.network_ports):
            for switch_regex in network_port_item.switches:
                # The match test is built on Python re.match which tests from the beginning of the string #}
                # Since the user would not expect "DC1-LEAF1" to also match "DC-LEAF11" we will force ^ and $ around the regex
                raw_switch_regex = rf"^{switch_regex}$"
                if not re.match(raw_switch_regex, self.shared_utils.hostname):
                    # Skip entry if no match
                    continue

                network_port_item._internal_data.context = f"network_ports[{index}]"
                adapter_settings = self.shared_utils.get_merged_adapter_settings(network_port_item)
                adapter_vlans, adapter_trunk_groups = self._parse_adapter_settings(adapter_settings)
                vlans.update(adapter_vlans)
                trunk_groups.update(adapter_trunk_groups)
                if len(vlans) >= 4094:
                    # No need to check further, since the list is now containing all vlans.
                    # The trunk group list may not be complete, but it will not matter, since we will
                    # configure all vlans anyway.
                    return vlans, trunk_groups

        return vlans, trunk_groups

    def _parse_adapter_settings(
        self: FactsStageOneProtocol,
        adapter_settings: EosDesigns._DynamicKeys.DynamicConnectedEndpointsItem.ConnectedEndpointsItem.AdaptersItem | EosDesigns.NetworkPortsItem,
    ) -> tuple[set[int], set[str]]:
        """Parse the given adapter_settings and return relevant vlans and trunk_groups."""
        vlans: set[int] = set()
        trunk_groups: set[str] = set(adapter_settings.trunk_groups)
        if adapter_settings.vlans and adapter_settings.vlans != "all":
            vlans.update(map(int, range_expand(adapter_settings.vlans)))
        elif adapter_settings.mode == "trunk" and not trunk_groups:
            # No vlans or trunk_groups defined, but this is a trunk, so default is all vlans allowed
            # No need to check further, since the list is now containing all vlans.
            return set(range(1, 4094)), trunk_groups
        elif adapter_settings.mode == "trunk phone":
            # # EOS default native VLAN is VLAN 1
            if not adapter_settings.native_vlan:
                vlans.add(1)
        else:
            # No vlans or mode defined so this is an access port with only vlan 1 allowed
            vlans.add(1)

        if adapter_settings.native_vlan:
            vlans.add(adapter_settings.native_vlan)
        if adapter_settings.phone_vlan:
            vlans.add(adapter_settings.phone_vlan)

        for subinterface in adapter_settings.port_channel.subinterfaces:
            if subinterface.vlan_id:
                vlans.add(subinterface.vlan_id)
            elif subinterface.number:
                vlans.add(subinterface.number)

        return vlans, trunk_groups
