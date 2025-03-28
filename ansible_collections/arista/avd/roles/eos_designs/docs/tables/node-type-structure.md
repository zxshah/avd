<!--
  ~ Copyright (c) 2025 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->
=== "Table"

    | Variable | Type | Required | Default | Value Restrictions | Description |
    | -------- | ---- | -------- | ------- | ------------------ | ----------- |
    | [<samp>&lt;node_type_keys.key&gt;</samp>](## "<node_type_keys.key>") | Dictionary |  |  |  |  |
    | [<samp>&nbsp;&nbsp;defaults</samp>](## "<node_type_keys.key>.defaults") | Dictionary |  |  |  | Define variables for all nodes of this type. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;mgmt_gateway</samp>](## "<node_type_keys.key>.defaults.mgmt_gateway") | String |  |  |  | This key sets the management gateway for the device. It takes precedence over the global `mgmt_gateway`. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;ipv6_mgmt_gateway</samp>](## "<node_type_keys.key>.defaults.ipv6_mgmt_gateway") | String |  |  |  | This key sets the ipv6 management gateway for the device. It takes precedence over the global `ipv6_mgmt_gateway`. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;flow_tracker_type</samp>](## "<node_type_keys.key>.defaults.flow_tracker_type") | String |  |  | Valid Values:<br>- <code>sampled</code><br>- <code>hardware</code> | Set the flow tracker type.<br>Override the `default_flow_tracker_type`` set at the `node_type_key` level.<br>`default_flow_tracker_type` default value is `sampled`. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;underlay_multicast</samp>](## "<node_type_keys.key>.defaults.underlay_multicast") | Dictionary |  |  |  |  |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;pim_sm</samp>](## "<node_type_keys.key>.defaults.underlay_multicast.pim_sm") | Dictionary |  |  |  |  |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;enabled</samp>](## "<node_type_keys.key>.defaults.underlay_multicast.pim_sm.enabled") | Boolean |  |  |  | Enable/Disable Protocol Independent Multicast sparse mode in the underlay on all p2p uplink interfaces, mlag l3 peer interface and core interfaces for the specific node. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;uplinks</samp>](## "<node_type_keys.key>.defaults.underlay_multicast.pim_sm.uplinks") | List, items: String |  |  |  | Enable/Disable Protocol Independent Multicast sparse mode in the underlay on specific p2p uplink interfaces. If not set, all uplinks will be enabled. Set as an empty list to remove all uplinks. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;&lt;str&gt;</samp>](## "<node_type_keys.key>.defaults.underlay_multicast.pim_sm.uplinks.[]") | String |  |  |  |  |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;mlag</samp>](## "<node_type_keys.key>.defaults.underlay_multicast.pim_sm.mlag") | Boolean |  |  |  | Enable/Disable Protocol Independent Multicast sparse mode in the underlay on all mlag l3 peer interface and core interfaces for the specific node. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;static</samp>](## "<node_type_keys.key>.defaults.underlay_multicast.static") | Dictionary |  |  |  |  |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;enabled</samp>](## "<node_type_keys.key>.defaults.underlay_multicast.static.enabled") | Boolean |  |  |  | Enable/Disable static Multicast in the underlay on all p2p uplink interfaces, mlag l3 peer interface and core interfaces for the specific node. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;uplinks</samp>](## "<node_type_keys.key>.defaults.underlay_multicast.static.uplinks") | List, items: String |  |  |  | Enable/Disable static Protocol Independent Multicast in the underlay on specific p2p uplink interfaces. If not set, all uplinks will be enabled. Set as an empty list to remove all uplinks. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;&lt;str&gt;</samp>](## "<node_type_keys.key>.defaults.underlay_multicast.static.uplinks.[]") | String |  |  |  |  |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;mlag</samp>](## "<node_type_keys.key>.defaults.underlay_multicast.static.mlag") | Boolean |  |  |  | Enable/Disable static Multicast in the underlay on all mlag l3 peer interface and core interfaces for the specific node. |
    | [<samp>&nbsp;&nbsp;node_groups</samp>](## "<node_type_keys.key>.node_groups") | List, items: Dictionary |  |  |  | Define variables related to all nodes part of this group. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;group</samp>](## "<node_type_keys.key>.node_groups.[].group") | String | Required, Unique |  |  | The Node Group Name is used for MLAG domain unless set with 'mlag_domain_id'.<br>The Node Group Name is also used for peer description on downstream switches' uplinks.<br> |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;nodes</samp>](## "<node_type_keys.key>.node_groups.[].nodes") | List, items: Dictionary |  |  |  | Define variables per node. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;name</samp>](## "<node_type_keys.key>.node_groups.[].nodes.[].name") | String | Required, Unique |  |  | The Node Name is used as "hostname". |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;mgmt_gateway</samp>](## "<node_type_keys.key>.node_groups.[].nodes.[].mgmt_gateway") | String |  |  |  | This key sets the management gateway for the device. It takes precedence over the global `mgmt_gateway`. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ipv6_mgmt_gateway</samp>](## "<node_type_keys.key>.node_groups.[].nodes.[].ipv6_mgmt_gateway") | String |  |  |  | This key sets the ipv6 management gateway for the device. It takes precedence over the global `ipv6_mgmt_gateway`. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;flow_tracker_type</samp>](## "<node_type_keys.key>.node_groups.[].nodes.[].flow_tracker_type") | String |  |  | Valid Values:<br>- <code>sampled</code><br>- <code>hardware</code> | Set the flow tracker type.<br>Override the `default_flow_tracker_type`` set at the `node_type_key` level.<br>`default_flow_tracker_type` default value is `sampled`. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;underlay_multicast</samp>](## "<node_type_keys.key>.node_groups.[].nodes.[].underlay_multicast") | Dictionary |  |  |  |  |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;pim_sm</samp>](## "<node_type_keys.key>.node_groups.[].nodes.[].underlay_multicast.pim_sm") | Dictionary |  |  |  |  |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;enabled</samp>](## "<node_type_keys.key>.node_groups.[].nodes.[].underlay_multicast.pim_sm.enabled") | Boolean |  |  |  | Enable/Disable Protocol Independent Multicast sparse mode in the underlay on all p2p uplink interfaces, mlag l3 peer interface and core interfaces for the specific node. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;uplinks</samp>](## "<node_type_keys.key>.node_groups.[].nodes.[].underlay_multicast.pim_sm.uplinks") | List, items: String |  |  |  | Enable/Disable Protocol Independent Multicast sparse mode in the underlay on specific p2p uplink interfaces. If not set, all uplinks will be enabled. Set as an empty list to remove all uplinks. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;&lt;str&gt;</samp>](## "<node_type_keys.key>.node_groups.[].nodes.[].underlay_multicast.pim_sm.uplinks.[]") | String |  |  |  |  |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;mlag</samp>](## "<node_type_keys.key>.node_groups.[].nodes.[].underlay_multicast.pim_sm.mlag") | Boolean |  |  |  | Enable/Disable Protocol Independent Multicast sparse mode in the underlay on all mlag l3 peer interface and core interfaces for the specific node. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;static</samp>](## "<node_type_keys.key>.node_groups.[].nodes.[].underlay_multicast.static") | Dictionary |  |  |  |  |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;enabled</samp>](## "<node_type_keys.key>.node_groups.[].nodes.[].underlay_multicast.static.enabled") | Boolean |  |  |  | Enable/Disable static Multicast in the underlay on all p2p uplink interfaces, mlag l3 peer interface and core interfaces for the specific node. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;uplinks</samp>](## "<node_type_keys.key>.node_groups.[].nodes.[].underlay_multicast.static.uplinks") | List, items: String |  |  |  | Enable/Disable static Protocol Independent Multicast in the underlay on specific p2p uplink interfaces. If not set, all uplinks will be enabled. Set as an empty list to remove all uplinks. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;&lt;str&gt;</samp>](## "<node_type_keys.key>.node_groups.[].nodes.[].underlay_multicast.static.uplinks.[]") | String |  |  |  |  |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;mlag</samp>](## "<node_type_keys.key>.node_groups.[].nodes.[].underlay_multicast.static.mlag") | Boolean |  |  |  | Enable/Disable static Multicast in the underlay on all mlag l3 peer interface and core interfaces for the specific node. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;mgmt_gateway</samp>](## "<node_type_keys.key>.node_groups.[].mgmt_gateway") | String |  |  |  | This key sets the management gateway for the device. It takes precedence over the global `mgmt_gateway`. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ipv6_mgmt_gateway</samp>](## "<node_type_keys.key>.node_groups.[].ipv6_mgmt_gateway") | String |  |  |  | This key sets the ipv6 management gateway for the device. It takes precedence over the global `ipv6_mgmt_gateway`. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;flow_tracker_type</samp>](## "<node_type_keys.key>.node_groups.[].flow_tracker_type") | String |  |  | Valid Values:<br>- <code>sampled</code><br>- <code>hardware</code> | Set the flow tracker type.<br>Override the `default_flow_tracker_type`` set at the `node_type_key` level.<br>`default_flow_tracker_type` default value is `sampled`. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;underlay_multicast</samp>](## "<node_type_keys.key>.node_groups.[].underlay_multicast") | Dictionary |  |  |  |  |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;pim_sm</samp>](## "<node_type_keys.key>.node_groups.[].underlay_multicast.pim_sm") | Dictionary |  |  |  |  |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;enabled</samp>](## "<node_type_keys.key>.node_groups.[].underlay_multicast.pim_sm.enabled") | Boolean |  |  |  | Enable/Disable Protocol Independent Multicast sparse mode in the underlay on all p2p uplink interfaces, mlag l3 peer interface and core interfaces for the specific node. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;uplinks</samp>](## "<node_type_keys.key>.node_groups.[].underlay_multicast.pim_sm.uplinks") | List, items: String |  |  |  | Enable/Disable Protocol Independent Multicast sparse mode in the underlay on specific p2p uplink interfaces. If not set, all uplinks will be enabled. Set as an empty list to remove all uplinks. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;&lt;str&gt;</samp>](## "<node_type_keys.key>.node_groups.[].underlay_multicast.pim_sm.uplinks.[]") | String |  |  |  |  |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;mlag</samp>](## "<node_type_keys.key>.node_groups.[].underlay_multicast.pim_sm.mlag") | Boolean |  |  |  | Enable/Disable Protocol Independent Multicast sparse mode in the underlay on all mlag l3 peer interface and core interfaces for the specific node. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;static</samp>](## "<node_type_keys.key>.node_groups.[].underlay_multicast.static") | Dictionary |  |  |  |  |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;enabled</samp>](## "<node_type_keys.key>.node_groups.[].underlay_multicast.static.enabled") | Boolean |  |  |  | Enable/Disable static Multicast in the underlay on all p2p uplink interfaces, mlag l3 peer interface and core interfaces for the specific node. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;uplinks</samp>](## "<node_type_keys.key>.node_groups.[].underlay_multicast.static.uplinks") | List, items: String |  |  |  | Enable/Disable static Protocol Independent Multicast in the underlay on specific p2p uplink interfaces. If not set, all uplinks will be enabled. Set as an empty list to remove all uplinks. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;&lt;str&gt;</samp>](## "<node_type_keys.key>.node_groups.[].underlay_multicast.static.uplinks.[]") | String |  |  |  |  |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;mlag</samp>](## "<node_type_keys.key>.node_groups.[].underlay_multicast.static.mlag") | Boolean |  |  |  | Enable/Disable static Multicast in the underlay on all mlag l3 peer interface and core interfaces for the specific node. |
    | [<samp>&nbsp;&nbsp;nodes</samp>](## "<node_type_keys.key>.nodes") | List, items: Dictionary |  |  |  | Define variables per node. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;name</samp>](## "<node_type_keys.key>.nodes.[].name") | String | Required, Unique |  |  | The Node Name is used as "hostname". |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;mgmt_gateway</samp>](## "<node_type_keys.key>.nodes.[].mgmt_gateway") | String |  |  |  | This key sets the management gateway for the device. It takes precedence over the global `mgmt_gateway`. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ipv6_mgmt_gateway</samp>](## "<node_type_keys.key>.nodes.[].ipv6_mgmt_gateway") | String |  |  |  | This key sets the ipv6 management gateway for the device. It takes precedence over the global `ipv6_mgmt_gateway`. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;flow_tracker_type</samp>](## "<node_type_keys.key>.nodes.[].flow_tracker_type") | String |  |  | Valid Values:<br>- <code>sampled</code><br>- <code>hardware</code> | Set the flow tracker type.<br>Override the `default_flow_tracker_type`` set at the `node_type_key` level.<br>`default_flow_tracker_type` default value is `sampled`. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;underlay_multicast</samp>](## "<node_type_keys.key>.nodes.[].underlay_multicast") | Dictionary |  |  |  |  |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;pim_sm</samp>](## "<node_type_keys.key>.nodes.[].underlay_multicast.pim_sm") | Dictionary |  |  |  |  |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;enabled</samp>](## "<node_type_keys.key>.nodes.[].underlay_multicast.pim_sm.enabled") | Boolean |  |  |  | Enable/Disable Protocol Independent Multicast sparse mode in the underlay on all p2p uplink interfaces, mlag l3 peer interface and core interfaces for the specific node. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;uplinks</samp>](## "<node_type_keys.key>.nodes.[].underlay_multicast.pim_sm.uplinks") | List, items: String |  |  |  | Enable/Disable Protocol Independent Multicast sparse mode in the underlay on specific p2p uplink interfaces. If not set, all uplinks will be enabled. Set as an empty list to remove all uplinks. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;&lt;str&gt;</samp>](## "<node_type_keys.key>.nodes.[].underlay_multicast.pim_sm.uplinks.[]") | String |  |  |  |  |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;mlag</samp>](## "<node_type_keys.key>.nodes.[].underlay_multicast.pim_sm.mlag") | Boolean |  |  |  | Enable/Disable Protocol Independent Multicast sparse mode in the underlay on all mlag l3 peer interface and core interfaces for the specific node. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;static</samp>](## "<node_type_keys.key>.nodes.[].underlay_multicast.static") | Dictionary |  |  |  |  |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;enabled</samp>](## "<node_type_keys.key>.nodes.[].underlay_multicast.static.enabled") | Boolean |  |  |  | Enable/Disable static Multicast in the underlay on all p2p uplink interfaces, mlag l3 peer interface and core interfaces for the specific node. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;uplinks</samp>](## "<node_type_keys.key>.nodes.[].underlay_multicast.static.uplinks") | List, items: String |  |  |  | Enable/Disable static Protocol Independent Multicast in the underlay on specific p2p uplink interfaces. If not set, all uplinks will be enabled. Set as an empty list to remove all uplinks. |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;&lt;str&gt;</samp>](## "<node_type_keys.key>.nodes.[].underlay_multicast.static.uplinks.[]") | String |  |  |  |  |
    | [<samp>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;mlag</samp>](## "<node_type_keys.key>.nodes.[].underlay_multicast.static.mlag") | Boolean |  |  |  | Enable/Disable static Multicast in the underlay on all mlag l3 peer interface and core interfaces for the specific node. |

=== "YAML"

    ```yaml
    <node_type_keys.key>:

      # Define variables for all nodes of this type.
      defaults:

        # This key sets the management gateway for the device. It takes precedence over the global `mgmt_gateway`.
        mgmt_gateway: <str>

        # This key sets the ipv6 management gateway for the device. It takes precedence over the global `ipv6_mgmt_gateway`.
        ipv6_mgmt_gateway: <str>

        # Set the flow tracker type.
        # Override the `default_flow_tracker_type`` set at the `node_type_key` level.
        # `default_flow_tracker_type` default value is `sampled`.
        flow_tracker_type: <str; "sampled" | "hardware">
        underlay_multicast:
          pim_sm:

            # Enable/Disable Protocol Independent Multicast sparse mode in the underlay on all p2p uplink interfaces, mlag l3 peer interface and core interfaces for the specific node.
            enabled: <bool>

            # Enable/Disable Protocol Independent Multicast sparse mode in the underlay on specific p2p uplink interfaces. If not set, all uplinks will be enabled. Set as an empty list to remove all uplinks.
            uplinks:
              - <str>

            # Enable/Disable Protocol Independent Multicast sparse mode in the underlay on all mlag l3 peer interface and core interfaces for the specific node.
            mlag: <bool>
          static:

            # Enable/Disable static Multicast in the underlay on all p2p uplink interfaces, mlag l3 peer interface and core interfaces for the specific node.
            enabled: <bool>

            # Enable/Disable static Protocol Independent Multicast in the underlay on specific p2p uplink interfaces. If not set, all uplinks will be enabled. Set as an empty list to remove all uplinks.
            uplinks:
              - <str>

            # Enable/Disable static Multicast in the underlay on all mlag l3 peer interface and core interfaces for the specific node.
            mlag: <bool>

      # Define variables related to all nodes part of this group.
      node_groups:

          # The Node Group Name is used for MLAG domain unless set with 'mlag_domain_id'.
          # The Node Group Name is also used for peer description on downstream switches' uplinks.
        - group: <str; required; unique>

          # Define variables per node.
          nodes:

              # The Node Name is used as "hostname".
            - name: <str; required; unique>

              # This key sets the management gateway for the device. It takes precedence over the global `mgmt_gateway`.
              mgmt_gateway: <str>

              # This key sets the ipv6 management gateway for the device. It takes precedence over the global `ipv6_mgmt_gateway`.
              ipv6_mgmt_gateway: <str>

              # Set the flow tracker type.
              # Override the `default_flow_tracker_type`` set at the `node_type_key` level.
              # `default_flow_tracker_type` default value is `sampled`.
              flow_tracker_type: <str; "sampled" | "hardware">
              underlay_multicast:
                pim_sm:

                  # Enable/Disable Protocol Independent Multicast sparse mode in the underlay on all p2p uplink interfaces, mlag l3 peer interface and core interfaces for the specific node.
                  enabled: <bool>

                  # Enable/Disable Protocol Independent Multicast sparse mode in the underlay on specific p2p uplink interfaces. If not set, all uplinks will be enabled. Set as an empty list to remove all uplinks.
                  uplinks:
                    - <str>

                  # Enable/Disable Protocol Independent Multicast sparse mode in the underlay on all mlag l3 peer interface and core interfaces for the specific node.
                  mlag: <bool>
                static:

                  # Enable/Disable static Multicast in the underlay on all p2p uplink interfaces, mlag l3 peer interface and core interfaces for the specific node.
                  enabled: <bool>

                  # Enable/Disable static Protocol Independent Multicast in the underlay on specific p2p uplink interfaces. If not set, all uplinks will be enabled. Set as an empty list to remove all uplinks.
                  uplinks:
                    - <str>

                  # Enable/Disable static Multicast in the underlay on all mlag l3 peer interface and core interfaces for the specific node.
                  mlag: <bool>

          # This key sets the management gateway for the device. It takes precedence over the global `mgmt_gateway`.
          mgmt_gateway: <str>

          # This key sets the ipv6 management gateway for the device. It takes precedence over the global `ipv6_mgmt_gateway`.
          ipv6_mgmt_gateway: <str>

          # Set the flow tracker type.
          # Override the `default_flow_tracker_type`` set at the `node_type_key` level.
          # `default_flow_tracker_type` default value is `sampled`.
          flow_tracker_type: <str; "sampled" | "hardware">
          underlay_multicast:
            pim_sm:

              # Enable/Disable Protocol Independent Multicast sparse mode in the underlay on all p2p uplink interfaces, mlag l3 peer interface and core interfaces for the specific node.
              enabled: <bool>

              # Enable/Disable Protocol Independent Multicast sparse mode in the underlay on specific p2p uplink interfaces. If not set, all uplinks will be enabled. Set as an empty list to remove all uplinks.
              uplinks:
                - <str>

              # Enable/Disable Protocol Independent Multicast sparse mode in the underlay on all mlag l3 peer interface and core interfaces for the specific node.
              mlag: <bool>
            static:

              # Enable/Disable static Multicast in the underlay on all p2p uplink interfaces, mlag l3 peer interface and core interfaces for the specific node.
              enabled: <bool>

              # Enable/Disable static Protocol Independent Multicast in the underlay on specific p2p uplink interfaces. If not set, all uplinks will be enabled. Set as an empty list to remove all uplinks.
              uplinks:
                - <str>

              # Enable/Disable static Multicast in the underlay on all mlag l3 peer interface and core interfaces for the specific node.
              mlag: <bool>

      # Define variables per node.
      nodes:

          # The Node Name is used as "hostname".
        - name: <str; required; unique>

          # This key sets the management gateway for the device. It takes precedence over the global `mgmt_gateway`.
          mgmt_gateway: <str>

          # This key sets the ipv6 management gateway for the device. It takes precedence over the global `ipv6_mgmt_gateway`.
          ipv6_mgmt_gateway: <str>

          # Set the flow tracker type.
          # Override the `default_flow_tracker_type`` set at the `node_type_key` level.
          # `default_flow_tracker_type` default value is `sampled`.
          flow_tracker_type: <str; "sampled" | "hardware">
          underlay_multicast:
            pim_sm:

              # Enable/Disable Protocol Independent Multicast sparse mode in the underlay on all p2p uplink interfaces, mlag l3 peer interface and core interfaces for the specific node.
              enabled: <bool>

              # Enable/Disable Protocol Independent Multicast sparse mode in the underlay on specific p2p uplink interfaces. If not set, all uplinks will be enabled. Set as an empty list to remove all uplinks.
              uplinks:
                - <str>

              # Enable/Disable Protocol Independent Multicast sparse mode in the underlay on all mlag l3 peer interface and core interfaces for the specific node.
              mlag: <bool>
            static:

              # Enable/Disable static Multicast in the underlay on all p2p uplink interfaces, mlag l3 peer interface and core interfaces for the specific node.
              enabled: <bool>

              # Enable/Disable static Protocol Independent Multicast in the underlay on specific p2p uplink interfaces. If not set, all uplinks will be enabled. Set as an empty list to remove all uplinks.
              uplinks:
                - <str>

              # Enable/Disable static Multicast in the underlay on all mlag l3 peer interface and core interfaces for the specific node.
              mlag: <bool>
    ```
