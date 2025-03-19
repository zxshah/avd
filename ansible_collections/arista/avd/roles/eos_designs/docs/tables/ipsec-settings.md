<!--
  ~ Copyright (c) 2025 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->
=== "Table"

    | Variable | Type | Required | Default | Value Restrictions | Description |
    | -------- | ---- | -------- | ------- | ------------------ | ----------- |
    | [<samp>ipsec_settings</samp>](## "ipsec_settings") | Dictionary |  |  |  | Settings applicable to all IPsec connections. |
    | [<samp>&nbsp;&nbsp;bind_connection_to_interface</samp>](## "ipsec_settings.bind_connection_to_interface") | Boolean |  | `False` |  | Allow IPsec connections to be bound to the source interface.<br>Enabling this prevents IPsec connections from using ECMP paths. |

=== "YAML"

    ```yaml
    # Settings applicable to all IPsec connections.
    ipsec_settings:

      # Allow IPsec connections to be bound to the source interface.
      # Enabling this prevents IPsec connections from using ECMP paths.
      bind_connection_to_interface: <bool; default=False>
    ```
