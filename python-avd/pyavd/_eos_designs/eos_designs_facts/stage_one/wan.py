# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from pyavd._eos_designs.eos_designs_facts.facts_generator import facts_contributor
from pyavd._eos_designs.eos_designs_facts.schema import EosDesignsFacts

if TYPE_CHECKING:
    from . import FactsStageOneProtocol


class WanMixin(Protocol):
    """
    Mixin Class providing a subset of EosDesignsFacts.

    Class should only be used as Mixin to the EosDesignsFacts class
    Using type-hint on self to get proper type-hints on attributes across all Mixins.
    """

    @facts_contributor
    def wan_path_groups(self: FactsStageOneProtocol) -> None:
        """
        Return the list of WAN path_groups directly connected to this router.

        Each with a list of dictionaries containing the (interface, ip_address) in the path_group.

        TODO: Also add the path_groups importing any of our connected path groups.
              Need to find out if we need to resolve recursive imports.
        """
        if not self.shared_utils.is_wan_router:
            return

        for wan_path_group in self.shared_utils.wan_local_path_groups:
            wan_path_group_item = wan_path_group._cast_as(EosDesignsFacts.WanPathGroupsItem)
            for interface in wan_path_group._internal_data.interfaces:
                wan_path_group_item.interfaces.append_new(
                    name=interface["name"],
                    connected_to_pathfinder=interface["connected_to_pathfinder"],
                    public_ip=interface.get("public_ip"),
                    wan_circuit_id=interface.get("wan_circuit_id"),
                )
            self.facts.wan_path_groups.append(wan_path_group_item)
