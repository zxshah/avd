# Copyright (c) 2024-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Protocol

from pyavd._eos_cli_config_gen.schema import EosCliConfigGen
from pyavd._eos_designs.schema import EosDesigns
from pyavd._errors import AristaAvdError
from pyavd._utils import get_ip_from_ip_prefix

if TYPE_CHECKING:
    from pyavd._eos_designs.schema import EosDesigns

    from . import AvdStructuredConfigNetworkServicesProtocol


class IpAccesslistsMixin(Protocol):
    """
    Mixin Class used to generate structured config for one key.

    Class should only be used as Mixin to a AvdStructuredConfig class.
    """

    def _set_ipv4_acl(self: AvdStructuredConfigNetworkServicesProtocol, ipv4_acl: EosDesigns.Ipv4AclsItem) -> None:
        """
        Set structured config for ip_access_lists.

        Called for each interface in l3_interfaces and l3_port_channels when applying ipv4_acls
        """
        self.structured_config.ip_access_lists.append(ipv4_acl._cast_as(EosCliConfigGen.IpAccessListsItem))

    def _set_direct_ie_policy_acl(self: AvdStructuredConfigNetworkServicesProtocol, connections: list) -> None:
        # TODO: this is replicated
        acls = self._acl_internet_exit_user_defined("direct")
        if acls:
            self.structured_config.ip_access_lists.append(acls._cast_as(EosCliConfigGen.IpAccessListsItem))
            return

        interface_ips = set()
        for connection in connections:
            interface_ips.add(connection["source_interface_ip_address"])

        if interface_ips:
            acl = EosCliConfigGen.IpAccessListsItem(name=self.get_internet_exit_nat_acl_name("direct"))
            interface_ips = sorted(interface_ips)
            i = 0
            for i, interface_ip in enumerate(interface_ips):
                acl.entries.append_new(sequence=10 + i * 10, action="deny", protocol="ip", source=get_ip_from_ip_prefix(interface_ip), destination="any")
            acl.entries.append_new(
                sequence=20 + i * 10,
                action="permit",
                protocol="ip",
                source="any",
                destination="any",
            )

            self.structured_config.ip_access_lists.append(acl)

    def _set_zscaler_ie_policy_acl(self: AvdStructuredConfigNetworkServicesProtocol) -> None:
        # TODO: this is replicated
        acls = self._acl_internet_exit_user_defined("zscaler")
        if acls:
            self.structured_config.ip_access_lists.append(acls._cast_as(EosCliConfigGen.IpAccessListsItem))
            return
        ip_access_list = EosCliConfigGen.IpAccessListsItem(name=self.get_internet_exit_nat_acl_name("zscaler"))
        ip_access_list.entries.append_new(sequence=10, action="permit", protocol="ip", source="any", destination="any")
        self.structured_config.ip_access_lists.append(ip_access_list)

    def _acl_internet_exit_user_defined(
        self: AvdStructuredConfigNetworkServicesProtocol, internet_exit_policy_type: Literal["zscaler", "direct"]
    ) -> EosDesigns.Ipv4AclsItem | None:
        acl_name = self.get_internet_exit_nat_acl_name(internet_exit_policy_type)
        if acl_name not in self.inputs.ipv4_acls:
            # TODO: Evaluate if we should continue so we raise when there is no ACL.
            return None

        # pass substitution fields as anything to check if acl requires substitution or not
        acl = self.shared_utils.get_ipv4_acl(acl_name, "random", interface_ip="random", peer_ip="random")
        if acl.name == acl_name:
            # ACL doesn't need replacement
            return acl

        # TODO: We still have one nat for all interfaces, need to also add logic to make nat per interface
        # if acl needs substitution
        msg = f"ipv4_acls[name={acl_name}] field substitution is not supported for internet exit access lists"
        raise AristaAvdError(msg)
