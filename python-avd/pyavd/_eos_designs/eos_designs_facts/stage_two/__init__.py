# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from pyavd._eos_designs.eos_designs_facts.facts_generator import FactsGenerator, FactsGeneratorProtocol, facts_contributor
from pyavd._eos_designs.eos_designs_facts.schema import EosDesignsFacts
from pyavd._errors import AristaAvdError

from .mlag import MlagMixin
from .overlay import OverlayMixin
from .vlans import VlansMixin

if TYPE_CHECKING:
    from collections.abc import Mapping

    from _eos_designs.schema import EosDesigns
    from _eos_designs.shared_utils import SharedUtilsProtocol

    from pyavd._eos_designs.eos_designs_facts.schema import EosDesignsFacts


class FactsStageTwoProtocol(MlagMixin, OverlayMixin, VlansMixin, FactsGeneratorProtocol, Protocol):
    peer_facts: dict[str, EosDesignsFacts]

    @facts_contributor
    def evpn_multicast(self) -> None:
        """
        Is EPVN Multicast enabled?

        This method _must_ be in EosDesignsFacts and not in SharedUtils, since it reads the SharedUtils instance on the peer.
        This is only possible when running from EosDesignsFacts, since this is the only time where we can access the actual
        python instance of EosDesignsFacts and not the simplified dict.
        """
        if "evpn" not in self.shared_utils.overlay_address_families:
            return
        if self.inputs.evpn_multicast and self.shared_utils.vtep:
            if not (self.shared_utils.underlay_multicast and self.shared_utils.igmp_snooping_enabled):
                msg = "'evpn_multicast: True' is only supported in combination with 'underlay_multicast: True' and 'igmp_snooping_enabled : True'"
                raise AristaAvdError(msg)

            if (
                self.shared_utils.mlag
                and self.shared_utils.overlay_rd_type_admin_subfield
                == self.shared_utils.mlag_peer_facts.only_used_for_peer_facts.overlay_rd_type_admin_subfield
            ):
                msg = "For MLAG devices Route Distinguisher must be unique when 'evpn_multicast: True' since it will create a multi-vtep configuration."
                raise AristaAvdError(msg)
            self.facts.evpn_multicast = True

    @facts_contributor
    def local_vrfs_in_use(self) -> None:
        self.facts.only_used_for_peer_facts.local_vrfs_in_use.extend(self.shared_utils.vrfs)

    @facts_contributor
    def short_esi(self) -> None:
        """
        The short_esi value to use for this device.

        Note: Secondary MLAG switch should have the same short-esi value
        as primary MLAG switch.
        """
        # On the MLAG Secondary use short-esi from MLAG primary
        if self.shared_utils.mlag_role == "secondary" and (peer_short_esi := self.shared_utils.mlag_peer_facts.local_short_esi):
            self.facts.short_esi = peer_short_esi
        self.facts.short_esi = self.facts.local_short_esi


class FactsStageTwo(FactsGenerator, FactsStageTwoProtocol):
    """
    `FactsStageTwo` is based on `FactsGeneratorProtocol`, so make sure to read the description there first.

    All methods relies on other device's facts either directly or indirectly, so this class has an extra argument of peer_facts, which is a dictionary
    with facts set during Stage One for all all other devices.
    """

    def __init__(
        self, hostvars: Mapping, inputs: EosDesigns, facts: EosDesignsFacts, shared_utils: SharedUtilsProtocol, peer_facts: dict[str, EosDesignsFacts]
    ) -> None:
        self.peer_facts = peer_facts
        super().__init__(hostvars, inputs, facts, shared_utils)
