# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from pyavd._eos_designs.eos_designs_facts.facts_generator import facts_contributor

if TYPE_CHECKING:
    from . import FactsStageTwoProtocol


class OverlayMixin(Protocol):
    """
    Mixin Class used to generate some of the EosDesignsFacts.

    Class should only be used as Mixin to the EosDesignsFacts class.
    Using type-hint on self to get proper type-hints on attributes across all Mixins.
    """

    @facts_contributor
    def vtep_ip(self: FactsStageTwoProtocol) -> None:
        """Exposed in avd_switch_facts."""
        if self.shared_utils.vtep or self.shared_utils.is_wan_router:
            self.facts.vtep_ip = self.shared_utils.vtep_ip
