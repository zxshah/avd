# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Protocol

from pyavd._eos_designs.eos_designs_facts.facts_generator import facts_contributor
from pyavd._eos_designs.eos_designs_facts.schema import EosDesignsFacts
from pyavd._errors import AristaAvdError
from pyavd.j2filters import list_compress, natural_sort, range_expand

if TYPE_CHECKING:
    from . import FactsStageTwoProtocol


class UplinksMixin(Protocol):
    """
    Mixin Class used to generate some of the EosDesignsFacts.

    Class should only be used as Mixin to the EosDesignsFacts class.
    Using type-hint on self to get proper type-hints on attributes across all Mixins.
    """

    @cached_property
    def _uplink_port_channel_id(self: FactsStageTwoProtocol) -> int | None:
        """
        For MLAG secondary get the uplink_port_channel_id from the peer's facts.

        We don't need to validate it (1-2000), since it will be validated on the peer.

        For MLAG primary or none MLAG, take the value of 'uplink_port_channel_id' if set,
        or use the numbers from the first interface in 'uplink_interfaces'.

        For MLAG primary validate that the port-channel id falls within 1-2000 since we also use this ID as MLAG ID.
        """
        if self.shared_utils.mlag_role != "secondary":
            # MLAG Primary or not MLAG.
            return self.facts.only_used_for_peer_facts.uplink_port_channel_id

        # MLAG Secondary
        peer_uplink_port_channel_id = self.shared_utils.mlag_peer_facts.only_used_for_peer_facts.uplink_port_channel_id
        # Check that port-channel IDs are the same as on primary when set manually.
        if (uplink_port_channel_id := self.shared_utils.node_config.uplink_port_channel_id) and uplink_port_channel_id != peer_uplink_port_channel_id:
            msg = (
                f"'uplink_port_channel_id' is set to {uplink_port_channel_id} and is not matching {peer_uplink_port_channel_id} set on MLAG peer."
                " The 'uplink_port_channel_id' must be matching on MLAG peers."
            )
            raise AristaAvdError(msg)
        return peer_uplink_port_channel_id

    @cached_property
    def _uplink_switch_port_channel_id(self: FactsStageTwoProtocol) -> int | None:
        """
        For MLAG secondary get the uplink_switch_port_channel_id from the peer's facts.

        We don't need to validate it (1-2000), since it will be validated on the peer.

        For MLAG primary or none MLAG, take the value of 'uplink_switch_port_channel_id' if set,
        or use the numbers from the first interface in 'uplink_switch_interfaces'.

        If the *uplink_switch* is in MLAG,  validate that the port-channel id falls within 1-2000
        since we also use this ID as MLAG ID on the *uplink switch*.
        """
        if self.shared_utils.mlag_role != "secondary":
            # MLAG Primary or not MLAG.
            return self.facts.only_used_for_peer_facts.uplink_switch_port_channel_id

        # MLAG Secondary
        peer_uplink_switch_port_channel_id = self.shared_utils.mlag_peer_facts.only_used_for_peer_facts.uplink_switch_port_channel_id
        # Check that port-channel IDs are the same as on primary when set manually.
        if (
            uplink_switch_port_channel_id := self.shared_utils.node_config.uplink_switch_port_channel_id
        ) is not None and uplink_switch_port_channel_id != peer_uplink_switch_port_channel_id:
            msg = (
                f"'uplink_switch_port_channel_id' is set to {uplink_switch_port_channel_id} and is not matching {peer_uplink_switch_port_channel_id} "
                "set on MLAG peer. The 'uplink_switch_port_channel_id' must be matching on MLAG peers."
            )
            raise AristaAvdError(msg)
        return peer_uplink_switch_port_channel_id

    @facts_contributor
    def uplinks(self: FactsStageTwoProtocol) -> None:
        """
        Exposed in avd_switch_facts.

        List of uplinks with all parameters

        These facts are leveraged by templates for this device when rendering uplinks
        and by templates for peer devices when rendering downlinks
        """
        if self.shared_utils.uplink_type == "p2p":
            get_uplink = self._get_p2p_uplink
        elif self.shared_utils.uplink_type == "port-channel":
            get_uplink = self._get_port_channel_uplink
        elif self.shared_utils.uplink_type == "p2p-vrfs":
            if self.shared_utils.network_services_l3 is False or self.shared_utils.underlay_router is False:
                msg = "'underlay_router' and 'network_services.l3' must be 'true' for the node_type_key when using 'p2p-vrfs' as 'uplink_type'."
                raise AristaAvdError(msg)
            get_uplink = self._get_p2p_vrfs_uplink
        elif self.shared_utils.uplink_type == "lan":
            if self.shared_utils.network_services_l3 is False or self.shared_utils.underlay_router is False:
                msg = "'underlay_router' and 'network_services.l3' must be 'true' for the node_type_key when using 'lan' as 'uplink_type'."
                raise AristaAvdError(msg)
            if len(self.shared_utils.uplink_interfaces) > 1:
                msg = f"'uplink_type: lan' only supports a single uplink interface. Got {self.shared_utils.uplink_interfaces}."
                raise AristaAvdError(msg)
                # TODO: Adjust error message when we add lan-port-channel support.
                # uplink_type: lan' only supports a single uplink interface.
                # Got {self._uplink_interfaces}. Consider 'uplink_type: lan-port-channel' if applicable.
            get_uplink = self._get_l2_uplink
        else:
            msg = f"Invalid uplink_type '{self.shared_utils.uplink_type}'."
            raise AristaAvdError(msg)

        uplink_switches = self.shared_utils.uplink_switches
        uplink_switch_interfaces = self.shared_utils.uplink_switch_interfaces
        for uplink_index, uplink_interface in enumerate(self.shared_utils.uplink_interfaces):
            if len(uplink_switches) <= uplink_index or len(uplink_switch_interfaces) <= uplink_index:
                # Invalid length of input variables. Skipping
                continue

            uplink_switch = uplink_switches[uplink_index]
            uplink_switch_interface = uplink_switch_interfaces[uplink_index]
            if uplink_switch is None or uplink_switch not in self.shared_utils.all_fabric_devices:
                # Invalid uplink_switch. Skipping.
                continue

            self.facts.uplinks.append(get_uplink(uplink_index, uplink_interface, uplink_switch, uplink_switch_interface))

    def _get_p2p_uplink(
        self: FactsStageTwoProtocol, uplink_index: int, uplink_interface: str, uplink_switch: str, uplink_switch_interface: str
    ) -> EosDesignsFacts.UplinksItem:
        """Return facts for a single uplink for uplink_type p2p."""
        uplink_switch_facts = self.shared_utils.get_peer_facts(uplink_switch)
        uplink = EosDesignsFacts.UplinksItem(
            interface=uplink_interface,
            peer=uplink_switch,
            peer_interface=uplink_switch_interface,
            peer_type=uplink_switch_facts.type,
            peer_is_deployed=uplink_switch_facts.is_deployed,
            peer_bgp_as=uplink_switch_facts.bgp_as,
            type="underlay_p2p",
            speed=self.shared_utils.uplink_interface_speed,
            bfd=self.shared_utils.node_config.uplink_bfd or None,
            peer_speed=self.shared_utils.uplink_switch_interface_speed,
            underlay_multicast=(self.shared_utils.underlay_multicast and uplink_switch_facts.only_used_for_peer_facts.underlay_multicast is True),
            structured_config=self.shared_utils.node_config.uplink_structured_config,
        )

        if self.shared_utils.node_config.uplink_ptp:
            uplink.ptp.enable = self.shared_utils.node_config.uplink_ptp.enable
        elif self.shared_utils.ptp_enabled and (not (ptp_uplinks := self.shared_utils.node_config.ptp.uplinks) or (uplink_interface in ptp_uplinks)):
            uplink.ptp.enable = True

        if self.shared_utils.node_config.uplink_macsec.profile:
            uplink.mac_security.profile = self.shared_utils.node_config.uplink_macsec.profile

        if self.inputs.underlay_rfc5549:
            uplink.ipv6_enable = True
        else:
            uplink.prefix_length = self.inputs.fabric_ip_addressing.p2p_uplinks.ipv4_prefix_length
            uplink.ip_address = self.shared_utils.ip_addressing.p2p_uplinks_ip(uplink_index)
            uplink.peer_ip_address = self.shared_utils.ip_addressing.p2p_uplinks_peer_ip(uplink_index)

        if self.shared_utils.link_tracking_groups is not None:
            for lt_group in self.shared_utils.link_tracking_groups:
                uplink.link_tracking_groups.append_new(name=lt_group["name"], direction="upstream")

        return uplink

    def _get_port_channel_uplink(
        self: FactsStageTwoProtocol, uplink_index: int, uplink_interface: str, uplink_switch: str, uplink_switch_interface: str
    ) -> EosDesignsFacts.UplinksItem:
        """Return facts for a single uplink for uplink_type port-channel."""
        uplink_switch_facts = self.shared_utils.get_peer_facts(uplink_switch)

        # Reusing get_l2_uplink
        uplink = self._get_l2_uplink(uplink_index, uplink_interface, uplink_switch, uplink_switch_interface)

        if uplink_switch_facts.only_used_for_peer_facts.mlag is True or self._short_esi is not None:
            # Override our description on port-channel to be peer's group name if they are mlag pair or A/A #}
            uplink.peer_node_group = uplink_switch_facts.group

        # Used to determine whether or not port-channel should have an mlag id configure on the uplink_switch
        unique_uplink_switches = set(self.shared_utils.uplink_switches)
        if self.shared_utils.mlag is True:
            # Override the peer's description on port-channel to be our group name if we are mlag pair #}
            uplink.node_group = self.shared_utils.group

            # Updating unique_uplink_switches with our mlag peer's uplink switches
            unique_uplink_switches.update(self.shared_utils.mlag_peer_facts.uplink_peers)

        # Only enable mlag for this port-channel on the uplink switch if there are multiple unique uplink switches
        uplink.peer_mlag = len(unique_uplink_switches) > 1

        uplink.channel_group_id = self._uplink_port_channel_id
        uplink.peer_channel_group_id = self._uplink_switch_port_channel_id

        return uplink

    def _get_l2_uplink(
        self: FactsStageTwoProtocol,
        uplink_index: int,  # pylint: disable=unused-argument # noqa: ARG002
        uplink_interface: str,
        uplink_switch: str,
        uplink_switch_interface: str,
    ) -> EosDesignsFacts.UplinksItem:
        """Return facts for a single uplink for an L2 uplink. Reused for both uplink_type port-channel, lan and TODO: lan-port-channel."""
        uplink_switch_facts = self.shared_utils.get_peer_facts(uplink_switch)
        uplink = EosDesignsFacts.UplinksItem(
            interface=uplink_interface,
            peer=uplink_switch,
            peer_interface=uplink_switch_interface,
            peer_type=uplink_switch_facts.type,
            peer_is_deployed=uplink_switch_facts.is_deployed,
            type="underlay_l2",
            speed=self.shared_utils.uplink_interface_speed,
            peer_speed=self.shared_utils.uplink_switch_interface_speed,
            native_vlan=self.shared_utils.node_config.uplink_native_vlan,
            peer_short_esi=self._short_esi,
            structured_config=self.shared_utils.node_config.uplink_structured_config,
        )

        if self.shared_utils.node_config.uplink_ptp:
            uplink.ptp.enable = self.shared_utils.node_config.uplink_ptp.enable
        elif self.shared_utils.ptp_enabled:
            uplink.ptp.enable = True

        # Remove vlans if upstream switch does not have them #}
        if self.inputs.enable_trunk_groups:
            uplink.trunk_groups.append_unique("UPLINK")
            if self.shared_utils.mlag and self.shared_utils.group:
                uplink.peer_trunk_groups.append_unique(self.shared_utils.group)
            else:
                uplink.peer_trunk_groups.append_unique(self.shared_utils.hostname)

        uplink_vlans = set(self._vlans).intersection(set(map(int, range_expand(uplink_switch_facts.vlans))))

        if self.shared_utils.configure_inband_mgmt or self.shared_utils.configure_inband_mgmt_ipv6:
            # Always add inband_mgmt_vlan even if the uplink switch does not have this vlan defined
            uplink_vlans.add(self.shared_utils.node_config.inband_mgmt_vlan)

        uplink.vlans = list_compress(list(uplink_vlans)) if uplink_vlans else "none"

        if self.shared_utils.link_tracking_groups is not None:
            for lt_group in self.shared_utils.link_tracking_groups:
                uplink.link_tracking_groups.append_new(name=lt_group["name"], direction="upstream")

        if not self.shared_utils.network_services_l2:
            # This child device does not support VLANs, so we tell the peer to enable portfast
            uplink.peer_spanning_tree_portfast = "edge"

        return uplink

    def _get_p2p_vrfs_uplink(
        self: FactsStageTwoProtocol, uplink_index: int, uplink_interface: str, uplink_switch: str, uplink_switch_interface: str
    ) -> EosDesignsFacts.UplinksItem:
        """Return facts for a single uplink for uplink_type p2p-vrfs."""
        uplink_switch_facts = self.shared_utils.get_peer_facts(uplink_switch)

        # Reusing regular p2p logic for main interface.
        uplink = self._get_p2p_uplink(uplink_index, uplink_interface, uplink_switch, uplink_switch_interface)
        for tenant in self.shared_utils.filtered_tenants:
            for vrf in tenant.vrfs:
                # Only keep VRFs present on the uplink switch as well.
                # Also skip VRF default since it is covered on the parent interface.
                # ok to use like this because this is only ever called inside EosDesignsFacts
                uplink_switch_vrfs = uplink_switch_facts.only_used_for_peer_facts.vrfs
                if vrf.name == "default" or vrf.name not in uplink_switch_vrfs:
                    continue

                vrf_id: int = self.shared_utils.get_vrf_id(vrf)
                subinterface = EosDesignsFacts.UplinksItem.SubinterfacesItem(
                    interface=f"{uplink_interface}.{vrf_id}",
                    peer_interface=f"{uplink_switch_interface}.{vrf_id}",
                    vrf=vrf.name,
                    encapsulation_dot1q_vlan=vrf_id,
                    structured_config=self.shared_utils.node_config.uplink_structured_config,
                )

                if self.inputs.underlay_rfc5549:
                    subinterface.ipv6_enable = True
                else:
                    subinterface._update(
                        prefix_length=self.inputs.fabric_ip_addressing.p2p_uplinks.ipv4_prefix_length,
                        ip_address=self.shared_utils.ip_addressing.p2p_vrfs_uplinks_ip(uplink_index, vrf.name),
                        peer_ip_address=self.shared_utils.ip_addressing.p2p_vrfs_uplinks_peer_ip(uplink_index, vrf.name),
                    )

                uplink.subinterfaces.append(subinterface)

        return uplink

    @facts_contributor
    def uplink_switch_vrfs(self: FactsStageTwoProtocol) -> None:
        """
        Exposed in avd_switch_facts.

        Return the list of VRF names present on uplink switches.
        """
        if self.shared_utils.uplink_type != "p2p-vrfs":
            return

        vrfs = set()
        for uplink_switch in self.facts.uplink_peers:
            uplink_switch_facts = self.shared_utils.get_peer_facts(uplink_switch)
            vrfs.update(uplink_switch_facts.only_used_for_peer_facts.vrfs)

        self.facts.uplink_switch_vrfs.extend(natural_sort(vrfs))
