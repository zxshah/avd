# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from pyavd._eos_designs.eos_designs_facts.facts_generator import facts_contributor

if TYPE_CHECKING:
    from . import FactsStageOneProtocol


class MlagMixin(Protocol):
    """
    Mixin Class used to generate some of the EosDesignsFacts.

    Class should only be used as Mixin to the EosDesignsFacts class
    Using type-hint on self to get proper type-hints on attributes across all Mixins.
    """

    @facts_contributor
    def mlag_peer(self: FactsStageOneProtocol) -> None:
        """Exposed in avd_switch_facts."""
        if self.shared_utils.mlag:
            self.facts.mlag_peer = self.shared_utils.mlag_peer

    @facts_contributor
    def mlag_port_channel_id(self: FactsStageOneProtocol) -> None:
        """Exposed in avd_switch_facts."""
        if self.shared_utils.mlag:
            self.facts.mlag_port_channel_id = self.shared_utils.mlag_port_channel_id

    @facts_contributor
    def mlag_interfaces(self: FactsStageOneProtocol) -> None:
        """Exposed in avd_switch_facts."""
        if self.shared_utils.mlag:
            self.facts.mlag_interfaces.extend(self.shared_utils.mlag_interfaces)

    @facts_contributor
    def mlag(self: FactsStageOneProtocol) -> None:
        """Exposed in avd_switch_facts."""
        self.facts.only_used_for_peer_facts.mlag = self.shared_utils.mlag
