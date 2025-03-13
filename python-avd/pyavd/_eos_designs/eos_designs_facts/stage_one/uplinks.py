# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from pyavd._eos_designs.eos_designs_facts.facts_generator import facts_contributor
from pyavd.j2filters import range_expand

if TYPE_CHECKING:
    from . import FactsStageOneProtocol


class UplinksMixin(Protocol):
    """
    Mixin Class used to generate some of the EosDesignsFacts.

    Class should only be used as Mixin to the EosDesignsFacts class.
    Using type-hint on self to get proper type-hints on attributes across all Mixins.
    """

    @facts_contributor
    def max_parallel_uplinks(self: FactsStageOneProtocol) -> None:
        """Exposed in avd_switch_facts."""
        self.facts.max_parallel_uplinks = self.shared_utils.node_config.max_parallel_uplinks

    @facts_contributor
    def max_uplink_switches(self: FactsStageOneProtocol) -> None:
        """Exposed in avd_switch_facts."""
        self.facts.max_uplink_switches = self.shared_utils.max_uplink_switches

    @facts_contributor
    def default_downlink_interfaces(self: FactsStageOneProtocol) -> None:
        """
        Internal default_downlink_interfaces set based on default_interfaces.

        Parsed by downstream switches during eos_designs_facts phase.
        """
        self.facts.only_used_for_peer_facts.default_downlink_interfaces.extend(range_expand(self.shared_utils.default_interfaces.downlink_interfaces))

    @facts_contributor
    def uplink_type(self: FactsStageOneProtocol) -> None:
        """Exposed in avd_switch_facts."""
        self.facts.only_used_for_peer_facts.uplink_type = self.shared_utils.node_config.uplink_type

    @facts_contributor
    def uplink_switch_port_channel_id(self: FactsStageOneProtocol) -> None:
        """Exposed in avd_switch_facts."""
        self.facts.only_used_for_peer_facts.uplink_switch_port_channel_id = self.shared_utils.node_config.uplink_switch_port_channel_id

    @facts_contributor
    def uplink_port_channel_id(self: FactsStageOneProtocol) -> None:
        """Exposed in avd_switch_facts."""
        self.facts.only_used_for_peer_facts.uplink_port_channel_id = self.shared_utils.node_config.uplink_port_channel_id
