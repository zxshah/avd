# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from functools import cached_property, lru_cache
from typing import TYPE_CHECKING, Literal, Protocol

from pyavd._eos_cli_config_gen.schema import EosCliConfigGen
from pyavd._eos_designs.schema import EosDesigns
from pyavd._eos_designs.structured_config.structured_config_generator import structured_config_contributor
from pyavd._errors import AristaAvdError, AristaAvdInvalidInputsError, AristaAvdMissingVariableError
from pyavd._utils.password_utils.password import simple_7_encrypt
from pyavd.j2filters import natural_sort, range_expand

if TYPE_CHECKING:
    from . import AvdStructuredConfigNetworkServicesProtocol


class UtilsWanMixin(Protocol):
    """
    Mixin Class with internal functions for WAN.

    Class should only be used as Mixin to a AvdStructuredConfig class.
    """

    @cached_property
    def _filtered_wan_vrfs(self: AvdStructuredConfigNetworkServicesProtocol) -> EosDesigns.WanVirtualTopologies.Vrfs:
        """Loop through all the VRFs defined under `wan_virtual_topologies.vrfs` and returns a list of mode."""
        wan_vrfs = EosDesigns.WanVirtualTopologies.Vrfs(
            vrf for vrf in self.inputs.wan_virtual_topologies.vrfs if vrf.name in self.shared_utils.vrfs or self.shared_utils.is_wan_server
        )

        # Check that default is in the list as it is required everywhere
        if "default" not in wan_vrfs:
            wan_vrfs.append(EosDesigns.WanVirtualTopologies.VrfsItem(name="default", wan_vni=1))

        return wan_vrfs

    @structured_config_contributor
    def set_wan_policies(self: AvdStructuredConfigNetworkServicesProtocol) -> None:
        if not self.shared_utils.is_wan_router:
            return

        append_policy = self._append_autovpn_policy if self.inputs.wan_mode == "autovpn" else self._append_cv_pathfinder_policy

        for vrf in self._filtered_wan_vrfs:
            if vrf.policy not in self.inputs.wan_virtual_topologies.policies:
                if vrf.policy == self._default_wan_policy_name and self._default_wan_policy_name not in self.inputs.wan_virtual_topologies.policies:
                    vrf_policy = self._default_wan_policy
                else:
                    msg = (
                        f"The policy {vrf.policy} applied to vrf {vrf.name} under `wan_virtual_topologies.vrfs` is not "
                        "defined under `wan_virtual_topologies.policies`."
                    )
                    raise AristaAvdInvalidInputsError(msg)
            else:
                vrf_policy = self.inputs.wan_virtual_topologies.policies[vrf.policy]

            # TODO: it seems we could set multiple time the same policy here so need to check
            append_policy(vrf_policy, vrf, control_plane=vrf.name == "default")

        # Add Application Traffic Recognition after all policies have been taken care off
        # TODO: but this in a better place.
        self._set_control_plane_application_profile()
        self.set_cv_pathfinder_metadata_applications()

    def _append_control_plane_virtual_topology(
        self: AvdStructuredConfigNetworkServicesProtocol,
        policy: EosDesigns.WanVirtualTopologies.PoliciesItem,
        output_policy: EosCliConfigGen.RouterAdaptiveVirtualTopology.PoliciesItem | EosCliConfigGen.RouterPathSelection.PoliciesItem,
        output_vrf: EosCliConfigGen.RouterAdaptiveVirtualTopology.VrfsItem | EosCliConfigGen.RouterPathSelection.VrfsItem,
    ) -> None:
        control_plane_virtual_topology = self._wan_control_plane_virtual_topology

        if (
            load_balance_policy := self._generate_wan_load_balance_policy(
                self._wan_control_plane_profile_name,
                control_plane_virtual_topology,
                output_policy.name,
            )
        ) is None:
            msg = "The WAN control-plane load-balance policy is empty. Make sure at least one path-group can be used in the policy"
            raise AristaAvdError(msg)

        if self.inputs.wan_mode == "autovpn":
            output_policy.rules.append_new(
                id=10,
                application_profile=self.inputs.wan_virtual_topologies.control_plane_virtual_topology.application_profile,
                load_balance=load_balance_policy.name,
            )
        else:
            # control plane
            output_policy.matches.append_new(
                application_profile=self.inputs.wan_virtual_topologies.control_plane_virtual_topology.application_profile,
                avt_profile=self._wan_control_plane_profile_name,
                traffic_class=control_plane_virtual_topology.traffic_class,
                dscp=control_plane_virtual_topology.dscp,
            )

            # Add profile
            profile = EosCliConfigGen.RouterAdaptiveVirtualTopology.ProfilesItem(
                name=self._wan_control_plane_profile_name,
                load_balance_policy=load_balance_policy.name,
            )
            if control_plane_virtual_topology.internet_exit.policy:
                self._verify_internet_exit_policy(control_plane_virtual_topology.internet_exit.policy, output_policy.name)
                if self._internet_exit_policy_has_local_interfaces(control_plane_virtual_topology.internet_exit.policy):
                    profile.internet_exit_policy = control_plane_virtual_topology.internet_exit.policy

            self.structured_config.router_adaptive_virtual_topology.profiles.append(profile)
            output_vrf.profiles.append_new(name=self._wan_control_plane_profile_name, id=254)

            # Handling Internet Exit
            self._set_internet_exit_policy(control_plane_virtual_topology, output_policy.name)

        # Add load_balance_policy
        self.structured_config.router_path_selection.load_balance_policies.append(load_balance_policy)
        self._set_virtual_topology_application_classification(control_plane_virtual_topology, output_policy.name)

    def _append_autovpn_policy(
        self: AvdStructuredConfigNetworkServicesProtocol,
        policy: EosDesigns.WanVirtualTopologies.PoliciesItem,
        vrf: EosDesigns.WanVirtualTopologies.VrfsItem,
        *,
        control_plane: bool = False,
    ) -> EosCliConfigGen.RouterPathSelectionItems.PoliciesItem:
        index = 1
        output_policy = EosCliConfigGen.RouterPathSelection.PoliciesItem(name=policy.name)
        output_vrf = EosCliConfigGen.RouterPathSelection.VrfsItem(name=vrf.name)

        # Control plane
        if control_plane:
            output_policy.name = f"{output_policy.name}-WITH-CP"
            self._append_control_plane_virtual_topology(policy, output_policy, output_vrf)
            index = 2

        # Normal entries
        for application_virtual_topology in policy.application_virtual_topologies:
            name = application_virtual_topology.name or self._default_profile_name(policy.name, application_virtual_topology.application_profile)
            context_path = f"wan_virtual_topologies.policies[{policy.name}].application_virtual_topologies[{application_virtual_topology.application_profile}]"
            load_balance_policy = self._generate_wan_load_balance_policy(name, application_virtual_topology, context_path)
            if not load_balance_policy:
                # Empty load balance policy so skipping
                # TODO: Add "nodes" or similar under the profile and raise here
                # if the node is set and there are no matching path groups.
                continue

            if not application_virtual_topology.application_profile:
                # TODO: fix message
                # application_profile = application_virtual_topology, "application_profile", required=True)
                msg = "TODO required"
                raise AristaAvdInvalidInputsError(msg)

            output_policy.rules.append_new(
                id=10 * index,
                application_profile=application_virtual_topology.application_profile,
                load_balance=load_balance_policy.name,
            )

            # Add load_balance_policy
            self.structured_config.router_path_selection.load_balance_policies.append(load_balance_policy)
            # Add application traffic recognition
            self._set_virtual_topology_application_classification(application_virtual_topology, policy.name)
            index += 1

        # default match
        self._verify_policy_default_match(policy)
        if not policy.default_virtual_topology.drop_unmatched:
            name = policy.default_virtual_topology.name or self._default_profile_name(policy.name, "DEFAULT")
            context_path = f"wan_virtual_topologies.policies[{policy.name}].default_virtual_topology"
            load_balance_policy = self._generate_wan_load_balance_policy(name, policy.default_virtual_topology, context_path)

            if not load_balance_policy:
                msg = (
                    f"The `default_virtual_topology` path-groups configuration for `wan_virtual_topologies.policies[{policy.name}]` produces "
                    "an empty load-balancing policy. Make sure at least one path-group present on the device is allowed in the "
                    "`default_virtual_topology` path-groups."
                )
                raise AristaAvdError(msg)

            output_policy.default_match.load_balance = load_balance_policy.name
            # Add load_balance_policy
            self.structured_config.router_path_selection.load_balance_policies.append(load_balance_policy)

        # TODO: handle below
        if not output_policy.rules and not output_policy.default_match:
            # The policy is empty but should be assigned to a VRF
            msg = (
                f"The policy `wan_virtual_topologies.policies[{policy.name}]` cannot match any traffic but is assigned to a VRF. "
                "Make sure at least one path-group present on the device is used in the policy."
            )
            raise AristaAvdError(msg)

        self.structured_config.router_path_selection.policies.append(output_policy)
        return output_policy

    def _verify_policy_default_match(self: AvdStructuredConfigNetworkServicesProtocol, policy: EosDesigns.WanVirtualTopologies.PoliciesItem) -> None:
        """
        Verifies the policy has a proper default_match definition.

        Checks that:
            * the default_virtual_topology is defined.
            * either drop_unmatched must be set or some path_groups must be defined.

        Raises:
            AristaAvdInvalidInputsError: if any criteria is not met.
        """
        if not policy.default_virtual_topology:
            msg = f"wan_virtual_topologies.policies[{policy.name}].default_virtual_toplogy."
            raise AristaAvdInvalidInputsError(msg)

        if not policy.default_virtual_topology.drop_unmatched:
            context_path = f"wan_virtual_topologies.policies[{policy.name}].default_virtual_topology"
            # Verify that path_groups are set or raise
            # TODO: this functionality could be added to schema
            if not policy.default_virtual_topology.path_groups:
                msg = f"Either 'drop_unmatched' or 'path_groups' must be set under '{context_path}'."
                raise AristaAvdInvalidInputsError(msg)

    def _append_cv_pathfinder_policy(
        self: AvdStructuredConfigNetworkServicesProtocol,
        policy: EosDesigns.WanVirtualTopologies.PoliciesItem,
        vrf: EosDesigns.WanVirtualTopologies.VrfsItem,
        *,
        control_plane: bool = False,
    ) -> EosCliConfigGen.RouterAdaptiveVirtualTopology.PoliciesItem:
        """
        TODO.

        Add policy to the output.
        """
        output_policy = EosCliConfigGen.RouterAdaptiveVirtualTopology.PoliciesItem(name=policy.name)
        # Maybe set it directly
        output_vrf = EosCliConfigGen.RouterAdaptiveVirtualTopology.VrfsItem(name=vrf.name)

        # Control Plane
        if control_plane:
            output_policy.name = f"{output_policy.name}-WITH-CP"
            self._append_control_plane_virtual_topology(policy, output_policy, output_vrf)

        output_vrf.policy = output_policy.name

        # Normal entries
        for application_virtual_topology in policy.application_virtual_topologies:
            name = application_virtual_topology.name or self._default_profile_name(policy.name, application_virtual_topology.application_profile)
            context_path = f"wan_virtual_topologies.policies[{policy.name}].application_virtual_topologies[{application_virtual_topology.application_profile}]"
            load_balance_policy = self._generate_wan_load_balance_policy(name, application_virtual_topology, context_path)

            if not load_balance_policy:
                # Empty load balance policy so skipping
                # TODO: Add "nodes" or similar under the profile and raise here
                # if the node is set and there are no matching path groups.
                continue

            if not application_virtual_topology.application_profile:
                # TODO: fix message
                # application_profile = application_virtual_topology, "application_profile", required=True)
                msg = "TODO required"
                raise AristaAvdInvalidInputsError(msg)

            if not application_virtual_topology.id:
                msg = (
                    f"Missing mandatory `id` in "
                    f"`wan_virtual_topologies.policies[{policy.name}].application_virtual_topologies[{application_virtual_topology.application_profile}]` "
                    "when `wan_mode` is 'cv-pathfinder."
                )
                raise AristaAvdInvalidInputsError(msg)

            output_policy.matches.append_new(
                application_profile=application_virtual_topology.application_profile,
                avt_profile=name,
                traffic_class=application_virtual_topology.traffic_class,
                dscp=application_virtual_topology.dscp,
            )
            output_vrf.profiles.append_new(id=application_virtual_topology.id, name=name)

            # Add load_balance_policy
            self.structured_config.router_path_selection.load_balance_policies.append(load_balance_policy)
            # Add application traffic recognition
            self._set_virtual_topology_application_classification(application_virtual_topology, policy.name)

            # Need to create the object and not use append_new otherwise it conflicts
            # with other profiles as we are not adding the internet_exit_policy immediately
            profile = EosCliConfigGen.RouterAdaptiveVirtualTopology.ProfilesItem(
                name=name,
                load_balance_policy=load_balance_policy.name,
            )
            # TODO: refactor filtered_internet_exit_policies_and_connections
            if application_virtual_topology.internet_exit.policy:
                self._verify_internet_exit_policy(application_virtual_topology.internet_exit.policy, policy.name)
                if self._internet_exit_policy_has_local_interfaces(application_virtual_topology.internet_exit.policy):
                    profile.internet_exit_policy = application_virtual_topology.internet_exit.policy

            self.structured_config.router_adaptive_virtual_topology.profiles.append(profile)

            # Handling Internet Exit
            self._set_internet_exit_policy(application_virtual_topology, output_policy.name)

        # default match
        self._verify_policy_default_match(policy)
        if not policy.default_virtual_topology.drop_unmatched:
            name = policy.default_virtual_topology.name or self._default_profile_name(policy.name, "DEFAULT")
            context_path = f"wan_virtual_topologies.policies[{policy.name}].default_virtual_topology"
            load_balance_policy = self._generate_wan_load_balance_policy(name, policy.default_virtual_topology, context_path)

            if not load_balance_policy:
                msg = (
                    f"The `default_virtual_topology` path-groups configuration for `wan_virtual_topologies.policies[{policy.name}]` produces "
                    "an empty load-balancing policy. Make sure at least one path-group present on the device is allowed in the "
                    "`default_virtual_topology` path-groups."
                )
                raise AristaAvdError(msg)

            output_policy.matches.append_new(
                application_profile="default",
                avt_profile=name,
                traffic_class=policy.default_virtual_topology.traffic_class,
                dscp=policy.default_virtual_topology.dscp,
            )
            # Add load_balance_policy
            self.structured_config.router_path_selection.load_balance_policies.append(load_balance_policy)

            profile = EosCliConfigGen.RouterAdaptiveVirtualTopology.ProfilesItem(
                name=name,
                load_balance_policy=load_balance_policy.name,
            )
            if policy.default_virtual_topology.internet_exit.policy:
                self._verify_internet_exit_policy(policy.default_virtual_topology.internet_exit.policy, policy.name)
                if self._internet_exit_policy_has_local_interfaces(policy.default_virtual_topology.internet_exit.policy):
                    profile.internet_exit_policy = policy.default_virtual_topology.internet_exit.policy
            self.structured_config.router_adaptive_virtual_topology.profiles.append(profile)
            output_vrf.profiles.append_new(id=1, name=name)

            # Handling Internet Exit
            self._set_internet_exit_policy(policy.default_virtual_topology, output_policy.name)

        # TODO: handle below
        if not output_policy.matches:
            # The policy is empty but should be assigned to a VRF
            msg = (
                f"The policy `wan_virtual_topologies.policies[{policy.name}]` cannot match any traffic but is assigned to a VRF. "
                "Make sure at least one path-group present on the device is used in the policy."
            )
            raise AristaAvdError(msg)

        self.structured_config.router_adaptive_virtual_topology.policies.append(output_policy)
        self.structured_config.router_adaptive_virtual_topology.vrfs.append(output_vrf)

    def _verify_internet_exit_policy(self: AvdStructuredConfigNetworkServicesProtocol, ie_policy_name: str, policy_name: str) -> None:
        """Check if the Internet Exit policy name is configured.

        If not raise an AristaAvdInvalidInputsError.

        TODO: This used to check that there is an interface to make it valid.
        """
        if ie_policy_name not in self.inputs.cv_pathfinder_internet_exit_policies:
            msg = (
                f"The internet exit policy {ie_policy_name} configured under "
                f"`wan_virtual_topologies.policies[name={policy_name}].internet_exit.policy` "
                "is not defined under `cv_pathfinder_internet_exit_policies`."
            )
            raise AristaAvdInvalidInputsError(msg)

    @lru_cache
    def _internet_exit_policy_has_local_interfaces(self: AvdStructuredConfigNetworkServicesProtocol, ie_policy_name: str) -> bool:
        """Cached property stating if an internet exit is used locally."""
        local_wan_l3_interfaces = EosDesigns._DynamicKeys.DynamicNodeTypesItem.NodeTypes.NodesItem.L3Interfaces(
            [wan_interface for wan_interface in self.shared_utils.wan_interfaces if ie_policy_name in wan_interface.cv_pathfinder_internet_exit.policies]
        )
        return bool(local_wan_l3_interfaces)

    def _generate_wan_load_balance_policy(
        self: AvdStructuredConfigNetworkServicesProtocol,
        name: str,
        input_topology: EosDesigns.WanVirtualTopologies.ControlPlaneVirtualTopology
        | EosDesigns.WanVirtualTopologies.PoliciesItem.DefaultVirtualTopology
        | EosDesigns.WanVirtualTopologies.PoliciesItem.ApplicationVirtualTopologiesItem,
        context_path: str,
    ) -> EosCliConfigGen.RouterPathSelection.LoadBalancePoliciesItem | None:
        """
        Generate and return a router path-selection load-balance policy.

        If HA is enabled:
        * the remote peer path-groups are considered.
        * inject the HA path-group with priority 1.

        Attrs:
            name (str): The name to use as prefix for the Load Balance policy
            input_dict (dict): The dictionary containing the list of path-groups and their preference.
            context_path (str): Key used for context for error messages.

        Returns:
            EosCliConfigGen.RouterPathSelection.LoadBalancePoliciesItem | None
        """
        lb_policy_name = self.shared_utils.generate_lb_policy_name(name)

        wan_load_balance_policy = EosCliConfigGen.RouterPathSelection.LoadBalancePoliciesItem(
            name=lb_policy_name,
            jitter=input_topology.constraints.jitter,
            latency=input_topology.constraints.latency,
            loss_rate=input_topology.constraints.loss_rate,
        )

        if self.shared_utils.is_cv_pathfinder_router:
            wan_load_balance_policy.lowest_hop_count = input_topology.lowest_hop_count

        # Using this flag while looping through all entries to keep track of any path group present on the remote host
        any_path_group_on_wan_ha_peer = self.shared_utils.wan_ha

        for policy_entry in input_topology.path_groups:
            policy_entry_priority = None
            if policy_entry.preference:
                policy_entry_priority = self._path_group_preference_to_eos_priority(policy_entry.preference, f"{context_path}[{policy_entry.names}]")

            for path_group_name in policy_entry.names:
                if (priority := policy_entry_priority) is None:
                    # No preference defined at the policy level, need to retrieve the default preference
                    if path_group_name not in self.inputs.wan_path_groups:
                        msg = (
                            f"Failed to retrieve path-group {path_group_name} from `wan_path_groups` when generating load balance policy {lb_policy_name}. "
                            f"Verify the path-groups defined under {context_path}."
                        )
                        raise AristaAvdInvalidInputsError(msg)
                    wan_path_group = self.inputs.wan_path_groups[path_group_name]
                    priority = self._path_group_preference_to_eos_priority(wan_path_group.default_preference, f"wan_path_groups[{wan_path_group.name}]")

                # Skip path-group on this device if not present on the router except for pathfinders
                if self.shared_utils.is_wan_client and path_group_name not in self.shared_utils.wan_local_path_group_names:
                    continue

                wan_load_balance_policy.path_groups.append_new(
                    name=path_group_name,
                    priority=priority if priority != 1 else None,
                )

            # Updating peer path-groups tracking
            any_path_group_on_wan_ha_peer = any_path_group_on_wan_ha_peer and set(self.shared_utils.wan_ha_peer_path_group_names).union(set(policy_entry.names))

        if len(wan_load_balance_policy.path_groups) == 0 and not any_path_group_on_wan_ha_peer:
            # The policy is empty, and either the site is not using HA or no path-group in the policy is present on the HA peer
            return None

        if self.shared_utils.wan_ha or self.shared_utils.is_cv_pathfinder_server:
            # Adding HA path-group with priority 1
            wan_load_balance_policy.path_groups.append_new(name=self.inputs.wan_ha.lan_ha_path_group_name)

        return wan_load_balance_policy

    def _path_group_preference_to_eos_priority(self: AvdStructuredConfigNetworkServicesProtocol, path_group_preference: int | str, context_path: str) -> int:
        """
        Convert "preferred" to 1 and "alternate" to 2. Everything else is returned as is.

        Arguments:
        ----------
        path_group_preference (str|int): The value of the preference key to be converted. It must be either "preferred", "alternate" or an integer.
        context_path (str): Input path context for the error message.
        """
        if path_group_preference == "preferred":
            return 1
        if path_group_preference == "alternate":
            return 2

        failed_conversion = False
        try:
            priority = int(path_group_preference)
        except ValueError:
            failed_conversion = True

        if failed_conversion or not 1 <= priority <= 65535:
            msg = (
                f"Invalid value '{path_group_preference}' for Path-Group preference - should be either 'preferred', "
                f"'alternate' or an integer[1-65535] for {context_path}."
            )
            raise AristaAvdError(msg)

        return priority

    @cached_property
    def _default_wan_policy_name(self: AvdStructuredConfigNetworkServicesProtocol) -> str:
        """TODO: make this configurable."""
        return "DEFAULT-POLICY"

    @cached_property
    def _default_policy_path_group_names(self: AvdStructuredConfigNetworkServicesProtocol) -> list[str]:
        """
        Return a list of path group names for the default policy.

        Return the list of path-groups to consider when generating a default policy with AVD
        whether for the default policy or the special Control-plane policy.
        """
        path_group_names = {path_group.name for path_group in self.inputs.wan_path_groups if not path_group.excluded_from_default_policy}
        if not path_group_names.intersection(self.shared_utils.wan_local_path_group_names):
            # No common path-group between this device local path-groups and the available path-group for the default policy
            msg = (
                f"Unable to generate the default WAN policy as none of the device local path-groups {self.shared_utils.wan_local_path_group_names} "
                "is eligible to be included. Make sure that at least one path-group for the device is not configured with "
                "`excluded_from_default_policy: true` under `wan_path_groups`."
            )
            raise AristaAvdError(msg)
        return natural_sort(path_group_names)

    @cached_property
    def _default_wan_policy(self: AvdStructuredConfigNetworkServicesProtocol) -> EosDesigns.WanVirtualTopologies.PoliciesItem:
        """
        Returning policy containing all path groups not excluded from default policy.

        If no policy is defined for a VRF under 'wan_virtual_topologies.vrfs', a default policy named DEFAULT-POLICY is used
        where all traffic is matched in the default category and distributed amongst all path-groups.
        """
        return EosDesigns.WanVirtualTopologies.PoliciesItem(
            name=self._default_wan_policy_name,
            default_virtual_topology=EosDesigns.WanVirtualTopologies.PoliciesItem.DefaultVirtualTopology(
                path_groups=EosDesigns.WanVirtualTopologies.PoliciesItem.DefaultVirtualTopology.PathGroups(
                    [
                        EosDesigns.WanVirtualTopologies.PoliciesItem.DefaultVirtualTopology.PathGroupsItem(
                            names=EosDesigns.WanVirtualTopologies.PoliciesItem.DefaultVirtualTopology.PathGroupsItem.Names(
                                self._default_policy_path_group_names
                            )
                        )
                    ]
                )
            ),
        )

    def _default_profile_name(self: AvdStructuredConfigNetworkServicesProtocol, profile_name: str, application_profile: str) -> str:
        """
        Helper function to consistently return the default name of a profile.

        Returns {profile_name}-{application_profile}
        """
        return f"{profile_name}-{application_profile}"

    @cached_property
    def _wan_control_plane_virtual_topology(self: AvdStructuredConfigNetworkServicesProtocol) -> EosDesigns.WanVirtualTopologies.ControlPlaneVirtualTopology:
        """
        Return the Control plane virtual topology or the default one.

        The default control_plane_virtual_topology, excluding path_groups with excluded_from_default_policy
        """
        if self.inputs.wan_virtual_topologies.control_plane_virtual_topology:
            return self.inputs.wan_virtual_topologies.control_plane_virtual_topology

        path_groups = self._default_policy_path_group_names
        if self.shared_utils.is_wan_client:
            # Filter only the path-groups connected to pathfinder
            path_groups = [path_group for path_group in path_groups if path_group in self._local_path_groups_connected_to_pathfinder]
        return EosDesigns.WanVirtualTopologies.ControlPlaneVirtualTopology(
            path_groups=EosDesigns.WanVirtualTopologies.ControlPlaneVirtualTopology.PathGroups(
                [
                    EosDesigns.WanVirtualTopologies.ControlPlaneVirtualTopology.PathGroupsItem(
                        names=EosDesigns.WanVirtualTopologies.ControlPlaneVirtualTopology.PathGroupsItem.Names(path_groups)
                    )
                ]
            )
        )

    @cached_property
    def _wan_control_plane_profile_name(self: AvdStructuredConfigNetworkServicesProtocol) -> str:
        """Control plane profile name."""
        vrf_default_policy_name = self._filtered_wan_vrfs["default"].policy
        return self._wan_control_plane_virtual_topology.name or f"{vrf_default_policy_name}-CONTROL-PLANE"

    @cached_property
    def _local_path_groups_connected_to_pathfinder(self: AvdStructuredConfigNetworkServicesProtocol) -> list:
        """Return list of names of local path_groups connected to pathfinder."""
        # TODO: Refactor: this is only used in _wan_control_plane_virtual_topology and be merged in the logic.
        return [
            path_group.name
            for path_group in self.shared_utils.wan_local_path_groups
            if any(wan_interface["connected_to_pathfinder"] for wan_interface in path_group._internal_data.interfaces)
        ]

    def get_internet_exit_nat_profile_name(self: AvdStructuredConfigNetworkServicesProtocol, internet_exit_policy_type: Literal["zscaler", "direct"]) -> str:
        return "NAT-IE-ZSCALER" if internet_exit_policy_type == "zscaler" else "NAT-IE-DIRECT"

    def get_internet_exit_nat_acl_name(self: AvdStructuredConfigNetworkServicesProtocol, internet_exit_policy_type: Literal["zscaler", "direct"]) -> str:
        return f"ACL-{self.get_internet_exit_nat_profile_name(internet_exit_policy_type)}"

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

    def _get_ipsec_credentials(
        self: AvdStructuredConfigNetworkServicesProtocol, internet_exit_policy: EosDesigns.CvPathfinderInternetExitPoliciesItem
    ) -> tuple[str, str]:
        """Returns ufqdn, shared_key based on various details from the given internet_exit_policy."""
        if not internet_exit_policy.zscaler.domain_name:
            msg = "zscaler.domain_name"
            raise AristaAvdMissingVariableError(msg)

        if not internet_exit_policy.zscaler.ipsec_key_salt:
            msg = "zscaler.ipsec_key_salt"
            raise AristaAvdMissingVariableError(msg)

        ipsec_key = self._generate_ipsec_key(name=internet_exit_policy.name, salt=internet_exit_policy.zscaler.ipsec_key_salt)
        ufqdn = f"{self.shared_utils.hostname}_{internet_exit_policy.name}@{internet_exit_policy.zscaler.domain_name}"
        return ufqdn, ipsec_key

    def _generate_ipsec_key(self: AvdStructuredConfigNetworkServicesProtocol, name: str, salt: str) -> str:
        """
        Build a secret containing various components for this policy and device.

        Run type-7 obfuscation using a algorithmic salt so we ensure the same key every time.

        TODO: Maybe introduce some formatting with max length of each element, since the keys can become very very long.
        """
        secret = f"{self.shared_utils.hostname}_{name}_{salt}"
        type_7_salt = sum(salt.encode("utf-8")) % 16
        return simple_7_encrypt(secret, type_7_salt)
