# Integration Gruenbeck SoftliQ SC

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![Community Forum][forum-shield]][forum]

_Integration to integrate with [gruenbeck_softliQ_SC][gruenbeck_softliQ_SC]._

# Gruenbeck SoftliQ SC Home Assistant Integration

## Supported Platforms

This integration provides support for the following platforms:

| Platform  | Description |
|-----------|------------|
| `sensor`  | Displays information from the Grünbeck Softliq Mux API. |
| `select`  | Allows changing the operation mode of the Softliq system. |

## Installation

### With HACS

1. Open HACS in Home Assistant.
2. Click the three dots in the top-right corner, then select "Add custom repository".
3. Enter the following URL: [https://github.com/tizianodeg/gruenbeck_softliQ_SC/](https://github.com/tizianodeg/gruenbeck_softliQ_SC/) and set the type to "Integration".
4. Click the "+" button in the bottom-left corner to add the new "Gruenbeck SoftliQ SC" integration.
5. Download the integration.
6. Restart Home Assistant.

### Manual Installation

1. Using a file manager or terminal, navigate to your Home Assistant configuration directory (where `configuration.yaml` is located).
2. If the `custom_components` folder does not exist, create it.
3. Inside the `custom_components` directory, create a new folder named `gruenbeck_softliq_sc`.
4. Download all files from `custom_components/gruenbeck_softliq_sc/` in this repository and place them into the newly created directory.
5. Restart Home Assistant.

## Configuration in the UI

1. In the Home Assistant UI, go to **Configuration** → **Integrations**.
2. Click "+" and search for "Gruenbeck SoftliQ SC".
3. Enter a name for the device and the IP address of your Grünbeck SoftliQ device.
4. Assign the device to a room.

## Contributions

Contributions are welcome! 

## Developer Notes

Translation, value mappings, and unit information are extracted from the local UI JavaScript file:
[http://<device-ip>/var.js](http://<device-ip>/var.js)

An unofficial documentation of the Mux interface is also attached:
[Webserver_Dokumentation.pdf](Webserver_Dokumentation.pdf)

The following protected-area codes have been observed in the local UI and parameter exports:

### SC

| Bereich                     | Code |
|-----------------------------|------|
| Programmierbare Ein/Ausgänge | 113  |
| Kontrollparameter           | 142  |
| Anlage-Datensatz            | 290  |
| Hydraulische Werte          | 121  |
| Schrittabstände             | 302  |
| Fehlerspeicher              | 245  |
| Fehlerspeicher zurücksetzen | 189  |

### MC

| Area | Code | Notes |
|------|------|-------|
| System data record | `290` | Used for `D_F_6` |
| Installer level | `005` | Exposes `D_K_3` |
| Programmable input and output | `005` | From UI traces |
| Control parameters | `142` | From UI traces |
| Hydraulic values | `121` | From UI traces |
| Step intervals / distances | `302` | From UI traces |
| Meter / counter readings | `245` | Uses `D_K_5`, `D_K_8_1..7`, `D_K_9_1..7` |
| Error memory & change history | `005` | UI traces place error history behind `005` |
| Reset error memory | not confirmed | Uses `D_M_3_3`, numeric code still unverified |

Current implementation notes:

- Model detection uses `D_Y_6` major version plus the system-data record: `D_F_4` for SC and `D_F_6` for MC.
- Current-value polling is model-specific because SC and MC do not expose the same parameter keys.
- Diagnostic polling is also model-specific. MC values span multiple protected areas, so the integration merges more than one MUX read.

see: [https://www.haustechnikdialog.de/Forum/t/232430/Gruenbeck-SC18-Fehlerspeicher?PostSort=1](https://www.haustechnikdialog.de/Forum/t/232430/Gruenbeck-SC18-Fehlerspeicher?PostSort=1)

**Performance Considerations:**

The web server on the water softener has limited capacity and can only handle a few simultaneous requests. If multiple applications (this Home Assistant integration, the Web UI, and the phone app) access the Mux interface at the same time, performance will degrade.

For debugging purposes, disable this integration and ensure that only one application is accessing the Mux interface at a time.



***

[gruenbeck_softliQ_SC]: https://github.com/tizianodeg/gruenbeck_softliQ_SC
[commits-shield]: https://img.shields.io/github/commit-activity/y/tizianodeg/gruenbeck_softliQ_SC.svg?style=for-the-badge
[commits]: https://github.com/tizianodeg/gruenbeck_softliQ_SC/commits/main
[exampleimg]: example.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/tizianodeg/gruenbeck_softliQ_SC.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/tizianodeg/gruenbeck_softliQ_SC.svg?style=for-the-badge
[releases]: https://github.com/tizianodeg/gruenbeck_softliQ_SC/releases
