# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from pyavd._eos_cli_config_gen.schema import EosCliConfigGen
from pyavd._eos_designs.schema import EosDesigns
from pyavd._eos_designs.structured_config.structured_config_generator import structured_config_contributor
from pyavd._errors import AristaAvdInvalidInputsError

if TYPE_CHECKING:
    from . import AvdStructuredConfigNetworkServicesProtocol


class RouterInternetExitMixin(Protocol):
    """
    Mixin Class used to generate structured config for one key.

    Class should only be used as Mixin to a AvdStructuredConfig class.
    """

    @structured_config_contributor
    def router_internet_exit(self: AvdStructuredConfigNetworkServicesProtocol) -> None:
        """
        Set the structured config for router_internet_exit.

        Only used for CV Pathfinder edge routers today
        """
        if not self._filtered_internet_exit_policies_and_connections:
            return

        policies = EosCliConfigGen.RouterInternetExit.Policies()
        exit_groups = EosCliConfigGen.RouterInternetExit.ExitGroups()
        for policy, connections in self._filtered_internet_exit_policies_and_connections:
            # TODO: Today we use the order of the connection list to order the exit-groups inside the policy.
            #       This works for zscaler but later we may need to use some sorting intelligence as order matters.
            for connection in connections:
                exit_group_name = connection["exit_group"]
                exit_groups.obtain(exit_group_name).local_connections.append_new(name=connection["name"])
                # Recording the exit_group in the policy
                policies.obtain(policy.name).exit_groups.append_new(name=exit_group_name)

            if policy.fallback_to_system_default:
                policies.obtain(policy.name).exit_groups.append_new(name="system-default-exit-group")

        self.structured_config.router_internet_exit._update(policies=policies, exit_groups=exit_groups)

    def _set_internet_exit_policy(
        self: AvdStructuredConfigNetworkServicesProtocol,
        input_topology: EosDesigns.WanVirtualTopologies.ControlPlaneVirtualTopology
        | EosDesigns.WanVirtualTopologies.PoliciesItem.DefaultVirtualTopology
        | EosDesigns.WanVirtualTopologies.PoliciesItem.ApplicationVirtualTopologiesItem,
    ) -> None:
        """
        Set the internet exit policy for a given Virtual Topology if required.

        TODO Make this description nice
        """
        if not self.shared_utils.is_cv_pathfinder_client:
            return

        if not (internet_policy_name := input_topology.internet_exit.policy):
            return

        # TODO: the older function was handling multiple definition
        # if not internet_exit_policy_name or internet_exit_policy_name in internet_exit_policy_names:
        #     continue

        if internet_policy_name not in self.inputs.cv_pathfinder_internet_exit_policies:
            msg = (
                f"The internet exit policy {internet_policy_name} configured under "
                f"`wan_virtual_topologies.policies[name={input_policy.name}].internet_exit.policy` "
                "is not defined under `cv_pathfinder_internet_exit_policies`."
            )
            raise AristaAvdInvalidInputsError(msg)

        internet_exit_policy = self.inputs.cv_pathfinder_internet_exit_policies[internet_policy_name]

        # TODO: Adding to sets
        # internet_exit_policy_names.add(internet_exit_policy_name)
        # candidate_internet_exit_policies.append(internet_exit_policy)

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
            self.set_internet_exit_monitor_connectivity(connection)
            self.set_internet_exit_connection_static_route(connection)
            self.set_internet_exit_tunnel_interface(internet_exit_policy, connection)
            self.set_internet_exit_router_service_insertion(connection)
            self.set_internet_exit_connection_ethernet_interfaces(internet_exit_policy, connection)

        if internet_exit_policy.fallback_to_system_default:
            policy_exit_groups.append_new(name="system-default-exit-group")

        self.structured_config.router_internet_exit.policies.append_new(name=internet_exit_policy.name, exit_groups=policy_exit_groups)
        # TODO: call this only for zscaler.
        self._set_zscaler_internet_exit_policy_ip_securityip_security(internet_exit_policy)
