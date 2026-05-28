# AGENTS.md — OpenPlantbook Home Assistant Integration

Guidance for AI agents working in this repository. Keep this file in sync with `services.yaml`, `manifest.json`, and `README.md` whenever services, entities, or options change.

---

## 1. Repository rules (must follow)

### Git
- Read-only git is allowed: `git status`, `git diff`, `git log`.
- Do **not** run state-changing git commands: `restore`, `reset`, `add`, `commit`, `stash`, `checkout`/`switch`, `merge`, `rebase`, `cherry-pick`, `tag`, `branch -d`.

### Scope control
- Implement only the exact requested change.
- No drive-by refactors, reformatting, cleanups, dependency bumps, or adjacent fixes.
- If you spot an out-of-scope bug: report it and request explicit approval before touching code. If approved, deliver it as a separate commit/PR.

### Tests
- Run all tests in **WSL only**, using the current PyCharm virtual environment.
- Do not invent new test infrastructure unless asked.

---

## 2. Project overview

This is a custom Home Assistant integration that connects HA to [OpenPlantbook](https://open.plantbook.io/).

- Integration path in this repo: `custom_components/openplantbook/`
- Domain: `openplantbook`
- Distributed via HACS (recommended) or manual copy to `<config>/custom_components/openplantbook/`
- Declares HA dependencies on `history` and `recorder` (do not disable)

Key source files:
- `__init__.py` — service registration, search/get/cache logic, image download
- `uploader.py` — sensor data upload scheduling and execution
- `config_flow.py` — credential entry and options flow
- `services.yaml` — service schemas (keep aligned with code)
- `manifest.json` — version, requirements, dependencies
- `tests/` — pytest suite (`test_init.py`, `test_uploader.py`, `test_config_flow.py`, etc.)

---

## 3. Services exposed

| Service | Input | Effect |
|---|---|---|
| `openplantbook.search` | `alias` (str, required) | Sets `openplantbook.search_result`: state = result count, attributes = `pid → scientific name`. |
| `openplantbook.get` | `species` (str, required — exact `pid` from search) | Sets `openplantbook.<species_slug>` with attributes (`max_soil_moist`, `min_soil_moist`, `max_temp`, `image_url`, …). |
| `openplantbook.upload` | none | Uploads anonymized plant sensor data for the last 24 h (up to 7 d for catch-up). Returns `null` on no-op/error; details in logs. |
| `openplantbook.clean_cache` | `hours` (int, optional, default 24) | Drops cached entries older than `hours`. |

Entity IDs from `get` are slugified: `capsicum annuum` → `openplantbook.capsicum_annuum`.

### Example YAML

```yaml
service: openplantbook.search
service_data:
  alias: Capsicum
```

```yaml
service: openplantbook.get
service_data:
  species: capsicum annuum
```

```yaml
service: openplantbook.clean_cache
service_data:
  hours: 6
```

---

## 4. Safe-usage rules for agents

**Do**
- Use the `search → pick exact pid → get` flow; never guess species names.
- Throttle: add delays/backoff between calls; prefer HA automations on hour-scale intervals over polling.
- Surface results through HA entities/templates rather than log scraping.
- For uploads: get explicit user opt-in and clearly state that data is shared anonymously.
- Respect the user's location-sharing choice (country vs. coordinates); only relevant when uploads are enabled.
- Recommend setting the `openplantbook_sdk` logger to `debug` when diagnosing issues.

**Don't**
- Don't call `get` with names not returned by `search` — `pid` must match exactly.
- Don't create/overwrite plant image files manually; the integration downloads them when configured and never overwrites.
- Don't change HA's general location or integration options without explicit user approval.
- Don't tight-loop services or ignore API rate limits.
- Don't upload sensor data unless the user opted in and it's actually needed.
- Don't store the user's `client_id`/`secret` outside HA.

---

## 5. Setup checklist (when verifying an install)

1. Integration enabled; domain `openplantbook` is configured.
2. Credentials: `client_id` and `secret` from <https://open.plantbook.io/apikey/show/>; config flow validates and aborts on invalid input.
3. Optional options:
   - Upload sensor data — requires the sister "Home Assistant Plant" integration.
   - Location sharing (country/coordinates) — only with explicit user consent.
   - Image auto-download path — must exist and be writable; under `/config/www/...` to be served via `/local/...`.
4. `history` and `recorder` are enabled.

---

## 6. Quality-scale audit mode (optional task)

When asked to audit this integration against a Home Assistant quality-scale rule:

1. **Fetch the rule** from
   `https://raw.githubusercontent.com/home-assistant/developers.home-assistant/refs/heads/master/docs/core/integration-quality-scale/rules/{rule_name}.md`
   and extract: requirements, required code patterns, anti-patterns, exemption criteria, and tier (Bronze/Silver/Gold/Platinum).
2. **Inspect the integration** at `custom_components/openplantbook/`:
   - `manifest.json` — quality-scale declaration
   - `quality_scale.yaml` (if present) — rule status (`done` / `todo` / `exempt`)
   - Relevant Python modules, `services.yaml`, `strings.json`, translations
3. **Cross-references**:
   - Integration docs: `https://raw.githubusercontent.com/home-assistant/home-assistant.io/refs/heads/current/source/_integrations/openplantbook.markdown`
   - PyPI metadata: `https://pypi.org/pypi/<package>/json`
4. **Verify**:
   - `exempt` → exemption reason is valid.
   - `done` → implementation actually matches the rule.
   - Apply rules cumulatively per declared tier (Bronze ⊆ Silver ⊆ Gold ⊆ Platinum).
5. **Report** with these sections: Rule Summary, Compliance Status (pass/fail/exempt), Evidence (file + lines), Issues Found, Recommendations, Exemption Analysis (if applicable).

If the rule doc or required code is unreachable, state explicitly what's missing instead of guessing.

---

## 7. Privacy

- Uploads are anonymized; location sharing is opt-in and must be explicit.
- Never exfiltrate or persist `client_id`/`secret` outside HA.
- When proposing actions, state up front what data will be accessed or shared.

---

## 8. Maintainers — keeping this file current

When services, entities, or config options change:
1. Update `services.yaml`, `manifest.json`, and `README.md`.
2. Mirror the relevant changes here in `AGENTS.md`.
3. Update `CHANGELOG.md`.

More info:
- README: `README.md`
- Issues: <https://github.com/slaxor505/home-assistant-openplantbook/issues>
