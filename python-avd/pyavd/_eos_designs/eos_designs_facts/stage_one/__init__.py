# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from typing import Protocol

from pyavd._eos_designs.eos_designs_facts.facts_generator import FactsGenerator, FactsGeneratorProtocol, facts_contributor
from pyavd._eos_designs.eos_designs_facts.schema import EosDesignsFacts

from .mlag import MlagMixin
from .overlay import OverlayMixin
from .uplinks import UplinksMixin
from .vlans import VlansMixin
from .wan import WanMixin


class FactsStageOneProtocol(MlagMixin, OverlayMixin, UplinksMixin, VlansMixin, WanMixin, FactsGeneratorProtocol, Protocol):
    @facts_contributor
    def id(self) -> None:
        """Exposed in avd_switch_facts."""
        self.facts.id = self.shared_utils.id

    @facts_contributor
    def type(self) -> None:
        """
        Exposed in avd_switch_facts.

        switch.type fact set based on type variable
        """
        self.facts.type = self.shared_utils.type

    @facts_contributor
    def platform(self) -> None:
        """Exposed in avd_switch_facts."""
        self.facts.platform = self.shared_utils.platform

    @facts_contributor
    def is_deployed(self) -> None:
        """Exposed in avd_switch_facts."""
        self.facts.is_deployed = self.inputs.is_deployed

    @facts_contributor
    def serial_number(self) -> None:
        """Exposed in avd_switch_facts."""
        self.facts.serial_number = self.shared_utils.serial_number

    @facts_contributor
    def mgmt_interface(self) -> None:
        """Exposed in avd_switch_facts."""
        self.facts.mgmt_interface = self.shared_utils.mgmt_interface

    @facts_contributor
    def mgmt_ip(self) -> None:
        """Exposed in avd_switch_facts."""
        self.facts.mgmt_ip = self.shared_utils.node_config.mgmt_ip

    @facts_contributor
    def mpls_lsr(self) -> None:
        """Exposed in avd_switch_facts."""
        self.facts.mpls_lsr = self.shared_utils.mpls_lsr

    @facts_contributor
    def loopback_ipv4_pool(self) -> None:
        """Exposed in avd_switch_facts."""
        if self.shared_utils.underlay_router:
            self.facts.loopback_ipv4_pool = self.shared_utils.loopback_ipv4_pool

    @facts_contributor
    def uplink_ipv4_pool(self) -> None:
        """Exposed in avd_switch_facts."""
        if self.shared_utils.underlay_router:
            self.facts.uplink_ipv4_pool = self.shared_utils.node_config.uplink_ipv4_pool

    @facts_contributor
    def downlink_pools(self) -> None:
        """Exposed in avd_switch_facts."""
        if self.shared_utils.underlay_router:
            for downlink_pool in self.shared_utils.node_config.downlink_pools:
                self.facts.downlink_pools.append(downlink_pool._cast_as(EosDesignsFacts.DownlinkPoolsItem))

    @facts_contributor
    def underlay_routing_protocol(self) -> None:
        """Exposed in avd_switch_facts."""
        self.facts.underlay_routing_protocol = self.shared_utils.underlay_routing_protocol

    @facts_contributor
    def vtep_loopback_ipv4_pool(self) -> None:
        """Exposed in avd_switch_facts."""
        if self.shared_utils.vtep is True:
            self.facts.vtep_loopback_ipv4_pool = self.shared_utils.vtep_loopback_ipv4_pool

    @facts_contributor
    def inband_mgmt_subnet(self) -> None:
        """Exposed in avd_switch_facts."""
        if self.shared_utils.configure_parent_for_inband_mgmt:
            self.facts.inband_mgmt_subnet = self.shared_utils.node_config.inband_mgmt_subnet

    @facts_contributor
    def inband_mgmt_ipv6_subnet(self) -> None:
        """Exposed in avd_switch_facts."""
        if self.shared_utils.configure_parent_for_inband_mgmt_ipv6:
            self.facts.inband_mgmt_ipv6_subnet = self.shared_utils.node_config.inband_mgmt_ipv6_subnet

    @facts_contributor
    def inband_mgmt_vlan(self) -> None:
        """Exposed in avd_switch_facts."""
        if self.shared_utils.configure_parent_for_inband_mgmt or self.shared_utils.configure_parent_for_inband_mgmt_ipv6:
            self.facts.inband_mgmt_vlan = self.shared_utils.node_config.inband_mgmt_vlan

    @facts_contributor
    def inband_ztp(self) -> None:
        """Exposed in avd_switch_facts."""
        self.facts.inband_ztp = self.shared_utils.node_config.inband_ztp

    @facts_contributor
    def inband_ztp_vlan(self) -> None:
        """Exposed in avd_switch_facts."""
        if self.shared_utils.node_config.inband_ztp:
            self.facts.inband_ztp_vlan = self.shared_utils.node_config.inband_mgmt_vlan

    @facts_contributor
    def inband_ztp_lacp_fallback_delay(self) -> None:
        """Exposed in avd_switch_facts."""
        if self.shared_utils.node_config.inband_ztp:
            self.facts.inband_ztp_lacp_fallback_delay = self.shared_utils.node_config.inband_ztp_lacp_fallback_delay

    @facts_contributor
    def dc_name(self) -> None:
        """Exposed in avd_switch_facts."""
        self.facts.dc_name = self.inputs.dc_name

    @facts_contributor
    def group(self) -> None:
        """Exposed in avd_switch_facts."""
        self.facts.group = self.shared_utils.group

    @facts_contributor
    def router_id(self) -> None:
        """Exposed in avd_switch_facts."""
        self.facts.router_id = self.shared_utils.router_id

    @facts_contributor
    def inband_mgmt_ip(self) -> None:
        """
        Exposed in avd_switch_facts.

        Used for fabric docs
        """
        self.facts.inband_mgmt_ip = self.shared_utils.inband_mgmt_ip

    @facts_contributor
    def inband_mgmt_interface(self) -> None:
        """
        Exposed in avd_switch_facts.

        Used for fabric docs
        """
        self.facts.inband_mgmt_interface = self.shared_utils.inband_mgmt_interface

    @facts_contributor
    def pod(self) -> None:
        """
        Exposed in avd_switch_facts.

        Used for fabric docs
        """
        self.facts.pod = self.inputs.pod_name or self.inputs.dc_name or self.shared_utils.fabric_name

    @facts_contributor
    def connected_endpoints_keys(self) -> None:
        """
        List of connected_endpoints_keys in use on this device.

        Exposed in avd_switch_facts.

        Used for fabric docs
        """
        self.facts.connected_endpoints_keys = EosDesignsFacts.ConnectedEndpointsKeys(
            [
                entry._cast_as(EosDesignsFacts.ConnectedEndpointsKeysItem)
                for entry in self.inputs.connected_endpoints_keys
                if entry.key in self.inputs._dynamic_keys.connected_endpoints
            ]
        )

    @facts_contributor
    def port_profile_names(self) -> None:
        """
        Exposed in avd_switch_facts.

        Used for fabric docs
        """
        for profile in self.inputs.port_profiles:
            self.facts.port_profile_names.append_new(profile=profile.profile, parent_profile=profile.parent_profile)

    @facts_contributor
    def vrfs(self) -> None:
        self.facts.only_used_for_peer_facts.vrfs.extend(self.shared_utils.vrfs)

    @facts_contributor
    def underlay_multicast(self) -> None:
        self.facts.only_used_for_peer_facts.underlay_multicast = self.shared_utils.underlay_multicast


class FactsStageOne(FactsGenerator, FactsStageOneProtocol):
    """
    `FactsStageOne` is based on `FactsGeneratorProtocol`, so make sure to read the description there first.

    All methods should only rely on the device's own inputs.
    """
