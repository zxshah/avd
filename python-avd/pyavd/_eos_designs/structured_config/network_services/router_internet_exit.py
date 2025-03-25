# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from pyavd._eos_cli_config_gen.schema import EosCliConfigGen
from pyavd._eos_designs.schema import EosDesigns
from pyavd._errors import AristaAvdError, AristaAvdInvalidInputsError
from pyavd.j2filters import range_expand

if TYPE_CHECKING:
    from . import AvdStructuredConfigNetworkServicesProtocol


class RouterInternetExitMixin(Protocol):
    """
    Mixin Class used to generate structured config for one key.

    Class should only be used as Mixin to a AvdStructuredConfig class.
    """

    def _set_internet_exit_policy(
        self: AvdStructuredConfigNetworkServicesProtocol,
        input_topology: EosDesigns.WanVirtualTopologies.ControlPlaneVirtualTopology
        | EosDesigns.WanVirtualTopologies.PoliciesItem.DefaultVirtualTopology
        | EosDesigns.WanVirtualTopologies.PoliciesItem.ApplicationVirtualTopologiesItem,
        policy_name: str,
    ) -> None:
        """
        Set the internet exit policy for a given Virtual Topology if required.

        TODO Make this description nice
        """
        if not self.shared_utils.is_cv_pathfinder_client:
            return

        if not (internet_exit_policy_name := input_topology.internet_exit.policy):
            return

        if internet_exit_policy_name in self.structured_config.router_internet_exit.policies:
            # We have already added this policy
            return

        if internet_exit_policy_name not in self.inputs.cv_pathfinder_internet_exit_policies:
            msg = (
                f"The internet exit policy {internet_exit_policy_name} configured under "
                f"`wan_virtual_topologies.policies[name={policy_name}].internet_exit.policy` "
                "is not defined under `cv_pathfinder_internet_exit_policies`."
            )
            raise AristaAvdInvalidInputsError(msg)

        internet_exit_policy = self.inputs.cv_pathfinder_internet_exit_policies[internet_exit_policy_name]

        # duplicate with some function in utils_wan.
        # TODO: Add support for port_channels
        local_wan_l3_interfaces = EosDesigns._DynamicKeys.DynamicNodeTypesItem.NodeTypes.NodesItem.L3Interfaces(
            [
                wan_interface
                for wan_interface in self.shared_utils.wan_interfaces
                if internet_exit_policy.name in wan_interface.cv_pathfinder_internet_exit.policies
            ]
        )
        if not local_wan_l3_interfaces:
            # No local interface for this policy
            # implies policy present in input yml, but not associated with any interface yet
            # TODO: Decide if we should raise here instead
            return

        # fetch connections associated with given internet exit policy that applies to one or more wan interfaces
        # TODO: set the connections better
        connections = self.get_internet_exit_connections(internet_exit_policy, local_wan_l3_interfaces)
        policy_exit_groups = EosCliConfigGen.RouterInternetExit.PoliciesItem.ExitGroups()
        for connection in connections:
            exit_group = EosCliConfigGen.RouterInternetExit.PoliciesItem.ExitGroupsItem(name=connection["exit_group"])
            self.structured_config.router_internet_exit.exit_groups.obtain(connection["exit_group"]).local_connections.append_new(name=connection["name"])

            # Recording the exit_group in the policy
            policy_exit_groups.append(exit_group)
            # TODO: change the connection dict and see if we can avoid to give policy.
            self.set_internet_exit_tunnel_interface(internet_exit_policy, connection)
            self.set_internet_exit_monitor_connectivity(connection)
            self.set_internet_exit_connection_static_route(connection)
            self.set_internet_exit_router_service_insertion(connection)
            self.set_internet_exit_connection_ethernet_interfaces(internet_exit_policy, connection)

        if internet_exit_policy.fallback_to_system_default:
            policy_exit_groups.append_new(name="system-default-exit-group")

        if internet_exit_policy.type == "zscaler":
            self._set_zscaler_ie_policy_ip_nat()
            self._set_zscaler_ie_policy_acl()
            self._set_zscaler_internet_exit_policy_ip_security(internet_exit_policy)
            # set metadata
            self.set_cv_pathfinder_metadata_zscaler_internet_exit_policy(internet_exit_policy, connections)
        if internet_exit_policy.type == "direct":
            self._set_direct_ie_policy_ip_nat()
            self._set_direct_ie_policy_acl(connections)

        self.structured_config.router_internet_exit.policies.append_new(name=internet_exit_policy.name, exit_groups=policy_exit_groups)

    def get_internet_exit_connections(
        self: AvdStructuredConfigNetworkServicesProtocol,
        internet_exit_policy: EosDesigns.CvPathfinderInternetExitPoliciesItem,
        local_interfaces: EosDesigns._DynamicKeys.DynamicNodeTypesItem.NodeTypes.NodesItem.L3Interfaces,
    ) -> list:
        """
        Return a list of connections (dicts) for the given internet_exit_policy.

        These are useful for easy creation of connectivity-monitor, service-insertion connections, exit-groups, tunnels etc.
        """
        if internet_exit_policy.type == "direct":
            return self.get_direct_internet_exit_connections(internet_exit_policy, local_interfaces)

        if internet_exit_policy.type == "zscaler":
            return self.get_zscaler_internet_exit_connections(internet_exit_policy, local_interfaces)

        msg = f"Unsupported type '{internet_exit_policy.type}' found in cv_pathfinder_internet_exit[name={internet_exit_policy.name}]."
        raise AristaAvdError(msg)

    def get_direct_internet_exit_connections(
        self: AvdStructuredConfigNetworkServicesProtocol,
        internet_exit_policy: EosDesigns.CvPathfinderInternetExitPoliciesItem,
        local_interfaces: EosDesigns._DynamicKeys.DynamicNodeTypesItem.NodeTypes.NodesItem.L3Interfaces,
    ) -> list[dict]:
        """Return a list of connections (dicts) for the given internet_exit_policy of type direct."""
        if internet_exit_policy.type != "direct":
            return []

        connections = []

        # Build internet exit connection for each local interface (wan_interface)
        for wan_interface in local_interfaces:
            if internet_exit_policy.name not in wan_interface.cv_pathfinder_internet_exit.policies:
                continue

            if not wan_interface.peer_ip:
                msg = (
                    f"{wan_interface.name} peer_ip needs to be set. When using wan interface "
                    "for direct type internet exit, peer_ip is used for nexthop, and connectivity monitoring."
                )
                raise AristaAvdInvalidInputsError(msg)

            # wan interface ip will be used for acl, hence raise error if ip is not available
            if (ip_address := wan_interface.ip_address) == "dhcp" and not (ip_address := wan_interface.dhcp_ip):
                msg = (
                    f"{wan_interface.name} 'dhcp_ip' needs to be set. When using WAN interface for 'direct' type Internet exit, "
                    "'dhcp_ip' is used in the NAT ACL."
                )
                raise AristaAvdInvalidInputsError(msg)

            sanitized_interface_name = self.shared_utils.sanitize_interface_name(wan_interface.name)
            connections.append(
                {
                    "type": "ethernet",
                    "name": f"IE-{sanitized_interface_name}",
                    "source_interface_ip_address": ip_address,
                    "monitor_name": f"IE-{sanitized_interface_name}",
                    "monitor_host": wan_interface.peer_ip,
                    "next_hop": wan_interface.peer_ip,
                    "source_interface": wan_interface.name,
                    "description": f"Internet Exit {internet_exit_policy.name}",
                    "exit_group": f"{internet_exit_policy.name}",
                },
            )
        return connections

    def get_zscaler_internet_exit_connections(
        self: AvdStructuredConfigNetworkServicesProtocol,
        internet_exit_policy: EosDesigns.CvPathfinderInternetExitPoliciesItem,
        local_interfaces: EosDesigns._DynamicKeys.DynamicNodeTypesItem.NodeTypes.NodesItem.L3Interfaces,
    ) -> list:
        """Return a list of connections (dicts) for the given internet_exit_policy of type zscaler."""
        if internet_exit_policy.type != "zscaler":
            return []

        policy_name = internet_exit_policy.name

        cloud_name = self._zscaler_endpoints.cloud_name
        connections = []

        # Build internet exit connection for each local interface (wan_interface)
        for wan_interface in local_interfaces:
            if policy_name not in wan_interface.cv_pathfinder_internet_exit.policies:
                continue

            interface_policy_config = wan_interface.cv_pathfinder_internet_exit.policies[policy_name]

            if not wan_interface.peer_ip:
                msg = f"The configured internet-exit policy requires `peer_ip` configured under the WAN Interface {wan_interface.name}."
                raise AristaAvdInvalidInputsError(msg)

            connection_base = {
                "type": "tunnel",
                "source_interface": wan_interface.name,
                "next_hop": wan_interface.peer_ip,
                # Accepting SonarLint issue: The URL is just for verifying connectivity. No data is passed.
                "monitor_url": f"http://gateway.{cloud_name}.net/vpntest",  # NOSONAR
            }

            if interface_policy_config.tunnel_interface_numbers is None:
                msg = (
                    f"{wan_interface.name}.cv_pathfinder_internet_exit.policies[{internet_exit_policy.name}]."
                    "tunnel_interface_numbers needs to be set, when using wan interface for zscaler type internet exit."
                )
                raise AristaAvdInvalidInputsError(msg)

            tunnel_id_range = range_expand(interface_policy_config.tunnel_interface_numbers)

            zscaler_endpoints = (self._zscaler_endpoints.primary, self._zscaler_endpoints.secondary, self._zscaler_endpoints.tertiary)
            for index, zscaler_endpoint in enumerate(zscaler_endpoints):
                if not zscaler_endpoint:
                    continue

                preference = ("primary", "secondary", "tertiary")[index]

                # PRI, SEC, TER used for groups
                # TODO: consider if we should use DC names as group suffix.
                suffix = preference[0:3].upper()

                destination_ip = zscaler_endpoint.ip_address
                tunnel_id = tunnel_id_range[index]
                connections.append(
                    {
                        **connection_base,
                        "name": f"IE-Tunnel{tunnel_id}",
                        "monitor_name": f"IE-Tunnel{tunnel_id}",
                        "monitor_host": destination_ip,
                        "tunnel_id": tunnel_id,
                        # Using Loopback0 as source interface as using the WAN interface causes issues for DPS.
                        "tunnel_ip_address": "unnumbered Loopback0",
                        "tunnel_destination_ip": destination_ip,
                        "ipsec_profile": f"IE-{policy_name}-PROFILE",
                        "description": f"Internet Exit {policy_name} {suffix}",
                        "exit_group": f"{policy_name}_{suffix}",
                        "preference": preference,
                        "suffix": suffix,
                        "endpoint": zscaler_endpoint,
                    },
                )
        return connections
