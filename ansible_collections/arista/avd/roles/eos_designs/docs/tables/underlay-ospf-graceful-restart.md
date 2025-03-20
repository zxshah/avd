<!--
  ~ Copyright (c) 2025 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->
=== "Table"

    | Variable | Type | Required | Default | Value Restrictions | Description |
    | -------- | ---- | -------- | ------- | ------------------ | ----------- |
    | [<samp>underlay_ospf_graceful_restart</samp>](## "underlay_ospf_graceful_restart") | Boolean |  | `False` |  | Set graceful restart when the underlay_routing_protocol is OSPF. |

=== "YAML"

    ```yaml
    # Set graceful restart when the underlay_routing_protocol is OSPF.
    underlay_ospf_graceful_restart: <bool; default=False>
    ```
