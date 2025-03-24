<!--
  ~ Copyright (c) 2025 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->
=== "Table"

    | Variable | Type | Required | Default | Value Restrictions | Description |
    | -------- | ---- | -------- | ------- | ------------------ | ----------- |
    | [<samp>serial_number</samp>](## "serial_number") | String |  |  |  | Serial Number of the device.<br>Used only for documentation and deployment purposes. It is used by the 'eos_config_deploy_cvp' and 'cv_deploy' roles. |

=== "YAML"

    ```yaml
    # Serial Number of the device.
    # Used only for documentation and deployment purposes. It is used by the 'eos_config_deploy_cvp' and 'cv_deploy' roles.
    serial_number: <str>
    ```
