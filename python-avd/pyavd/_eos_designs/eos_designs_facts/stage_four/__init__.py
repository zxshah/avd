# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Protocol

from pyavd._eos_designs.eos_designs_facts.facts_generator import FactsGenerator, FactsGeneratorProtocol
from pyavd._eos_designs.eos_designs_facts.schema import EosDesignsFacts
from pyavd.j2filters import range_expand

from .uplinks import UplinksMixin

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pyavd._eos_designs.eos_designs_facts.schema import EosDesignsFacts
    from pyavd._eos_designs.schema import EosDesigns
    from pyavd._eos_designs.shared_utils import SharedUtilsProtocol


class FactsStageFourProtocol(UplinksMixin, FactsGeneratorProtocol, Protocol):
    peer_facts: dict[str, EosDesignsFacts]

    @cached_property
    def _vlans(self: FactsStageFourProtocol) -> set[int]:
        """
        Decompressed list of vlans to be defined on this switch after filtering network services.

        The filter is based on filter.tenants, filter.tags and filter.only_vlans_in_use.
        """
        return set(map(int, range_expand(self.facts.vlans)))


class FactsStageFour(FactsGenerator, FactsStageFourProtocol):
    """
    `FactsStageFour` is based on `FactsGeneratorProtocol`, so make sure to read the description there first.

    All methods relies on other device's facts either directly or indirectly, so this class has an extra argument of peer_facts, which is a dictionary
    with facts set during Stage One for all all other devices.
    """

    def __init__(
        self, hostvars: Mapping, inputs: EosDesigns, facts: EosDesignsFacts, shared_utils: SharedUtilsProtocol, peer_facts: dict[str, EosDesignsFacts]
    ) -> None:
        self.peer_facts = peer_facts
        super().__init__(hostvars, inputs, facts, shared_utils)
