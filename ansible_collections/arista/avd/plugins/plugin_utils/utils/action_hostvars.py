# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import TYPE_CHECKING

from ansible.vars.hostvars import HostVarsVars

if TYPE_CHECKING:
    from ansible.inventory.manager import InventoryManager
    from ansible.parsing.dataloader import DataLoader
    from ansible.playbook.play import Play
    from ansible.playbook.task import Task
    from ansible.plugins.action import ActionBase
    from ansible.vars.manager import VariableManager


class ActionHostVars(Mapping):
    """Ansible HostVars replacement that respects action plugin context for variable precedence."""

    def __init__(self, action_plugin: ActionBase) -> None:
        """Initialize with an Ansible action plugin instance."""
        self.action_plugin: ActionBase = action_plugin
        self.task: Task = action_plugin._task
        self.play: Play = self.task.get_play()
        self.loader: DataLoader = self.task.get_loader()
        self.variable_manager: VariableManager = self.task.get_variable_manager()
        self.inventory: InventoryManager = self.variable_manager._inventory
        self._cache = {}

    def __getitem__(self, hostname: str) -> HostVarsVars:
        """Get variables for a host with template processing."""
        variables = self.get_host_variables(hostname)
        return HostVarsVars(variables=variables, loader=self.loader)

    def get_host_variables(self, hostname: str) -> dict:
        """Get raw variables for a specific host with proper context."""
        if hostname in self._cache:
            return self._cache[hostname]

        host = self.inventory.get_host(hostname)
        if host is None:
            msg = f"Host '{hostname}' not found in Ansible inventory"
            raise KeyError(msg)

        variables = self.variable_manager.get_vars(
            play=self.play,
            host=host,
            task=self.task,
            include_hostvars=False,
        )

        self._cache[hostname] = variables
        return variables

    def __contains__(self, hostname: str) -> bool:
        """Check if a hostname exists in the inventory."""
        return self.inventory.get_host(hostname) is not None

    def __iter__(self) -> Iterator[str]:
        """Iterate over all hostnames in the inventory."""
        yield from self.inventory.hosts

    def __len__(self) -> int:
        """Return the number of hosts in the inventory."""
        return len(self.inventory.hosts)

    def get_subset(self, hostnames: list[str], variables: list[str] | None = None) -> dict:
        """Get a dictionary of {hostname: {var: value}} for specified hosts and vars."""
        result = {}

        for hostname in hostnames:
            host_hostvars = self[hostname]

            if variables:
                # Filter to just the requested variables
                result[hostname] = {var: host_hostvars.get(var) for var in variables}
            else:
                result[hostname] = dict(host_hostvars)

        return result
