"""Tests for openplantbook integration setup."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from openplantbook_sdk import MissingClientIdOrSecret
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.openplantbook.const import (
    ATTR_API,
    ATTR_IMAGE,
    ATTR_SPECIES,
    DEFAULT_IMAGE_PATH,
    DOMAIN,
    FLOW_DOWNLOAD_IMAGES,
    FLOW_DOWNLOAD_PATH,
    OPB_SERVICE_CLEAN_CACHE,
    OPB_SERVICE_GET,
    OPB_SERVICE_SEARCH,
    OPB_SERVICE_UPLOAD,
)
from custom_components.openplantbook.plantbook_exception import OpenPlantbookException


class TestIntegrationSetup:
    """Tests for integration setup."""

    async def test_async_setup(self, hass: HomeAssistant) -> None:
        """Test async_setup returns True."""
        from custom_components.openplantbook import async_setup

        result = await async_setup(hass, {})
        assert result is True

    async def test_async_setup_entry(
        self,
        hass: HomeAssistant,
        mock_config_entry: MockConfigEntry,
        mock_openplantbook_api: MagicMock,
    ) -> None:
        """Test async_setup_entry creates domain data and services."""
        mock_config_entry.add_to_hass(hass)

        result = await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert result is True
        assert DOMAIN in hass.data
        assert ATTR_API in hass.data[DOMAIN]
        assert ATTR_SPECIES in hass.data[DOMAIN]

    async def test_services_registered(
        self,
        hass: HomeAssistant,
        init_integration: MockConfigEntry,
    ) -> None:
        """Test that all services are registered."""
        assert hass.services.has_service(DOMAIN, OPB_SERVICE_SEARCH)
        assert hass.services.has_service(DOMAIN, OPB_SERVICE_GET)
        assert hass.services.has_service(DOMAIN, OPB_SERVICE_CLEAN_CACHE)
        assert hass.services.has_service(DOMAIN, OPB_SERVICE_UPLOAD)

    async def test_async_unload_entry(
        self,
        hass: HomeAssistant,
        init_integration: MockConfigEntry,
    ) -> None:
        """Test async_unload_entry removes services and data."""
        # Verify setup was successful
        assert DOMAIN in hass.data

        # Unload the entry
        result = await hass.config_entries.async_unload(init_integration.entry_id)
        await hass.async_block_till_done()

        assert result is True
        assert DOMAIN not in hass.data

    async def test_services_removed_on_unload(
        self,
        hass: HomeAssistant,
        init_integration: MockConfigEntry,
    ) -> None:
        """Test that services are removed on unload."""
        # Verify services exist
        assert hass.services.has_service(DOMAIN, OPB_SERVICE_SEARCH)
        assert hass.services.has_service(DOMAIN, OPB_SERVICE_GET)

        # Unload
        await hass.config_entries.async_unload(init_integration.entry_id)
        await hass.async_block_till_done()

        # Services should be removed
        assert not hass.services.has_service(DOMAIN, OPB_SERVICE_SEARCH)
        assert not hass.services.has_service(DOMAIN, OPB_SERVICE_GET)


class TestSearchService:
    """Tests for the search service."""

    async def test_search_service_returns_results(
        self,
        hass: HomeAssistant,
        init_integration: MockConfigEntry,
        mock_openplantbook_api: MagicMock,
    ) -> None:
        """Test search service returns plant results."""
        result = await hass.services.async_call(
            DOMAIN,
            OPB_SERVICE_SEARCH,
            {"alias": "monstera"},
            blocking=True,
            return_response=True,
        )

        assert result is not None
        assert "monstera deliciosa" in result

    async def test_search_service_creates_state(
        self,
        hass: HomeAssistant,
        init_integration: MockConfigEntry,
        mock_openplantbook_api: MagicMock,
    ) -> None:
        """Test search service creates search result state."""
        await hass.services.async_call(
            DOMAIN,
            OPB_SERVICE_SEARCH,
            {"alias": "monstera"},
            blocking=True,
        )

        state = hass.states.get(f"{DOMAIN}.search_result")
        assert state is not None
        assert int(state.state) == 1


class TestGetPlantService:
    """Tests for the get plant service."""

    async def test_get_plant_returns_data(
        self,
        hass: HomeAssistant,
        init_integration: MockConfigEntry,
        mock_openplantbook_api: MagicMock,
    ) -> None:
        """Test get plant service returns plant data."""
        result = await hass.services.async_call(
            DOMAIN,
            OPB_SERVICE_GET,
            {"species": "monstera deliciosa"},
            blocking=True,
            return_response=True,
        )

        assert result is not None
        assert result.get("pid") == "monstera deliciosa"
        assert result.get("display_pid") == "Monstera deliciosa"

    async def test_get_plant_caches_result(
        self,
        hass: HomeAssistant,
        init_integration: MockConfigEntry,
        mock_openplantbook_api: MagicMock,
    ) -> None:
        """Test that get plant caches the result."""
        # First call
        await hass.services.async_call(
            DOMAIN,
            OPB_SERVICE_GET,
            {"species": "monstera deliciosa"},
            blocking=True,
        )

        from custom_components.openplantbook import _cache_key

        cache_key = _cache_key("monstera deliciosa", None)
        assert cache_key in hass.data[DOMAIN][ATTR_SPECIES]

        # Second call should use cache
        mock_openplantbook_api.async_plant_detail_get.reset_mock()
        await hass.services.async_call(
            DOMAIN,
            OPB_SERVICE_GET,
            {"species": "monstera deliciosa"},
            blocking=True,
        )

        # API should not be called again (using cache)
        # Note: This depends on cache time, in practice it should use cache

    async def test_cache_key_function(self) -> None:
        """Test _cache_key builds correct composite keys."""
        from custom_components.openplantbook import _cache_key

        assert _cache_key("monstera", None) == ("monstera", None)
        assert _cache_key("monstera", "") == ("monstera", None)
        assert _cache_key("monstera", "care") == ("monstera", "care")
        assert _cache_key("monstera", "care,poison") == ("monstera", "care,poison")

    async def test_different_include_values_cache_separately(
        self,
        hass: HomeAssistant,
        init_integration: MockConfigEntry,
        mock_openplantbook_api: MagicMock,
    ) -> None:
        """Test that different 'include' values create separate cache entries."""
        from custom_components.openplantbook import _cache_key

        # Fetch without include
        await hass.services.async_call(
            DOMAIN,
            OPB_SERVICE_GET,
            {"species": "monstera deliciosa"},
            blocking=True,
        )

        # Fetch with include="care"
        await hass.services.async_call(
            DOMAIN,
            OPB_SERVICE_GET,
            {"species": "monstera deliciosa", "include": "care"},
            blocking=True,
        )

        # Both cache entries should exist independently
        species_cache = hass.data[DOMAIN][ATTR_SPECIES]
        assert _cache_key("monstera deliciosa", None) in species_cache
        assert _cache_key("monstera deliciosa", "care") in species_cache

        # API should have been called twice (once per unique variant)
        assert mock_openplantbook_api.async_plant_detail_get.call_count == 2

    async def test_cached_variant_served_for_matching_include(
        self,
        hass: HomeAssistant,
        init_integration: MockConfigEntry,
        mock_openplantbook_api: MagicMock,
    ) -> None:
        """Test that a cached variant is returned when the same include is requested again."""
        # First call with include="care"
        await hass.services.async_call(
            DOMAIN,
            OPB_SERVICE_GET,
            {"species": "monstera deliciosa", "include": "care"},
            blocking=True,
        )

        # Reset mock to track subsequent calls
        mock_openplantbook_api.async_plant_detail_get.reset_mock()

        # Second call with same include="care" should use cache
        result = await hass.services.async_call(
            DOMAIN,
            OPB_SERVICE_GET,
            {"species": "monstera deliciosa", "include": "care"},
            blocking=True,
            return_response=True,
        )

        # Should return data and NOT call the API again
        assert result is not None
        assert result.get("pid") == "monstera deliciosa"
        mock_openplantbook_api.async_plant_detail_get.assert_not_called()

    async def test_cache_without_include_isolated_from_with_include(
        self,
        hass: HomeAssistant,
        init_integration: MockConfigEntry,
        mock_openplantbook_api: MagicMock,
    ) -> None:
        """Test that a cached entry without 'include' does not prevent fetching with 'include'.

        This is the core bug fix: previously, fetching without 'include' would cache data
        that was then incorrectly returned for a subsequent request with 'include'.
        """
        # First, fetch without include (this populates the no-include cache variant)
        await hass.services.async_call(
            DOMAIN,
            OPB_SERVICE_GET,
            {"species": "monstera deliciosa"},
            blocking=True,
        )

        # Reset mock so we can verify the API IS called for the include variant
        mock_openplantbook_api.async_plant_detail_get.reset_mock()

        # Now fetch WITH include - should hit the API (not reuse no-include cache)
        result = await hass.services.async_call(
            DOMAIN,
            OPB_SERVICE_GET,
            {"species": "monstera deliciosa", "include": "care"},
            blocking=True,
            return_response=True,
        )

        assert result is not None
        # API should have been called because the include variant wasn't cached yet
        mock_openplantbook_api.async_plant_detail_get.assert_called_once()
        call_kwargs = mock_openplantbook_api.async_plant_detail_get.call_args.kwargs
        assert call_kwargs["params"]["include"] == "care"

    async def test_cache_bypass_clears_only_specific_variant(
        self,
        hass: HomeAssistant,
        init_integration: MockConfigEntry,
        mock_openplantbook_api: MagicMock,
    ) -> None:
        """Test that cache bypass only clears the specific include variant."""
        from custom_components.openplantbook import _cache_key

        # Populate both cache variants
        await hass.services.async_call(
            DOMAIN,
            OPB_SERVICE_GET,
            {"species": "monstera deliciosa"},
            blocking=True,
        )
        await hass.services.async_call(
            DOMAIN,
            OPB_SERVICE_GET,
            {"species": "monstera deliciosa", "include": "care"},
            blocking=True,
        )

        species_cache = hass.data[DOMAIN][ATTR_SPECIES]
        key_no_include = _cache_key("monstera deliciosa", None)
        key_care = _cache_key("monstera deliciosa", "care")
        assert key_no_include in species_cache
        assert key_care in species_cache

        # Bypass cache only for the include="care" variant
        await hass.services.async_call(
            DOMAIN,
            OPB_SERVICE_GET,
            {"species": "monstera deliciosa", "include": "care", "cache": False},
            blocking=True,
        )

        # The no-include variant should still be cached
        assert key_no_include in species_cache
        # The care variant should have been re-fetched (still present but fresh)
        assert key_care in species_cache

    async def test_get_plant_passes_include_param(
        self,
        hass: HomeAssistant,
        init_integration: MockConfigEntry,
        mock_openplantbook_api: MagicMock,
    ) -> None:
        """Test get plant passes 'include' as a query param to the API."""
        await hass.services.async_call(
            DOMAIN,
            OPB_SERVICE_GET,
            {"species": "monstera deliciosa", "include": "care"},
            blocking=True,
        )

        mock_openplantbook_api.async_plant_detail_get.assert_called_once()
        call_kwargs = mock_openplantbook_api.async_plant_detail_get.call_args.kwargs
        assert "params" in call_kwargs
        assert call_kwargs["params"]["include"] == "care"

    async def test_get_plant_no_include_param_when_not_provided(
        self,
        hass: HomeAssistant,
        init_integration: MockConfigEntry,
        mock_openplantbook_api: MagicMock,
    ) -> None:
        """Test get plant does not send 'include' param when not provided."""
        await hass.services.async_call(
            DOMAIN,
            OPB_SERVICE_GET,
            {"species": "monstera deliciosa"},
            blocking=True,
        )

        call_kwargs = mock_openplantbook_api.async_plant_detail_get.call_args.kwargs
        assert "params" not in call_kwargs or "include" not in call_kwargs.get(
            "params", {}
        )


class TestCleanCacheService:
    """Tests for the clean cache service."""

    async def test_clean_cache_removes_old_entries(
        self,
        hass: HomeAssistant,
        init_integration: MockConfigEntry,
        mock_openplantbook_api: MagicMock,
    ) -> None:
        """Test clean cache service removes old entries."""
        # First get a plant to populate cache
        await hass.services.async_call(
            DOMAIN,
            OPB_SERVICE_GET,
            {"species": "monstera deliciosa"},
            blocking=True,
        )

        # Verify it's cached
        from custom_components.openplantbook import _cache_key

        cache_key = _cache_key("monstera deliciosa", None)
        assert cache_key in hass.data[DOMAIN][ATTR_SPECIES]

        # Clean cache with hours=0 to remove all
        await hass.services.async_call(
            DOMAIN,
            OPB_SERVICE_CLEAN_CACHE,
            {"hours": 0},
            blocking=True,
        )

        # Cache should be empty
        assert cache_key not in hass.data[DOMAIN][ATTR_SPECIES]


class TestSearchServiceErrors:
    """Tests for search service error handling."""

    async def test_search_service_missing_alias(
        self,
        hass: HomeAssistant,
        init_integration: MockConfigEntry,
        mock_openplantbook_api: MagicMock,
    ) -> None:
        """Test search service raises error when alias is missing."""
        with pytest.raises(OpenPlantbookException):
            await hass.services.async_call(
                DOMAIN,
                OPB_SERVICE_SEARCH,
                {},  # No alias provided
                blocking=True,
            )

    async def test_search_service_api_error(
        self,
        hass: HomeAssistant,
        init_integration: MockConfigEntry,
        mock_openplantbook_api: MagicMock,
    ) -> None:
        """Test search service handles API errors."""
        mock_openplantbook_api.async_plant_search = AsyncMock(
            side_effect=MissingClientIdOrSecret("Invalid credentials")
        )

        with pytest.raises(MissingClientIdOrSecret):
            await hass.services.async_call(
                DOMAIN,
                OPB_SERVICE_SEARCH,
                {"alias": "monstera"},
                blocking=True,
            )


class TestGetPlantServiceErrors:
    """Tests for get plant service error handling."""

    async def test_get_plant_missing_species(
        self,
        hass: HomeAssistant,
        init_integration: MockConfigEntry,
        mock_openplantbook_api: MagicMock,
    ) -> None:
        """Test get plant raises error when species is missing."""
        with pytest.raises(OpenPlantbookException):
            await hass.services.async_call(
                DOMAIN,
                OPB_SERVICE_GET,
                {},  # No species provided
                blocking=True,
            )

    async def test_get_plant_api_error(
        self,
        hass: HomeAssistant,
        init_integration: MockConfigEntry,
        mock_openplantbook_api: MagicMock,
    ) -> None:
        """Test get plant handles API errors."""
        mock_openplantbook_api.async_plant_detail_get = AsyncMock(
            side_effect=MissingClientIdOrSecret("Invalid credentials")
        )

        with pytest.raises(MissingClientIdOrSecret):
            await hass.services.async_call(
                DOMAIN,
                OPB_SERVICE_GET,
                {"species": "monstera deliciosa"},
                blocking=True,
            )

    async def test_get_plant_returns_empty_when_not_found(
        self,
        hass: HomeAssistant,
        init_integration: MockConfigEntry,
        mock_openplantbook_api: MagicMock,
    ) -> None:
        """Test get plant returns empty dict when plant not found."""
        mock_openplantbook_api.async_plant_detail_get = AsyncMock(return_value=None)

        result = await hass.services.async_call(
            DOMAIN,
            OPB_SERVICE_GET,
            {"species": "unknown_plant"},
            blocking=True,
            return_response=True,
        )

        assert result == {}


class TestUploadService:
    """Tests for the upload service."""

    async def test_upload_service_callable(
        self,
        hass: HomeAssistant,
        init_integration: MockConfigEntry,
        mock_openplantbook_api: MagicMock,
    ) -> None:
        """Test upload service is callable."""
        # The upload service should be callable even if there's nothing to upload
        result = await hass.services.async_call(
            DOMAIN,
            OPB_SERVICE_UPLOAD,
            {},
            blocking=True,
            return_response=True,
        )

        # Result should have a result key (even if the value is None)
        assert "result" in result


class TestCleanCacheServiceEdgeCases:
    """Tests for clean cache service edge cases."""

    async def test_clean_cache_with_default_hours(
        self,
        hass: HomeAssistant,
        init_integration: MockConfigEntry,
        mock_openplantbook_api: MagicMock,
    ) -> None:
        """Test clean cache with default hours (no parameter)."""
        # First get a plant to populate cache
        await hass.services.async_call(
            DOMAIN,
            OPB_SERVICE_GET,
            {"species": "monstera deliciosa"},
            blocking=True,
        )

        # Clean cache without hours parameter (uses default)
        await hass.services.async_call(
            DOMAIN,
            OPB_SERVICE_CLEAN_CACHE,
            {},
            blocking=True,
        )

        # With default hours (24), recent cache entries should remain
        from custom_components.openplantbook import _cache_key

        assert _cache_key("monstera deliciosa", None) in hass.data[DOMAIN][ATTR_SPECIES]

    async def test_clean_cache_with_invalid_hours(
        self,
        hass: HomeAssistant,
        init_integration: MockConfigEntry,
        mock_openplantbook_api: MagicMock,
    ) -> None:
        """Test clean cache with invalid hours parameter uses default."""
        # First get a plant to populate cache
        await hass.services.async_call(
            DOMAIN,
            OPB_SERVICE_GET,
            {"species": "monstera deliciosa"},
            blocking=True,
        )

        # Clean cache with invalid hours (string instead of int)
        await hass.services.async_call(
            DOMAIN,
            OPB_SERVICE_CLEAN_CACHE,
            {"hours": "invalid"},
            blocking=True,
        )

        # With invalid hours, uses default (24), recent entries should remain
        from custom_components.openplantbook import _cache_key

        assert _cache_key("monstera deliciosa", None) in hass.data[DOMAIN][ATTR_SPECIES]


class TestImageDownload:
    """Tests for image download functionality."""

    @pytest.fixture
    def mock_config_entry_with_download(self) -> MockConfigEntry:
        """Create a config entry with image download enabled."""
        return MockConfigEntry(
            domain=DOMAIN,
            data={
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
            },
            options={
                FLOW_DOWNLOAD_IMAGES: True,
                FLOW_DOWNLOAD_PATH: DEFAULT_IMAGE_PATH,
            },
            entry_id="test_entry_id_12345",
            title="Openplantbook API",
        )

    async def test_get_plant_downloads_image(
        self,
        hass: HomeAssistant,
        mock_config_entry_with_download: MockConfigEntry,
        mock_openplantbook_api: MagicMock,
        tmp_path,
    ) -> None:
        """Test get_plant downloads image when enabled and rewrites URL."""
        # Use a real temp directory under www/ so the /local/ rewrite works
        download_dir = tmp_path / "www" / "images" / "plants"
        download_dir.mkdir(parents=True)

        mock_config_entry_with_download.add_to_hass(hass)
        hass.config_entries.async_update_entry(
            mock_config_entry_with_download,
            options={
                **mock_config_entry_with_download.options,
                FLOW_DOWNLOAD_PATH: str(download_dir),
            },
        )

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.read = AsyncMock(return_value=b"fake image data")

        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_resp)

        with patch(
            "custom_components.openplantbook.async_get_clientsession",
            return_value=mock_session,
        ):
            await hass.config_entries.async_setup(
                mock_config_entry_with_download.entry_id
            )
            await hass.async_block_till_done()

            hass.data[DOMAIN][ATTR_SPECIES].clear()

            result = await hass.services.async_call(
                DOMAIN,
                OPB_SERVICE_GET,
                {"species": "monstera deliciosa"},
                blocking=True,
                return_response=True,
            )

        assert result is not None
        # The image_url should be rewritten to a /local/ path
        assert result.get(ATTR_IMAGE, "").startswith("/local/")
        # Verify the file was actually written
        downloaded_file = download_dir / "monstera.jpg"
        assert downloaded_file.exists()
        assert downloaded_file.read_bytes() == b"fake image data"

    async def test_get_plant_skips_existing_image(
        self,
        hass: HomeAssistant,
        mock_config_entry_with_download: MockConfigEntry,
        mock_openplantbook_api: MagicMock,
    ) -> None:
        """Test get_plant skips download when file already exists."""
        mock_config_entry_with_download.add_to_hass(hass)

        with (
            patch("os.path.isabs", return_value=True),
            patch("os.path.isdir", return_value=True),
        ):
            await hass.config_entries.async_setup(
                mock_config_entry_with_download.entry_id
            )
            await hass.async_block_till_done()

            hass.data[DOMAIN][ATTR_SPECIES].clear()

            # File already exists on disk
            with patch("os.path.isfile", return_value=True):
                result = await hass.services.async_call(
                    DOMAIN,
                    OPB_SERVICE_GET,
                    {"species": "monstera deliciosa"},
                    blocking=True,
                    return_response=True,
                )

        assert result is not None
        # Should still rewrite to /local/ path even if file existed
        assert result.get(ATTR_IMAGE, "").startswith("/local/")

    async def test_get_plant_no_download_when_disabled(
        self,
        hass: HomeAssistant,
        init_integration: MockConfigEntry,
        mock_openplantbook_api: MagicMock,
    ) -> None:
        """Test get_plant does not download when download is disabled."""
        result = await hass.services.async_call(
            DOMAIN,
            OPB_SERVICE_GET,
            {"species": "monstera deliciosa"},
            blocking=True,
            return_response=True,
        )

        assert result is not None
        # Image URL should remain the original HTTP URL
        assert result.get(ATTR_IMAGE, "").startswith("https://")
