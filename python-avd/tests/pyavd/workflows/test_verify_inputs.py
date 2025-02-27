# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.


import logging
import re
from contextlib import nullcontext as does_not_raise

import pytest
from _pytest.python_api import RaisesContext

from pyavd._cv.client.exceptions import CVDuplicatedDevices
from pyavd._cv.workflows.models import CVDevice
from pyavd._cv.workflows.verify_inputs import verify_device_inputs

TWO_DUPED_SERIAL_PATTERNS = [
    "\\('Duplicated devices found in inventory.*"
    "\\[\\{'duplicated_serial_number': 'serial1', 'devices_with_duplicated_serial_number': "
    "\\[CVDevice\\(hostname='switch1'.*serial_number='serial1'.*"
    "CVDevice\\(hostname='switch2'.*serial_number='serial1'.*"
    "\\{'duplicated_serial_number': 'serial3', 'devices_with_duplicated_serial_number': "
    "\\[CVDevice\\(hostname='switch3'.*serial_number='serial3'.*"
    "CVDevice\\(hostname='switch4', serial_number='serial3'.*",
]

NO_DUPS_DEVICES = [
    CVDevice(hostname="switch1", serial_number="serial1", system_mac_address="aa:bb:cc:dd:ee:f1"),
    CVDevice(hostname="switch2", serial_number="serial2", system_mac_address="aa:bb:cc:dd:ee:f2"),
    CVDevice(hostname="switch3", serial_number="serial3", system_mac_address="aa:bb:cc:dd:ee:f3"),
    CVDevice(hostname="switch4", serial_number="serial4", system_mac_address="aa:bb:cc:dd:ee:f4"),
    CVDevice(hostname="switch5", serial_number="serial5", system_mac_address="aa:bb:cc:dd:ee:f5"),
    CVDevice(hostname="switch6", serial_number="serial6", system_mac_address="aa:bb:cc:dd:ee:f6"),
    CVDevice(hostname="switch7", serial_number="serial7"),
    CVDevice(hostname="switch8", serial_number="serial8"),
    CVDevice(hostname="switch9", system_mac_address="aa:bb:cc:dd:ee:f9"),
    CVDevice(hostname="switch10", system_mac_address="aa:bb:cc:dd:ee:f0"),
    CVDevice(hostname="switch11"),
    CVDevice(hostname="switch12"),
]

TWO_DUPED_SERIAL_DEVICES = [
    CVDevice(hostname="switch1", serial_number="serial1", system_mac_address="aa:bb:cc:dd:ee:f1"),
    CVDevice(hostname="switch2", serial_number="serial1", system_mac_address="aa:bb:cc:dd:ee:f2"),
    CVDevice(hostname="switch3", serial_number="serial3"),
    CVDevice(hostname="switch4", serial_number="serial3"),
    CVDevice(hostname="switch5", serial_number="serial5", system_mac_address="aa:bb:cc:dd:ee:f5"),
    CVDevice(hostname="switch6", serial_number="serial6", system_mac_address="aa:bb:cc:dd:ee:f6"),
    CVDevice(hostname="switch7", serial_number="serial7"),
    CVDevice(hostname="switch8", serial_number="serial8"),
    CVDevice(hostname="switch9", system_mac_address="aa:bb:cc:dd:ee:f9"),
    CVDevice(hostname="switch10", system_mac_address="aa:bb:cc:dd:ee:f0"),
    CVDevice(hostname="switch11"),
    CVDevice(hostname="switch12"),
]

TWO_DUPED_SYS_MAC_DEVICES = [
    CVDevice(hostname="switch1", system_mac_address="aa:bb:cc:dd:ee:f1"),
    CVDevice(hostname="switch2", system_mac_address="aa:bb:cc:dd:ee:f1"),
    CVDevice(hostname="switch3", serial_number="serial3", system_mac_address="aa:bb:cc:dd:ee:f3"),
    CVDevice(hostname="switch4", serial_number="serial4", system_mac_address="aa:bb:cc:dd:ee:f3"),
    CVDevice(hostname="switch5", serial_number="serial5", system_mac_address="aa:bb:cc:dd:ee:f5"),
    CVDevice(hostname="switch6", serial_number="serial6", system_mac_address="aa:bb:cc:dd:ee:f6"),
    CVDevice(hostname="switch7", serial_number="serial7"),
    CVDevice(hostname="switch8", serial_number="serial8"),
    CVDevice(hostname="switch9", system_mac_address="aa:bb:cc:dd:ee:f9"),
    CVDevice(hostname="switch10", system_mac_address="aa:bb:cc:dd:ee:f0"),
    CVDevice(hostname="switch11"),
    CVDevice(hostname="switch12"),
]

TWO_DUPED_SYS_MAC_UNIQ_SER_DEVICES = [
    CVDevice(hostname="switch1", system_mac_address="aa:bb:cc:dd:ee:f1"),
    CVDevice(hostname="switch2", system_mac_address="aa:bb:cc:dd:ee:f2"),
    CVDevice(hostname="switch3", serial_number="serial3", system_mac_address="aa:bb:cc:dd:ee:f3"),
    CVDevice(hostname="switch4", serial_number="serial4", system_mac_address="aa:bb:cc:dd:ee:f3"),
    CVDevice(hostname="switch5", serial_number="serial5", system_mac_address="aa:bb:cc:dd:ee:f5"),
    CVDevice(hostname="switch6", serial_number="serial6", system_mac_address="aa:bb:cc:dd:ee:f5"),
    CVDevice(hostname="switch7", serial_number="serial7"),
    CVDevice(hostname="switch8", serial_number="serial8"),
    CVDevice(hostname="switch9", system_mac_address="aa:bb:cc:dd:ee:f9"),
    CVDevice(hostname="switch10", system_mac_address="aa:bb:cc:dd:ee:f0"),
    CVDevice(hostname="switch11"),
    CVDevice(hostname="switch12"),
]

ONE_DUPED_SERIAL_ONE_DUPED_SYS_MAC_DEVICES = [
    CVDevice(hostname="switch1", serial_number="serial1", system_mac_address="aa:bb:cc:dd:ee:f1"),
    CVDevice(hostname="switch2", serial_number="serial1", system_mac_address="aa:bb:cc:dd:ee:f2"),
    CVDevice(hostname="switch3", serial_number="serial3", system_mac_address="aa:bb:cc:dd:ee:f3"),
    CVDevice(hostname="switch4", serial_number="serial4", system_mac_address="aa:bb:cc:dd:ee:f3"),
    CVDevice(hostname="switch5", serial_number="serial5", system_mac_address="aa:bb:cc:dd:ee:f5"),
    CVDevice(hostname="switch6", serial_number="serial6", system_mac_address="aa:bb:cc:dd:ee:f6"),
    CVDevice(hostname="switch7", serial_number="serial7"),
    CVDevice(hostname="switch8", serial_number="serial8"),
    CVDevice(hostname="switch9", system_mac_address="aa:bb:cc:dd:ee:f9"),
    CVDevice(hostname="switch10", system_mac_address="aa:bb:cc:dd:ee:f0"),
    CVDevice(hostname="switch11"),
    CVDevice(hostname="switch12"),
]

ONE_DUPED_SERIAL_ONE_DUPED_SYS_MAC_SAME_DEVICES_DEVICES = [
    CVDevice(hostname="switch1", serial_number="serial1", system_mac_address="aa:bb:cc:dd:ee:f1"),
    CVDevice(hostname="switch2", serial_number="serial1", system_mac_address="aa:bb:cc:dd:ee:f1"),
    CVDevice(hostname="switch3", serial_number="serial3", system_mac_address="aa:bb:cc:dd:ee:f3"),
    CVDevice(hostname="switch4", serial_number="serial4", system_mac_address="aa:bb:cc:dd:ee:f4"),
    CVDevice(hostname="switch5", serial_number="serial5", system_mac_address="aa:bb:cc:dd:ee:f5"),
    CVDevice(hostname="switch6", serial_number="serial6", system_mac_address="aa:bb:cc:dd:ee:f6"),
    CVDevice(hostname="switch7", serial_number="serial7"),
    CVDevice(hostname="switch8", serial_number="serial8"),
    CVDevice(hostname="switch9", system_mac_address="aa:bb:cc:dd:ee:f9"),
    CVDevice(hostname="switch10", system_mac_address="aa:bb:cc:dd:ee:f0"),
    CVDevice(hostname="switch11"),
    CVDevice(hostname="switch12"),
]


@pytest.mark.parametrize(
    (
        "devices",
        "strict_system_mac_address",
        "warnings_qty",
        "expected_warning_patterns",
        "logs_qty",
        "expected_logs_patterns",
        "expected_exception_patterns",
        "expected_exception",
    ),
    [
        pytest.param(
            NO_DUPS_DEVICES,
            # strict_system_mac_address
            False,
            # Warnings
            0,
            [],
            # Logs
            0,
            [],
            # Exceptions
            [],
            does_not_raise(),
            id="NO_DUPS_STRICT_MAC_FALSE",
        ),
        pytest.param(
            NO_DUPS_DEVICES,
            # strict_system_mac_address
            True,
            # Warnings
            0,
            [],
            # Logs
            0,
            [],
            # Exceptions
            [],
            does_not_raise(),
            id="NO_DUPS_STRICT_MAC_TRUE",
        ),
        pytest.param(
            TWO_DUPED_SERIAL_DEVICES,
            # strict_system_mac_address
            False,
            # Warnings
            0,
            [],
            # Logs
            0,
            [],
            # Exceptions
            TWO_DUPED_SERIAL_PATTERNS,
            pytest.raises(CVDuplicatedDevices),
            id="TWO_DUPED_SERIAL_STRICT_MAC_FALSE",
        ),
        pytest.param(
            TWO_DUPED_SERIAL_DEVICES,
            # strict_system_mac_address
            True,
            # Warnings
            0,
            [],
            # Logs
            0,
            [],
            # Exception
            TWO_DUPED_SERIAL_PATTERNS,
            pytest.raises(CVDuplicatedDevices),
            id="TWO_DUPED_SERIAL_STRICT_MAC_TRUE",
        ),
        pytest.param(
            TWO_DUPED_SYS_MAC_DEVICES,
            # strict_system_mac_address
            False,
            # Warnings
            0,
            [],
            # Logs
            0,
            [],
            # Exceptions
            [
                "\\('Duplicated devices found in inventory.*"
                "\\[\\{'duplicated_system_mac_address': 'aa:bb:cc:dd:ee:f1', 'devices_with_duplicated_system_mac_address': "
                "\\[CVDevice\\(hostname='switch1'.*system_mac_address='aa:bb:cc:dd:ee:f1'.*"
                "CVDevice\\(hostname='switch2'.*system_mac_address='aa:bb:cc:dd:ee:f1'.*",
            ],
            pytest.raises(CVDuplicatedDevices),
            id="TWO_DUPED_SYS_MAC_STRICT_MAC_FALSE",
        ),
        pytest.param(
            TWO_DUPED_SYS_MAC_DEVICES,
            # strict_system_mac_address
            True,
            # Warnings
            0,
            [],
            # Logs
            0,
            [],
            # Exception
            [
                "\\('Duplicated devices found in inventory.*"
                "\\[\\{'duplicated_system_mac_address': 'aa:bb:cc:dd:ee:f1', 'devices_with_duplicated_system_mac_address': "
                "\\[CVDevice\\(hostname='switch1'.*system_mac_address='aa:bb:cc:dd:ee:f1'.*"
                "CVDevice\\(hostname='switch2'.*system_mac_address='aa:bb:cc:dd:ee:f1'.*"
                "\\{'duplicated_system_mac_address': 'aa:bb:cc:dd:ee:f3', 'devices_with_duplicated_system_mac_address': "
                "\\[CVDevice\\(hostname='switch3'.*system_mac_address='aa:bb:cc:dd:ee:f3'.*"
                "CVDevice\\(hostname='switch4'.*system_mac_address='aa:bb:cc:dd:ee:f3'.*",
            ],
            pytest.raises(CVDuplicatedDevices),
            id="TWO_DUPED_SYS_MAC_STRICT_MAC_TRUE",
        ),
        pytest.param(
            TWO_DUPED_SYS_MAC_UNIQ_SER_DEVICES,
            # strict_system_mac_address
            False,
            # Warnings
            1,
            [
                "\\('Duplicated devices found in inventory.*"
                "\\[\\{'duplicated_system_mac_address': 'aa:bb:cc:dd:ee:f3', 'devices_with_duplicated_system_mac_address': "
                "\\[CVDevice\\(hostname='switch3'.*system_mac_address='aa:bb:cc:dd:ee:f3'.*"
                "CVDevice\\(hostname='switch4'.*system_mac_address='aa:bb:cc:dd:ee:f3'.*"
                "\\{'duplicated_system_mac_address': 'aa:bb:cc:dd:ee:f5', 'devices_with_duplicated_system_mac_address': "
                "\\[CVDevice\\(hostname='switch5'.*system_mac_address='aa:bb:cc:dd:ee:f5'.*"
                "CVDevice\\(hostname='switch6'.*system_mac_address='aa:bb:cc:dd:ee:f5'.*",
            ],
            # Logs
            1,
            [
                "verify_inputs: Devices with duplicated system_mac_address and unique serial_number discovered in inventory \\(structured config\\): "
                "\\[\\{'duplicated_system_mac_address': 'aa:bb:cc:dd:ee:f3', 'devices_with_duplicated_system_mac_address': "
                "\\[CVDevice\\(hostname='switch3'.*serial_number='serial3'.*system_mac_address='aa:bb:cc:dd:ee:f3'.*"
                "CVDevice\\(hostname='switch4'.*serial_number='serial4'.*system_mac_address='aa:bb:cc:dd:ee:f3'.*"
                "\\{'duplicated_system_mac_address': 'aa:bb:cc:dd:ee:f5', 'devices_with_duplicated_system_mac_address': "
                "\\[CVDevice\\(hostname='switch5'.*serial_number='serial5'.*system_mac_address='aa:bb:cc:dd:ee:f5'.*"
                "CVDevice\\(hostname='switch6'.*serial_number='serial6'.*system_mac_address='aa:bb:cc:dd:ee:f5.*",
            ],
            # Exceptions
            [],
            does_not_raise(),
            id="TWO_DUPED_SYS_MAC_UNIQ_SER_STRICT_MAC_FALSE",
        ),
        pytest.param(
            TWO_DUPED_SYS_MAC_UNIQ_SER_DEVICES,
            # strict_system_mac_address
            True,
            # Warnings
            0,
            [],
            # Logs
            0,
            [],
            # Exceptions
            [
                "\\('Duplicated devices found in inventory.*"
                "\\[\\{'duplicated_system_mac_address': 'aa:bb:cc:dd:ee:f3', 'devices_with_duplicated_system_mac_address': "
                "\\[CVDevice\\(hostname='switch3'.*system_mac_address='aa:bb:cc:dd:ee:f3'.*"
                "CVDevice\\(hostname='switch4'.*system_mac_address='aa:bb:cc:dd:ee:f3'.*"
                "\\{'duplicated_system_mac_address': 'aa:bb:cc:dd:ee:f5', 'devices_with_duplicated_system_mac_address': "
                "\\[CVDevice\\(hostname='switch5'.*system_mac_address='aa:bb:cc:dd:ee:f5'.*"
                "CVDevice\\(hostname='switch6'.*system_mac_address='aa:bb:cc:dd:ee:f5'.*",
            ],
            pytest.raises(CVDuplicatedDevices),
            id="TWO_DUPED_SYS_MAC_UNIQ_SER_STRICT_MAC_TRUE",
        ),
        pytest.param(
            ONE_DUPED_SERIAL_ONE_DUPED_SYS_MAC_DEVICES,
            # strict_system_mac_address
            False,
            # Warnings
            0,
            [],
            # Logs
            0,
            [],
            # Exceptions
            [
                "\\('Duplicated devices found in inventory.*"
                "\\[\\{'duplicated_serial_number': 'serial1', 'devices_with_duplicated_serial_number':.*"
                "\\[CVDevice\\(hostname='switch1'.*serial_number='serial1'.*"
                "CVDevice\\(hostname='switch2'.*serial_number='serial1'.*",
            ],
            pytest.raises(CVDuplicatedDevices),
            id="ONE_DUPED_SERIAL_ONE_DUPED_SYS_MAC_STRICT_MAC_FALSE",
        ),
        pytest.param(
            ONE_DUPED_SERIAL_ONE_DUPED_SYS_MAC_DEVICES,
            # strict_system_mac_address
            True,
            # Warnings
            0,
            [],
            # Logs
            0,
            [],
            # Exceptions
            [
                "\\('Duplicated devices found in inventory.*"
                "\\[\\{'duplicated_serial_number': 'serial1', 'devices_with_duplicated_serial_number':.*"
                "\\[CVDevice\\(hostname='switch1'.*serial_number='serial1'.*"
                "CVDevice\\(hostname='switch2'.*serial_number='serial1'.*"
                "\\{'duplicated_system_mac_address': 'aa:bb:cc:dd:ee:f3', 'devices_with_duplicated_system_mac_address':.*"
                "\\[CVDevice\\(hostname='switch3'.*system_mac_address='aa:bb:cc:dd:ee:f3'.*"
                "CVDevice\\(hostname='switch4'.*system_mac_address='aa:bb:cc:dd:ee:f3'.*",
            ],
            pytest.raises(CVDuplicatedDevices),
            id="ONE_DUPED_SERIAL_ONE_DUPED_SYS_MAC_STRICT_MAC_TRUE",
        ),
        pytest.param(
            ONE_DUPED_SERIAL_ONE_DUPED_SYS_MAC_SAME_DEVICES_DEVICES,
            # strict_system_mac_address
            False,
            # Warnings
            0,
            [],
            # Logs
            0,
            [],
            # Exception
            [
                "\\('Duplicated devices found in inventory.*"
                "\\[\\{'duplicated_serial_number': 'serial1', 'devices_with_duplicated_serial_number':.*"
                "\\[CVDevice\\(hostname='switch1'.*serial_number='serial1'.*system_mac_address='aa:bb:cc:dd:ee:f1'.*"
                "CVDevice\\(hostname='switch2'.*serial_number='serial1'.*system_mac_address='aa:bb:cc:dd:ee:f1'.*",
            ],
            pytest.raises(CVDuplicatedDevices),
            id="ONE_DUPED_SERIAL_ONE_DUPED_SYS_MAC_SAME_DEVICES_STRICT_MAC_FALSE",
        ),
        pytest.param(
            ONE_DUPED_SERIAL_ONE_DUPED_SYS_MAC_SAME_DEVICES_DEVICES,
            # strict_system_mac_address
            True,
            # Warnings
            0,
            [],
            # Logs
            0,
            [],
            # Exception
            [
                "\\('Duplicated devices found in inventory.*"
                "\\[\\{'duplicated_serial_number': 'serial1', 'devices_with_duplicated_serial_number':.*"
                "\\[CVDevice\\(hostname='switch1'.*serial_number='serial1'.*system_mac_address='aa:bb:cc:dd:ee:f1'.*"
                "CVDevice\\(hostname='switch2'.*serial_number='serial1'.*system_mac_address='aa:bb:cc:dd:ee:f1'.*"
                "\\{'duplicated_system_mac_address': 'aa:bb:cc:dd:ee:f1', 'devices_with_duplicated_system_mac_address':.*"
                "\\[CVDevice\\(hostname='switch1'.*serial_number='serial1'.*system_mac_address='aa:bb:cc:dd:ee:f1'.*"
                "CVDevice\\(hostname='switch2'.*serial_number='serial1'.*system_mac_address='aa:bb:cc:dd:ee:f1'.*",
            ],
            pytest.raises(CVDuplicatedDevices),
            id="ONE_DUPED_SERIAL_ONE_DUPED_SYS_MAC_SAME_DEVICES_STRICT_MAC_TRUE",
        ),
    ],
)
def test_verify_device_inputs(
    *,
    caplog: pytest.LogCaptureFixture,
    devices: list[CVDevice],
    strict_system_mac_address: bool,
    warnings: list[Exception] | None = None,
    warnings_qty: int,
    expected_warning_patterns: list[str],
    logs_qty: int,
    expected_logs_patterns: list[str],
    expected_exception_patterns: list[str],
    expected_exception: RaisesContext | does_not_raise,
) -> None:
    # Create an empty list for warnings
    warnings = []
    with caplog.at_level(logging.DEBUG), expected_exception as exc_info:
        # Engage FUT
        verify_device_inputs(devices=devices, strict_system_mac_address=strict_system_mac_address, warnings=warnings)
    # Assert number of returned warnings
    assert len(warnings) == warnings_qty
    # Assert that updated warnings match expected warning patterns
    for expected_pattern in expected_warning_patterns:
        assert any(re.search(re.compile(expected_pattern), str(warning_item.args)) for warning_item in warnings)
    # Assert number of log messages
    assert len(caplog.records) == logs_qty
    # Assert that log messages match expected log patterns
    for expected_pattern in expected_logs_patterns:
        assert any(re.search(re.compile(expected_pattern), str(record.message)) for record in caplog.records)
    # If exception is raised, assert that exception value contains all expected exception patterns
    if exc_info and (exception_string := str(exc_info.value)):
        for expected_pattern in expected_exception_patterns:
            assert re.search(re.compile(expected_pattern), exception_string)
