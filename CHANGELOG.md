# Changelog

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
