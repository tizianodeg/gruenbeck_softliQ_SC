# Integration Gruenbeck SoftliQ SC

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![Community Forum][forum-shield]][forum]

_Integration to integrate with [hass_gruenbeck_SC_Local][hass_gruenbeck_SC_Local]._

**This integration will set up the following platforms.**

Platform | Description
-- | --
`sensor` | Show info from blueprint API.

## Installation

### With HACS

1. Register this repository as a custom repository
1.


### Manual
1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
1. If you do not have a `custom_components` directory (folder) there, you need to create it.
1. In the `custom_components` directory (folder) create a new folder called `gruenbeck_softliQ_SC`.
1. Download _all_ the files from the `custom_components/gruenbeck_softliQ_SC/` directory (folder) in this repository.
1. Place the files you downloaded in the new directory (folder) you created.
1. Restart Home Assistant

## Configuration is done in the UI

1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Gruenbeck SoftliQ SC"
1. Provide the IP-Address of you Gruenbeck softliQ Device 
1. Define the Room your Device belongs to 

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***

[hass_gruenbeck_SC_Local]: https://github.com/ludeeus/hass_gruenbeck_SC_Local
[commits-shield]: https://img.shields.io/github/commit-activity/y/tizianodeg/hass_gruenbeck_SC_Local.svg?style=for-the-badge
[commits]: https://github.com/tizianodeg/hass_gruenbeck_SC_Local/commits/main
[exampleimg]: example.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/tizianodeg/hass_gruenbeck_SC_Local.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/tizianodeg/hass_gruenbeck_SC_Local.svg?style=for-the-badge
[releases]: https://github.com/tizianodeg/hass_gruenbeck_SC_Local/releases