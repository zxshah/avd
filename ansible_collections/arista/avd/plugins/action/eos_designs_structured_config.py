# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.

import cProfile
import json
import logging
import pstats
from collections import ChainMap, defaultdict
from pathlib import Path
from typing import Any

import yaml
from ansible.errors import AnsibleActionFail
from ansible.parsing.yaml.dumper import AnsibleDumper
from ansible.plugins.action import ActionBase, display

from ansible_collections.arista.avd.plugins.plugin_utils.pyavd_wrappers import RaiseOnUse
from ansible_collections.arista.avd.plugins.plugin_utils.schema.avdschematools import AvdSchemaTools
from ansible_collections.arista.avd.plugins.plugin_utils.utils import get_templar, get_tmp_path, write_file
from pyavd._eos_designs.eos_designs_facts.schema import EosDesignsFacts
from pyavd._eos_designs.schema import EosDesigns

PLUGIN_NAME = "arista.avd.eos_designs_structured_config"
try:
    from pyavd._eos_designs.structured_config import get_structured_config
    from pyavd._utils import merge, strip_null_from_data
    from pyavd._utils import template as templater
except ImportError as e:
    get_structured_config = get = merge = RaiseOnUse(
        AnsibleActionFail(
            f"The '{PLUGIN_NAME}' plugin requires the 'pyavd' Python library. Got import error",
            orig_exc=e,
        ),
    )

LOGGER = logging.getLogger()


class ActionModule(ActionBase):
    def run(self, tmp: Any = None, task_vars: dict | None = None) -> dict:
        if task_vars is None:
            task_vars = {}

        result = super().run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        cprofile_file = self._task.args.get("cprofile_file")
        if cprofile_file:
            profiler = cProfile.Profile()
            profiler.enable()

        tmp_path = get_tmp_path()
        LOGGER.info("eos_designs_structured_config: Using %s for temporary files.", tmp_path)

        hostname = task_vars["inventory_hostname"]

        if self._task.args.get("debug_vars") is True and (debug_vars_file := self._task.args.get("debug_vars_file")):
            # Dump all hostvars to a file.
            write_file(yaml.dump(task_vars["hostvars"][hostname], Dumper=AnsibleDumper, indent=2, sort_keys=False, width=2147483647), debug_vars_file)

        if self._task.args.get("structured_config") is False:
            # Not creating structured config
            return result

        eos_designs_custom_templates = self._task.args.get("eos_designs_custom_templates", [])
        filename = str(self._task.args.get("dest", ""))
        file_mode = str(self._task.args.get("mode", "0o664"))
        template_output = self._task.args.get("template_output", False)
        validation_mode = self._task.args.get("validation_mode")

        groups = task_vars.get("groups", {})
        fabric_name = self._templar.template(task_vars.get("fabric_name", ""))
        fabric_hosts = groups.get(fabric_name, [])

        # Initialise defaultdict that loads facts from json files on demand.
        all_facts = AvdSwitchFactsDefaultDict(tmp_path, fabric_hosts)

        # Load validated and coerced inputs from json file.
        host_inputs = EosDesigns._from_dumped_dict(read_json_file(tmp_path / "device_inputs" / f"{hostname}.json", f"AVD device inputs for {hostname}"))

        # TODO: AVD 6.0.0 remove 'switch'
        task_vars["switch"] = all_facts[hostname]

        # Read ansible variables and perform templating to support inline jinja2
        for var in task_vars:
            if str(var).startswith(("ansible", "molecule", "hostvars", "vars")):
                continue
            if self._templar.is_template(task_vars[var]):
                # Var contains a jinja2 template.
                try:
                    task_vars[var] = self._templar.template(task_vars[var], fail_on_undefined=False)
                except Exception as e:
                    msg = f"Exception during templating of task_var '{var}'"
                    raise AnsibleActionFail(msg) from e

        # Get updated templar instance to be passed along to our simplified "templater"
        self.templar = get_templar(self, task_vars)

        # Get Structured Config from modules in PyAVD using internal api so we can supply our own templar
        try:
            output = get_structured_config(hostname=hostname, all_facts=all_facts, hostvars=task_vars, inputs=host_inputs, templar=self.templar)._as_dict()
        except Exception as error:
            raise AnsibleActionFail(message=str(error)) from error

        # We use ChainMap to avoid copying large amounts of data around, mapping in
        #  - output (containing structured_config at this point)
        #  - templated, converted and validated version of all other vars
        # Any var assignments will end up in output, so all other objects are protected.
        template_vars = ChainMap(output, task_vars)

        # eos_designs_custom_templates can contain a list of jinja templates to run after PyAVD
        if eos_designs_custom_templates:
            # Load schema tools for output schema
            output_schema_tools = AvdSchemaTools(
                hostname=hostname,
                ansible_display=display,
                schema_id="eos_cli_config_gen",
                validation_mode=validation_mode,
                plugin_name="arista.avd.eos_cli_config_gen",
            )

            for template_item in eos_designs_custom_templates:
                template_options = template_item.get("options", {})
                list_merge = template_options.get("list_merge", "append_rp")
                strip_empty_keys = template_options.get("strip_empty_keys", True)
                template = template_item["template"]

                # Here we parse the template, expecting the result to be a YAML formatted string
                template_result = templater(template, template_vars, self.templar)

                # Load data from the template result.
                template_result_data = yaml.safe_load(template_result)

                # If the argument 'strip_empty_keys' is set, remove keys with value of null / None from the resulting dict (recursively).
                if strip_empty_keys:
                    template_result_data = strip_null_from_data(template_result_data)

                if not template_result_data:
                    continue

                # If there is any data produced by the template, convert and merge it on top of previous output.
                # Some templates return a list of dicts, others only return a dict. Here we normalize to list.
                if not isinstance(template_result_data, list):
                    template_result_data = [template_result_data]

                try:
                    merge(output, *template_result_data, list_merge=list_merge, schema=output_schema_tools.avdschema)
                except Exception as error:
                    raise AnsibleActionFail(message=str(error)) from error

        # If the argument 'template_output' is set, run the output data through another jinja2 rendering.
        # This is to resolve any input values with inline jinja using variables/facts set by the input templates.
        if template_output:
            with self._templar.set_temporary_context(available_variables=template_vars):
                output = self._templar.template(output, fail_on_undefined=False)

        # If the argument 'dest' (filename) is set, write the output data to a file.
        if filename:
            # Depending on the file suffix of 'filename' (default: 'json') we will format the data to yaml or just write the output data directly.
            if filename.endswith((".yml", ".yaml")):
                result["changed"] = write_file(
                    content=yaml.dump(output, Dumper=AnsibleDumper, indent=2, sort_keys=False, width=130),
                    filename=filename,
                    file_mode=file_mode,
                )
            else:
                result["changed"] = write_file(
                    content=json.dumps(output),
                    filename=filename,
                    file_mode=file_mode,
                )

        # If 'dest' (filename) is not set, hardcode 'changed' to true, since we don't know if something changed and later tasks may depend on this.
        else:
            result["changed"] = True

        # TODO: AVD 6.0.0 consider not setting facts at all.
        result["ansible_facts"] = output
        # TODO: AVD 6.0.0 remove 'switch'
        result["ansible_facts"]["switch"] = task_vars.get("switch")

        if cprofile_file:
            profiler.disable()
            stats = pstats.Stats(profiler).sort_stats("cumtime")
            stats.dump_stats(cprofile_file)

        return result


def read_json_file(file: Path, file_context: str) -> dict:
    try:
        with file.open("r") as stream:
            data = json.load(stream)
            if not isinstance(data, dict):
                msg = f"Expected a 'dict' when reading data from {file_context}. Got {type(data)}."
            return data
    except OSError as e:
        msg = f"Unable to read {file_context}: {e}"
        raise type(e)(msg) from e
    except json.JSONDecodeError as e:
        msg = f"Unable to decode {file_context}: {e}"
        raise type(e)(msg, e.doc, e.pos) from e


class AvdSwitchFactsDefaultDict(defaultdict):
    tmp_path: Path

    def __init__(self, tmp_path: Path, fabric_hosts: list[str]) -> None:
        self.fabric_hosts = fabric_hosts
        self.tmp_path = tmp_path

    def __contains__(self, key: object) -> bool:
        try:
            _dummy = self[key]
        except (OSError, json.JSONDecodeError):
            return False
        return True

    def get(self, key: str, default: Any = None) -> dict:
        try:
            return self[key]
        except (OSError, json.JSONDecodeError):
            return default

    def __missing__(self, key: str) -> dict:
        LOGGER.debug("Loading facts for %s", key)
        self[key] = EosDesignsFacts._from_dict(read_json_file(self.tmp_path / "device_facts" / f"{key}.json", f"AVD device facts for {key}"))
        return self[key]

    def keys(self) -> list[str]:
        return self.fabric_hosts
