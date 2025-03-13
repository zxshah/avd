<!--
  ~ Copyright (c) 2025 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->
=== "Table"

    | Variable | Type | Required | Default | Value Restrictions | Description |
    | -------- | ---- | -------- | ------- | ------------------ | ----------- |
    | [<samp>only_used_for_peer_facts</samp>](## "only_used_for_peer_facts") | Dictionary |  |  |  |  |
    | [<samp>&nbsp;&nbsp;uplink_type</samp>](## "only_used_for_peer_facts.uplink_type") | String |  |  | Valid Values:<br>- <code>p2p</code><br>- <code>port-channel</code><br>- <code>p2p-vrfs</code><br>- <code>lan</code> | Override the default `uplink_type` set at the `node_type_key` level.<br>`uplink_type` must be "p2p" if `vtep` or `underlay_router` is true for the `node_type_key` definition. |

=== "YAML"

    ```yaml
    only_used_for_peer_facts:

      # Override the default `uplink_type` set at the `node_type_key` level.
      # `uplink_type` must be "p2p" if `vtep` or `underlay_router` is true for the `node_type_key` definition.
      uplink_type: <str; "p2p" | "port-channel" | "p2p-vrfs" | "lan">
    ```
