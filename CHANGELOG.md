# Changelog

## [1.7.1.1] — 2026-11-06

### Added (from upstream v1.7.1)

- Local integration icons and logos, including high-resolution versions.

### Changed

- Synced with upstream main through `812a2d3`, including v1.7.1 and subsequent CI and installation-documentation updates.
- Upstream CI now installs the matching official `pytest-homeassistant` package from PyPI. Fork tests use the shared compatibility helper for both supported test packages.
- Release automation only publishes after successful CI on a push to this repository.
- Installation instructions identify this fork as a custom Marketplace/HACS repository because the default catalog now points to upstream.
- Preserved the fork's upload warnings, sensor monitoring, conductivity-unit support, and repository identity. The integration version is `1.7.1.1-beta1` while awaiting release validation.

## [1.7.0.1] — 2026-11-02

### Added (from upstream v1.7.0)

- **Reauth and reconfigure flows**: when the API rejects the stored credentials, Home Assistant starts a re-authentication flow automatically. Credentials can also be changed from the entry's **Reconfigure** menu, without deleting the integration.
- **Manifest category**: `garden_plants` integration category.
- **Docs/tooling**: `CONTRIBUTING.md`, `docs/openplantbook-api-reference.md`, `.gitattributes` (LF line endings), native GitHub release notes config, CI testing against the newest HA and HA betas (incl. the official `pytest-home-assistant` package).

### Changed (from upstream v1.7.0)

- **DLI conversion**: OpenPlantbook mmol light values are daily integrals, so `max_dli`/`min_dli` are now `mmol × 0.001` (mol/m²/d), replacing the old ratio-based ×0.0036 logic. Converted values are clamped to 65 mol/m²/d with a warning.
- **Plant device lookup**: the uploader finds plant devices through the Plant integration's config entries instead of scanning the device registry (`device_registry.devices` mapping access is deprecated in HA 2026.9). Other integrations' devices with "plant" in their identifiers are no longer matched.

### Fork-only features kept

- Upload-warning UI notifications (`notify_upload_warnings`), stale/missing sensor detection, extra conductivity unit variants, one-off info message, permission/rate-limit tests.
- Fork tests now mock the new `_plant_devices` lookup instead of the device registry.

### Upgrade notes

- DLI attributes (`max_dli`, `min_dli`) will show different (corrected) values after upgrading. Review any automations that depend on them.

## [1.6.0.1] — 2026-06-27

### Added (from upstream v1.6.0)

- **Real Home Assistant entities**: `openplantbook.search_result` and the per-species `openplantbook.<species>` results are now proper registered entities (backed by `EntityComponent`) with stable unique IDs, instead of ad-hoc states. They now appear in the entity registry.
- **Automatic entity cleanup**: per-species entities are purged from the registry when their cache entry expires.
- **Single-instance enforcement**: only one OpenPlantbook config entry is allowed, and the config entry is assigned a stable `unique_id`.
- **Tooling**: upstream Dependabot config, expanded ruff ruleset, and manifest dependency monitoring (PyPI freshness + HA-core guard).

### Upgrade notes

- **Upgrading from 1.5.1**: because search/get results are now **real entities**, their registry representation changes. Templates and automations that read the `openplantbook.search_result` and `openplantbook.<species>` states continue to work, but the entities now appear in the entity registry and are subject to single-instance enforcement and automatic expiry cleanup. Review any dashboards that referenced the previous ad-hoc states.

## [1.5.1] — 2026-05-28

### Added

- **Extra data categories in `get`**: `openplantbook.get` service now accepts an `include` parameter to request extra
  data categories (e.g., `care`) from the API.
- **AGENTS.md**: new guidance file for AI agents working in this repository.

### Changed

- **Include parameter aligned with upstream v1.5.0**: `include` is parsed as a comma-separated list (whitespace
  trimmed, duplicates removed) and sent to the API as a sorted string (e.g. `" care , poison "` → `care,poison`).
- **Subset-based include caching**: one cache entry per species tracks which extra categories are already satisfied via
  `_fetched_includes`. A plain `get` reuses a cached entry that already has `care`; requesting new categories (e.g.
  `care` after a base fetch) triggers a refetch. Matches
  [Olen/home-assistant-openplantbook v1.5.0](https://github.com/Olen/home-assistant-openplantbook/releases/tag/v1.5.0).
- **Cache bypass**: `cache: false` clears and refetches the species entry even when all requested `include`
  categories are already satisfied.
- **Cache cleanup logic**: `clean_cache` iterates species entries directly (single entry per species under the new
  model).
- **Error handling cleanup**: cache sentinel entries are cleared on API errors; a `finally` block ensures in-flight
  placeholders are removed when a fetch does not complete.
- **Upload validator**: switched from `isinstance(supported_unit, (list, tuple, set))` to
  `isinstance(supported_unit, list | tuple | set)` for consistency.
- **Tests**: added upstream-compatible coverage for `_parse_includes`, include API params, subset caching, cache
  bypass with `include`, and care fields on entity attributes.

## [1.5.0] — 2026-05-27

### Added
- **Cache bypass** for the `get` service: pass `cache: false` to force-fetch plant data from the API, bypassing the local cache. Useful for "Force refresh" workflows in plant integrations.
- **Home Assistant language support**: optionally send the configured HA language (ISO 639-1) to the OpenPlantbook API so common plant names are returned in the user's language. Controlled via the new `use_ha_language` option (enabled by default).
- **Plant sensor monitoring**: upload process now detects stale sensors (no updates in >24h) and sensors with no valid data, with optional persistent UI notifications grouped by plant.
- **Configurable upload warnings**: new `notify_upload_warnings` option to enable persistent notifications when sensor issues or upload gaps are detected.
- **Upload schedule randomization**: each integration instance now picks a random time of day for its daily upload (seeded from the entry ID), spreading load across the OpenPlantbook API instead of all instances uploading simultaneously.
- **Rate limit error handling**: all service calls (`get`, `search`, `upload`) now catch `RateLimitError` and surface it as a `HomeAssistantError` instead of crashing.
- **Authentication error handling**: `PermissionError` from the SDK (expired/invalid tokens) is now caught and raised as `InvalidAuth`, prompting the user to reconfigure.
- **Image download error handling**: `PermissionError` when writing downloaded plant images is now caught and logged instead of crashing.
- **Extended conductivity unit support**: `µS/cm` (micro sign U+00B5) and `μS/cm` (Greek mu U+03BC) variants are now accepted alongside the standard `MICROSIEMENS_PER_CM` unit.
- **New test coverage**: tests for rate limit errors and permission/auth errors in service calls, plus expanded uploader tests.

### Changed
- **SDK**: `openplantbook-sdk` bumped from 0.4.7 to 0.6.1.
- **Repository**: ownership transferred from `@Olen` to `@slaxor505`; all documentation/issue tracker URLs updated accordingly.
- **Base URL**: API client now explicitly receives `PLANTBOOK_BASEURL` rather than relying on SDK defaults.
- **Upload restart delay**: increased from 5 minutes to 4 hours after HA restart before the first scheduled upload.
- **First-time upload window**: expanded from 1 day to 2 days of historical data.
- **Image filename parsing**: now uses `urllib.parse.urlparse` to extract the path from image URLs, fixing filenames for URLs with query parameters.
- **Info message logic**: fixed so the one-off upgrade notification triggers on message version change rather than only on first install.
- **Upload "no data" warnings**: no longer restricted to specific weekdays — stale/missing sensor warnings can fire any day.
- **Logging**: switched from f-string formatting to `%`-style lazy formatting throughout for better performance and HA log standards compliance.
- **Tests**: refactored uploader tests with reusable `mock_upload_env` fixture; removed inline mocks.

### Removed
- `GUI.md` example documentation and associated assets.
- `TODO.txt` task list.
- `FLOW_UPLOAD_DATA` constant (replaced by refactored config flow). The old upload-data-only notification check was replaced by the new combined info message.

## [1.3.3] and earlier

See the [GitHub releases page](https://github.com/slaxor505/home-assistant-openplantbook/releases) for historical changelogs.
