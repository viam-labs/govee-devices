# Module govee-devices

This module provides a Viam [switch component](https://docs.viam.com/operate/reference/components/switch/) for controlling Govee smart plugs and switches via the [Govee Cloud API](https://developer.govee.com/).

## Model viam-labs:govee-devices:smart-plug

This model allows you to turn a Govee smart plug on and off through Viam, using the Govee Cloud API for device control.

### Prerequisites

1. A Govee smart plug added to your Govee Home app.
2. A Govee API key — request one in the Govee Home app under **Settings > About Us > Apply for API Key**.
3. Your device's **SKU** (product model, e.g. `H5080`) and **Device ID** (MAC address format). You can find these by calling the [Govee device list API](https://developer.govee.com/reference/get-you-devices) with your API key.

### Configuration

The following attribute template can be used to configure this model:

```json
{
  "api_key": "<string>",
  "device_id": "<string>",
  "sku": "<string>"
}
```

#### Attributes

| Name        | Type   | Inclusion | Description                                                        |
|-------------|--------|-----------|--------------------------------------------------------------------|
| `api_key`   | string | Required  | Your Govee API key                                                 |
| `device_id` | string | Required  | The device ID (MAC address format, e.g. `"9D:FA:85:EB:D3:00:8B:FF"`) |
| `sku`       | string | Required  | The product model/SKU (e.g. `"H5080"`)                             |

#### Example Configuration

```json
{
  "name": "my-govee-plug",
  "model": "viam-labs:govee-devices:smart-plug",
  "type": "switch",
  "attributes": {
    "api_key": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "device_id": "9D:FA:85:EB:D3:00:8B:FF",
    "sku": "H5080"
  }
}
```

### DoCommand

The following commands are supported via `do_command`:

#### `toggle_on`

Turn the smart plug on.

```json
{"toggle_on": {}}
```

#### `toggle_off`

Turn the smart plug off.

```json
{"toggle_off": {}}
```

#### `toggle_switch`

Toggle the smart plug to the opposite of its current state (queries current state first, then switches).

```json
{"toggle_switch": {}}
```

#### `get_status`

Query the current power state of the smart plug from the Govee API.

```json
{"get_status": {}}
```

#### Example Responses

```json
{"toggle_on": true}
```

```json
{"get_status": "on"}
```

Toggle commands return a boolean (`true` = on, `false` = off). `get_status` returns `"on"` or `"off"`.
