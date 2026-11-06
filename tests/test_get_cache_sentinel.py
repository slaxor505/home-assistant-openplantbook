from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET

from custom_components.openplantbook import async_setup_entry
from custom_components.openplantbook.const import (
    ATTR_SPECIES,
    DOMAIN,
    OPB_DISPLAY_PID,
    OPB_PID,
    OPB_SERVICE_GET,
)

from .ha_common import MockConfigEntry


@pytest.mark.asyncio
async def test_get_clears_inflight_sentinel_on_unexpected_error(hass):
    """An unexpected API error must not leave the {} sentinel cached.

    Otherwise later `get` calls fall into the wait-loop and time out instead of
    retrying (cache poisoning). Guards the finally cleanup in get_plant.
    """
    plant_data = {
        OPB_PID: "capsicum annuum",
        OPB_DISPLAY_PID: "Capsicum annuum",
    }

    api = AsyncMock()
    # First call blows up unexpectedly; the second call succeeds.
    api.async_plant_detail_get = AsyncMock(
        side_effect=[RuntimeError("boom"), plant_data]
    )

    with patch("custom_components.openplantbook.OpenPlantBookApi", return_value=api):
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={CONF_CLIENT_ID: "client", CONF_CLIENT_SECRET: "secret"},
            options={},
        )
        entry.add_to_hass(hass)
        assert await async_setup_entry(hass, entry)

        with pytest.raises(RuntimeError):
            await hass.services.async_call(
                DOMAIN,
                OPB_SERVICE_GET,
                {ATTR_SPECIES: "capsicum annuum"},
                blocking=True,
            )

        # The sentinel must be cleaned up, not left poisoning the cache.
        assert "capsicum annuum" not in hass.data[DOMAIN][ATTR_SPECIES]

        # A subsequent call should retry the API (not hit the wait-loop) and succeed.
        response = await hass.services.async_call(
            DOMAIN,
            OPB_SERVICE_GET,
            {ATTR_SPECIES: "capsicum annuum"},
            blocking=True,
            return_response=True,
        )

    assert response[OPB_PID] == "capsicum annuum"
    assert api.async_plant_detail_get.await_count == 2
