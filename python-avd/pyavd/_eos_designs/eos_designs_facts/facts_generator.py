# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Protocol

from pyavd._eos_designs.avdfacts import AvdFacts, AvdFactsProtocol

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import TypeVar

    from typing_extensions import Self

    from pyavd._eos_designs.eos_designs_facts.schema import EosDesignsFacts
    from pyavd._eos_designs.schema import EosDesigns
    from pyavd._eos_designs.shared_utils import SharedUtilsProtocol

    T_FactsGeneratorSubclass = TypeVar("T_FactsGeneratorSubclass", bound="FactsGeneratorProtocol")


def facts_contributor(func: Callable[[T_FactsGeneratorSubclass], None]) -> Callable[[T_FactsGeneratorSubclass], None]:
    """Decorator to mark methods that contribute to the structured config."""
    func._is_facts_contributor = True  # pyright: ignore[reportFunctionMemberAccess]
    return func


class FactsGeneratorProtocol(AvdFactsProtocol, Protocol):
    """
    Protocol for the FactsGenerator base class for facts generators.

    This differs from AvdFacts by also taking facts as argument
    and the render_facts function which updates self.facts instead of
    returning a dict.
    """

    facts: EosDesignsFacts

    def render_facts(self) -> None:
        """
        Execute all class methods marked with @facts_contributor decorator.

        Each method will in-place update self.facts.
        """
        for method in self.facts_methods():
            method(self)

    @classmethod
    def facts_methods(cls) -> list[Callable[[Self], None]]:
        """Return the list of methods decorated with 'facts_contributor'."""
        return [method for key in cls._keys() if getattr(method := getattr(cls, key), "_is_facts_contributor", False)]


class FactsGenerator(AvdFacts, FactsGeneratorProtocol):
    """
    Base class for facts generators.

    This differs from AvdFacts by also taking facts as argument
    and the render_facts function which updates self.facts instead of
    returning a dict.
    """

    def __init__(
        self,
        hostvars: Mapping,
        inputs: EosDesigns,
        facts: EosDesignsFacts,
        shared_utils: SharedUtilsProtocol,
    ) -> None:
        self.facts = facts
        super().__init__(hostvars=hostvars, inputs=inputs, shared_utils=shared_utils)
