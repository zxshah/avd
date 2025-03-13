# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from pyavd._eos_designs.eos_designs_facts.facts_generator import facts_contributor

if TYPE_CHECKING:
    from . import FactsStageTwoProtocol


class MlagMixin(Protocol):
    """
    Mixin Class used to generate some of the EosDesignsFacts.

    Class should only be used as Mixin to the EosDesignsFacts class
    Using type-hint on self to get proper type-hints on attributes across all Mixins.
    """

    @facts_contributor
    def mlag_ip(self: FactsStageTwoProtocol) -> None:
        """Exposed in avd_switch_facts."""
        if self.shared_utils.mlag:
            self.facts.mlag_ip = self.shared_utils.mlag_ip

    @facts_contributor
    def mlag_l3_ip(self: FactsStageTwoProtocol) -> None:
        """
        Exposed in avd_switch_facts.

        Only if L3 and not running rfc5549 for both underlay and overlay
        """
        if (
            self.shared_utils.mlag_l3
            and self.shared_utils.mlag_peer_l3_vlan is not None
            and not (self.inputs.underlay_rfc5549 and self.inputs.overlay_mlag_rfc5549)
        ):
            self.facts.mlag_l3_ip = self.shared_utils.mlag_l3_ip

    @facts_contributor
    def mlag_switch_ids(self: FactsStageTwoProtocol) -> None:
        """
        Exposed in avd_switch_facts.

        Returns the switch ids of both primary and secondary switches for a this node group
        {"primary": int, "secondary": int}
        """
        if mlag_switch_ids := self.shared_utils.mlag_switch_ids:
            self.facts.mlag_switch_ids._update(primary=mlag_switch_ids["primary"], secondary=mlag_switch_ids["secondary"])
