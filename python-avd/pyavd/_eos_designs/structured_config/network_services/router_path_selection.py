# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from pyavd._eos_designs.structured_config.structured_config_generator import structured_config_contributor

if TYPE_CHECKING:
    from . import AvdStructuredConfigNetworkServicesProtocol


class RouterPathSelectionMixin(Protocol):
    """
    Mixin Class used to generate structured config for one key.

    Class should only be used as Mixin to a AvdStructuredConfig class.
    """

    @structured_config_contributor
    def router_path_selection(self: AvdStructuredConfigNetworkServicesProtocol) -> None:
        """Set the structured config for router path-selection (DPS)."""
        if not self.shared_utils.is_wan_router:
            return
        # load balancing policies and WAN policies are set in utils_wan.

        # When running CV Pathfinder, only load balance policies are configured
        # for AutoVPN, need also vrfs and policies.
        if self.inputs.wan_mode == "autovpn":
            for vrf in self._filtered_wan_vrfs:
                self.structured_config.router_path_selection.vrfs.append_new(
                    name=vrf.name,
                    path_selection_policy=f"{vrf.policy}-WITH-CP" if vrf.name == "default" else vrf.policy,
                )
