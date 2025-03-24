# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from pyavd._eos_cli_config_gen.schema import EosCliConfigGen

if TYPE_CHECKING:
    from pyavd._eos_designs.schema import EosDesigns

    from . import AvdStructuredConfigNetworkServicesProtocol


class TunnelInterfacesMixin(Protocol):
    """
    Mixin Class used to generate structured config for one key.

    Class should only be used as Mixin to a AvdStructuredConfig class.
    """

    def set_internet_exit_tunnel_interface(
        self: AvdStructuredConfigNetworkServicesProtocol, internet_exit_policy: EosDesigns.CvPathfinderInternetExitPoliciesItem, connection: dict
    ) -> None:
        """
        Set structured config for one tunnel_interface for an Internet Exit connection.

        Only used for CV Pathfinder edge routers today
        """
        if connection["type"] != "tunnel":
            return

        tunnel_interface = EosCliConfigGen.TunnelInterfacesItem(
            name=f"Tunnel{connection['tunnel_id']}",
            description=connection["description"],
            mtu=1394,  # TODO: do not hardcode
            ip_address=connection["tunnel_ip_address"],
            tunnel_mode="ipsec",  # TODO: do not hardcode
            source_interface=connection["source_interface"],
            destination=connection["tunnel_destination_ip"],
            ipsec_profile=connection["ipsec_profile"],
        )

        if internet_exit_policy.type == "zscaler":
            tunnel_interface.nat_profile = self.get_internet_exit_nat_profile_name(internet_exit_policy.type)

        self.structured_config.tunnel_interfaces.append(tunnel_interface)
