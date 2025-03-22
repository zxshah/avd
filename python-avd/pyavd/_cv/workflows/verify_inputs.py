# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from collections import defaultdict
from itertools import chain
from logging import getLogger
from typing import TYPE_CHECKING

from pyavd._cv.client.exceptions import CVDuplicatedDevices
from pyavd._utils import groupby_obj

if TYPE_CHECKING:
    from .models import CVDevice

LOGGER = getLogger(__name__)


def verify_device_inputs(*, devices: list[CVDevice], strict_system_mac_address: bool, warnings: list[Exception]) -> None:
    """
    Verify device inputs from structured config files.

    Check for presence of the duplicated `serial_number` or `system_mac_address` values.
    Raise an exception and terminate execution if:
      - two or more devices have the same `serial_number` (values of `system_mac_address` are not important in this case)
      - two or more devices have the same `system_mac_address` and have `serial_number` values unset
      - two or more targeted devices have the same `system_mac_address`, unique `serial_number` and `strict_system_mac_address` is `True`
    Warn user (with log message and updated `cv_deploy_results.warnings`) if:
      - two or more targeted devices have the same `system_mac_address`, unique `serial_number` and `strict_system_mac_address` is `False`
    """
    duplicated_serial_number, duplicated_system_mac_address_unset_serial_number, duplicated_system_mac_address_set_serial_number = identify_duplicated_devices(
        devices=devices
    )

    if duplicated_serial_number or duplicated_system_mac_address_unset_serial_number or duplicated_system_mac_address_set_serial_number:
        duplicated_devices_handler(
            duplicated_serial_number=duplicated_serial_number,
            duplicated_system_mac_address_unset_serial_number=duplicated_system_mac_address_unset_serial_number,
            duplicated_system_mac_address_set_serial_number=duplicated_system_mac_address_set_serial_number,
            strict_system_mac_address=strict_system_mac_address,
            warnings=warnings,
        )


def identify_duplicated_devices(
    *, devices: list[CVDevice]
) -> tuple[list[dict[str, str | list[CVDevice]]], list[dict[str, str | list[CVDevice]]], list[dict[str, str | list[CVDevice]]]]:
    """
    Process list of CVDevice instances to identify those with overlapping serial_number or system_mac_address.

    Return tuple containing:
      - List of dictionaries with information about CVDevices with overlapping serial_number.
      - List of dictionaries with information about CVDevices with overlapping system_mac_address and unset serial_number.
      - List of dictionaries with information about CVDevices with overlapping system_mac_address and set serial_number.
    """
    # List holding CVDevices with duplicated serial_number
    duplicated_serial_number: list[dict[str, str | list[CVDevice]]] = []
    # List holding CVDevices with duplicated system_mac_address and unset
    duplicated_system_mac_address_unset_serial_number: list[dict[str, str | list[CVDevice]]] = []
    # List holding CVDevices with duplicated system_mac_address
    duplicated_system_mac_address_set_serial_number: list[dict[str, str | list[CVDevice]]] = []

    # Deduplicate CVDevice objects as original `devices` list may contain duplicated items
    unique_devices = list({id(device): device for device in devices}.values())

    # Group devices based on <CVDevice>.serial_number as long as it's not None
    devices_grouped_by_serial_number = groupby_obj(
        list_of_objects=[device for device in unique_devices if device.serial_number is not None], attr="serial_number"
    )

    # Group devices based on <CVDevice>.system_mac_address as long as it's not None
    devices_grouped_by_system_mac_address = groupby_obj(
        list_of_objects=[device for device in unique_devices if device.system_mac_address is not None], attr="system_mac_address"
    )

    # Populate list of CVDevice with duplicated serial_number values
    for current_serial_number, device_iterator_object in devices_grouped_by_serial_number:
        if len(devices_with_current_serial_number := list(device_iterator_object)) > 1:
            duplicated_serial_number.append(
                {"duplicated_serial_number": current_serial_number, "devices_with_duplicated_serial_number": devices_with_current_serial_number}
            )

    # Populate list of CVDevice with duplicated system_mac_address values
    for current_system_mac_address, device_iterator_object in devices_grouped_by_system_mac_address:
        if len(devices_with_current_system_mac_address := list(device_iterator_object)) > 1:
            if devices_with_unset_serial_number := [device for device in devices_with_current_system_mac_address if device.serial_number is None]:
                duplicated_system_mac_address_unset_serial_number.append(
                    {
                        "duplicated_system_mac_address": current_system_mac_address,
                        "devices_with_duplicated_system_mac_address": devices_with_unset_serial_number,
                    }
                )
            if devices_with_set_serial_number := [device for device in devices_with_current_system_mac_address if device.serial_number is not None]:
                duplicated_system_mac_address_set_serial_number.append(
                    {
                        "duplicated_system_mac_address": current_system_mac_address,
                        "devices_with_duplicated_system_mac_address": devices_with_set_serial_number,
                    }
                )

    return duplicated_serial_number, duplicated_system_mac_address_unset_serial_number, duplicated_system_mac_address_set_serial_number


def identify_duplicated_devices_new(
    *, devices: list[CVDevice]
) -> tuple[list[dict[str, str | list[CVDevice]]], list[dict[str, str | list[CVDevice]]], list[dict[str, str | list[CVDevice]]]]:
    """
    Process list of CVDevice instances to identify those with overlapping serial_number or system_mac_address.

    Return tuple containing:
      - List of dictionaries with information about CVDevices with overlapping serial_number.
      - List of dictionaries with information about CVDevices with overlapping system_mac_address and unset serial_number.
      - List of dictionaries with information about CVDevices with overlapping system_mac_address and set serial_number.
    """
    devices_grouped_by_serial_number = defaultdict(lambda: defaultdict(list))
    devices_grouped_by_system_mac_address = defaultdict(lambda: defaultdict(list))
    for device in devices:
        devices_grouped_by_serial_number[device.serial_number][device.system_mac_address].append(device)
        devices_grouped_by_system_mac_address[device.system_mac_address][device.serial_number].append(device)

    duplicated_serial_number = []
    duplicated_system_mac_address_unset_serial_number = []
    duplicated_system_mac_address_set_serial_number = []
    for serial_number, data in devices_grouped_by_serial_number.items():
        # Duplicate serial_number
        duplicated_devices = list(chain.from_iterable(data.values()))
        if len(duplicated_devices) > 1 and serial_number:
            duplicated_serial_number.append(
                {
                    "duplicated_serial_number": serial_number,
                    "devices_with_duplicated_serial_number": duplicated_devices,
                }
            )

    for system_mac, data in devices_grouped_by_system_mac_address.items():
        if system_mac:
            duplicated_devices = list(chain.from_iterable(data.values()))
            if len(duplicated_devices) > 1:
                devices_with_set_serial_number = []
                for serial_number, current_devices in data.items():
                    if serial_number is None:
                        duplicated_system_mac_address_unset_serial_number.append(
                            {
                                "duplicated_system_mac_address": system_mac,
                                "devices_with_duplicated_system_mac_address": current_devices,
                            }
                        )
                    else:
                        devices_with_set_serial_number.extend(current_devices)
                if devices_with_set_serial_number:
                    duplicated_system_mac_address_set_serial_number.append(
                        {
                            "duplicated_system_mac_address": system_mac,
                            "devices_with_duplicated_system_mac_address": devices_with_set_serial_number,
                        }
                    )

    return duplicated_serial_number, duplicated_system_mac_address_unset_serial_number, duplicated_system_mac_address_set_serial_number


def duplicated_devices_handler(
    *,
    duplicated_serial_number: list[dict[str, str | list[CVDevice]]],
    duplicated_system_mac_address_unset_serial_number: list[dict[str, str | list[CVDevice]]],
    duplicated_system_mac_address_set_serial_number: list[dict[str, str | list[CVDevice]]],
    strict_system_mac_address: bool,
    warnings: list[Exception],
) -> None:
    """
    Handle input devices with duplicated `serial_number`s or `system_mac_address`es.

    Raise an exception if (match-any):
        - duplicated_serial_number is not empty
        - duplicated_system_mac_address_unset_serial_number is not empty
        - duplicated_system_mac_address_set_serial_number is not empty and strict_system_mac_address set to True
    Raise warning if (match-any):
        - duplicated_system_mac_address_set_serial_number is not empty and strict_system_mac_address set to False
    """
    if (
        duplicated_serial_number
        or duplicated_system_mac_address_unset_serial_number
        or (duplicated_system_mac_address_set_serial_number and strict_system_mac_address)
    ):
        exception = CVDuplicatedDevices(
            "Duplicated devices found in inventory",
            *[
                item
                for item in (
                    duplicated_serial_number,
                    duplicated_system_mac_address_unset_serial_number,
                    duplicated_system_mac_address_set_serial_number if strict_system_mac_address else None,
                )
                if item
            ],
        )
        raise exception

    LOGGER.warning(
        "verify_inputs: Devices with duplicated system_mac_address and unique serial_number discovered in inventory (structured config): %s",
        duplicated_system_mac_address_set_serial_number,
    )
    warnings.append(CVDuplicatedDevices("Duplicated devices found in inventory", duplicated_system_mac_address_set_serial_number))
