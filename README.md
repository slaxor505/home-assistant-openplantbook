# 🌿 Founder-Edition of OpenPlantbook Integration for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/slaxor505/home-assistant-openplantbook?style=for-the-badge)](https://github.com/slaxor505/home-assistant-openplantbook/releases)

Connects Home Assistant to the [OpenPlantbook API](https://open.plantbook.io/) for searching plant species, fetching care data, and uploading sensor readings. Used as the data backend for the [Plant Monitor](https://github.com/slaxor505/homeassistant-plant) integration.

This is fork of original [OpenPlantbook](https://github.com/PlantMonitor/home-assistant-openplantbook) integration that reflects the [Open Plantbook founder](https://plantbook.io/about-us/)'s vision and adds extra features. 
The goal of this fork is to stay aligned with Open Plantbook features, keep things simple to use, and remain compatible with Home Assistant, including the custom plant integration.

---

## 📑 Table of Contents

- [🌿 Founder-Edition of OpenPlantbook Integration for Home Assistant](#-founder-edition-of-openplantbook-integration-for-home-assistant)
  - [🆕 What's New](#-whats-new-in-version-1711)
  - [📦 Installation](#-installation)
  - [🔧 Setup](#-setup)
  - [⚙️ Configuration Options](#️-configuration-options)
    - [📤 Upload Plant Sensor Data](#-upload-plant-sensor-data)
    - [🔔 Sensors Monitoring](#-sensors-monitoring)
    - [🌍 Share Location](#-share-location)
    - [🌐 International Common Names](#-international-common-names)
    - [🖼️ Automatically Download Images](#️-automatically-download-images)
  - [📡 Actions (Service Calls)](#-actions-service-calls)

---

## 🆕 What's New in version 1.7.1.1

Synced through [upstream v1.7.1](https://github.com/Olen/home-assistant-openplantbook/releases/tag/v1.7.1), including the subsequent documentation and CI updates:

- **Local brand images** — the integration includes its icons and logos, including high-resolution versions.
- **CI and releases** — updated Home Assistant test-package installation and release automation restricted to successful pushes to this repository.

- **Update credentials without re-adding** — if your API credentials stop working, Home Assistant now asks you to re-authenticate. You can also change them any time via the integration's **⋮ → Reconfigure** menu.
- **Corrected DLI values** — `max_dli` / `min_dli` are now calculated as a plain mmol → mol conversion (mol/m²/d) and capped at 65 (the physical maximum). Your plant DLI thresholds may change after upgrading.
- **Future-proof plant device lookup** — sensor-data upload finds plants via the Plant integration's config entries (needed for Home Assistant 2026.9+). Devices from other integrations whose names merely contain "plant" are no longer picked up.

> [!NOTE]
> All fork-only features (sensor monitoring notifications, extra conductivity units, etc.) are kept. See the [CHANGELOG](./CHANGELOG.md) for details.

## 🆕 What's New in version 1.6.0.1

- **Real Home Assistant entities** — `openplantbook.search_result` and the per-species `openplantbook.<species>` results are now proper registered entities (with stable unique IDs) instead of ad-hoc states. They appear in the entity registry, and per-species entities are automatically cleaned up when their cache entry expires. Existing templates and automations that read these states keep working. Synced from [upstream v1.6.0](https://github.com/Olen/home-assistant-openplantbook/releases/tag/v1.6.0).
- **Single instance** — only one OpenPlantbook integration entry is allowed per Home Assistant.

> [!NOTE]
> Upgrading from 1.5.1: search/get results are now real entities. Your existing automations and dashboard templates continue to work, but the entities now show up in the entity registry. See the [CHANGELOG](./CHANGELOG.md) for details.

## 🆕 What's New in version 1.5.1

- **Extra data categories in `get`** — The `openplantbook.get` service now supports an `include` parameter to request extra data categories like `care` from the API. See [openplantbook.get](#openplantbookget).
- **Smarter caching for extra data** — When you request extra data (like `care`) for a plant, those results are cached
  separately. This means fetching the same plant with different `include` options won't overwrite each other, and each
  variant stays fresh in the cache.

## 🆕 What's New in version 1.5

- **Sensor monitoring warnings** — Stale or missing sensor updates are flagged during upload runs; details and optional notifications in [🔔 Sensors Monitoring](#-sensors-monitoring).
- **Image downloading supports cache busting** — Image filenames are now derived from the URL path only, ignoring query parameters (e.g. `?v=...`).

## 🆕 What's New in version 1.4

- **International common names** — OpenPlantbook can return common names in your Home Assistant language. See [🌐 International Common Names](#-international-common-names).

---

## 📦 Installation

### Via the Marketplace *(recommended)*

The default catalog now points to [upstream OpenPlantbook](https://github.com/Olen/home-assistant-openplantbook). To install this Founder Edition, add `https://github.com/slaxor505/home-assistant-openplantbook` as a **custom repository**, with category **Integration**, in the Marketplace (HACS before Home Assistant 2026.11).

[![Open this fork in the Marketplace.](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=slaxor505&repository=home-assistant-openplantbook&category=integration)

1. Open the Marketplace or HACS and add the custom repository above if needed.
2. Open the OpenPlantbook repository card and verify its owner is **slaxor505**.
3. Click **Install** (**Download** in HACS), then restart Home Assistant.

> [!TIP]
> To install a pre-release (e.g. a `-beta` version), enable **Show beta versions** in the repository card before downloading.

> [!NOTE]
> Both this fork and upstream use the domain `openplantbook`; install one version at a time. You can continue using this fork to keep its sensor-monitoring notifications and other extra features.

### Manual Installation

1. Copy `custom_components/openplantbook/` to your `<config>/custom_components/` directory
2. Restart Home Assistant

---

## 🔧 Setup

You need an OpenPlantbook account (free) with API credentials.

1. Register at [open.plantbook.io](https://open.plantbook.io/)
2. Find your `client_id` and `secret` at https://open.plantbook.io/apikey/show/
3. In Home Assistant: **Settings** → **Devices & Services** → **Add Integration** → **OpenPlantbook**
4. Enter your credentials — the integration validates them and shows an error if incorrect
5. Configure upload settings (optional but recommended)

To change your credentials later, use **⋮ → Reconfigure** on the integration card. If the credentials become invalid, Home Assistant will prompt you to re-authenticate.

---

## ⚙️ Configuration Options

After setup, click **Configure** on the integration card to access additional options.

![Configuration options](./images/config-options.png)

### 📤 Upload Plant Sensor Data

> [!NOTE]
> All data is shared anonymously.

When enabled, the integration periodically (once a day) uploads sensor data from your plants to OpenPlantbook. This helps build a useful community dataset. More info: https://open.plantbook.io/ui/sensor-data/

- First upload: last 24 hours of data
- If sensors are disconnected, it retries daily for up to 7 days of historical data
- Can also be triggered manually via the `openplantbook.upload` action
- Daily uploads are scheduled at a randomized time-of-day per installation (stable for a given config entry) to even load distribution

**Configure in UI:**
- Go to **Settings** → **Devices & Services** → **OpenPlantbook** → **Configure**.
- Enable **Upload plant sensor data**.
- Enable **Plant-sensors monitoring notifications** to surface stale-sensor warnings as HA notifications (requires upload to be enabled).

### 🔔 Sensors Monitoring

Sensor monitoring runs during upload processing (scheduled daily or manual `openplantbook.upload`). For each plant sensor it:

- Looks at recorder history for the upload window and captures the latest *valid* state (ignores `unknown`/`unavailable`).
- If no valid states were found in the window, it falls back to the entity’s last known state change to determine staleness.

Warnings are emitted when:

- **Stale data**: the latest valid update is older than **24 hours**.
- **No valid data**: all recent states are `unknown`/`unavailable` and no last valid state can be determined.

If **Plant-sensors monitoring notifications** is enabled (requires upload enabled), the integration also posts a grouped Home Assistant notification per upload run, including the affected plant, each sensor entity, and the latest OpenPlantbook cloud data timestamp/age for context.

### 🌍 Share Location

Optionally share your Home Assistant location to complement sensor data. Two levels:

| Option | What is shared |
|--------|---------------|
| **Country only** | Country from HA configuration |
| **Coordinates** | Lat/lon from HA configuration |

Location is configured in HA under **Settings** → **System** → **General**.

![Location settings](./images/hass-location.png)

> [!TIP]
> Enable DEBUG logging for the integration to see exactly what data is being shared.
>
> ![Debug logging](./images/debug-logging.png)

### 🌐 International Common Names

When enabled, the integration sends your Home Assistant language to OpenPlantbook so the API can return common names in that language when available.

[More information about this Open Plantbook feature](https://github.com/slaxor505/OpenPlantbook-client/wiki/Plant-Common-names).

### 🖼️ Automatically Download Images

Available in the integration's Options (click **Configure** after setup).

- Default path: `/config/www/images/plants`
- Specify any directory the HA user has write access to
- Relative paths are relative to your config directory

**Path behavior:**
- If the path contains `www/` → `image_url` is replaced with a `/local/` reference
- If the path does **not** contain `www/` → the full OpenPlantbook URL is kept

> [!NOTE]
> Existing files are never overwritten. The target directory must exist before configuring.

---

## 📡 Actions (Service Calls)

### `openplantbook.search`

Search for plants matching a string:

```yaml
action: openplantbook.search
data:
  alias: Capsicum
```

Read results from `openplantbook.search_result`:

```jinja2
Number of plants found: {{ states('openplantbook.search_result') }}
{%- for pid in states.openplantbook.search_result.attributes %}
  {%- set name = state_attr('openplantbook.search_result', pid) %}
  * {{ pid }} -> {{ name }}
{%- endfor %}
```

**Example output:**

```
Number of plants found: 40
  * capsicum annuum -> Capsicum annuum
  * capsicum baccatum -> Capsicum baccatum
  * capsicum chinense -> Capsicum chinense
  (...)
```

### `openplantbook.get`

Get detailed data for a single species:

```yaml
action: openplantbook.get
data:
  species: capsicum annuum
  include: care
```

> [!NOTE]
> The species string must match exactly the `pid` returned by `openplantbook.search`.

**Parameters:**

| Parameter | Required | Default | Description                                                                                                                                                                                                                                                  |
|-----------|----------|---------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `species` | yes | — | Exact `pid` of the species                                                                                                                                                                                                                                   |
| `include` | no | — | Comma-separated extra data categories (e.g., `care`). If omitted, extra categories are not included. See [API docs](https://open.plantbook.io/api/v1/plant/detail/acer%20pseudoplatanus/?include=*) for supported categories |
| `cache`   | no | `true` | Set to `false` to bypass the cache and force a fresh fetch from the API. Each species has a **single** cache entry that records which `include` categories it already holds; requesting a category it doesn't yet have triggers a refetch. |

The result is stored as a Home Assistant state entity. Read it in Jinja templates:

```jinja2
Details for plant {{ states('openplantbook.capsicum_annuum') }}
* Max moisture: {{ state_attr('openplantbook.capsicum_annuum', 'max_soil_moist') }}
* Min moisture: {{ state_attr('openplantbook.capsicum_annuum', 'min_soil_moist') }}
* Max temperature: {{ state_attr('openplantbook.capsicum_annuum', 'max_temp') }}
* Image: {{ state_attr('openplantbook.capsicum_annuum', 'image_url') }}
```

### `openplantbook.upload`

Manually trigger uploading of plant sensor data:

```yaml
action: openplantbook.upload
```

Returns `null` if nothing was uploaded or an error occurred. Check the HA log for details.
