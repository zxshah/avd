# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

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
    # List holding CVDevices with duplicated serial_number
    duplicated_serial_number: list[dict[str, str | list[CVDevice]]] = []
    # List holding CVDevices with duplicated system_mac_address and unset
    duplicated_system_mac_address_unset_serial_number: list[dict[str, str | list[CVDevice]]] = []
    # List holding CVDevices with duplicated system_mac_address
    duplicated_system_mac_address_set_serial_number: list[dict[str, str | list[CVDevice]]] = []
    # Set object to track IDs of unique CVDevice objects
    unique_device_ids: set[str] = set()
    # List object to hold unique CVDevice objects from original `devices`
    unique_devices: list[CVDevice] = []

    # Deduplicate CVDevice objects as original `devices` list may contain duplicated items
    for device in devices:
        if (device_id := id(device)) not in unique_device_ids:
            unique_device_ids.add(device_id)
            unique_devices.append(device)

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

    if duplicated_serial_number or duplicated_system_mac_address_unset_serial_number or duplicated_system_mac_address_set_serial_number:
        warnings.append(
            duplicated_devices_handler(
                duplicated_serial_number=duplicated_serial_number,
                duplicated_system_mac_address_unset_serial_number=duplicated_system_mac_address_unset_serial_number,
                duplicated_system_mac_address_set_serial_number=duplicated_system_mac_address_set_serial_number,
                strict_system_mac_address=strict_system_mac_address,
            )
        )


def duplicated_devices_handler(
    *,
    duplicated_serial_number: list[dict[str, str | list[CVDevice]]],
    duplicated_system_mac_address_unset_serial_number: list[dict[str, str | list[CVDevice]]],
    duplicated_system_mac_address_set_serial_number: list[dict[str, str | list[CVDevice]]],
    strict_system_mac_address: bool,
) -> Exception:
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
    return CVDuplicatedDevices("Duplicated devices found in inventory", duplicated_system_mac_address_set_serial_number)
