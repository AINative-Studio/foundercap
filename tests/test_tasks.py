import pytest
from unittest.mock import AsyncMock, patch

from app.worker.tasks import process_company_data
from app.core.snapshot import SnapshotService
from app.services.scraper.crunchbase import CrunchbaseScraper
from app.services.scraper.linkedin import LinkedInScraper
from app.services.updater.airtable import AirtableUpdater
from app.services.updater.zerodb import ZeroDBUpdater

@pytest.fixture
async def mock_services():
    with patch('app.core.service.get_service_instance') as mock_get_service_instance:
        mock_snapshot_service = AsyncMock(spec=SnapshotService)
        mock_crunchbase_scraper = AsyncMock(spec=CrunchbaseScraper)
        mock_linkedin_scraper = AsyncMock(spec=LinkedInScraper)
        mock_airtable_updater = AsyncMock(spec=AirtableUpdater)
        mock_zerodb_updater = AsyncMock(spec=ZeroDBUpdater)

        # Set return values for update and invalidate_cache on the mocks
        mock_airtable_updater.update.return_value = {"success": True}
        mock_zerodb_updater.update.return_value = {"success": True}
        mock_zerodb_updater.invalidate_cache.return_value = None

        # Mock the _initialize method for all services to set _is_initialized and _client
        async def mock_initialize_side_effect(service_mock):
            service_mock._is_initialized = True
            if hasattr(service_mock, '_client'):
                service_mock._client = object() # Simulate client being set

        mock_snapshot_service._initialize.side_effect = lambda: mock_initialize_side_effect(mock_snapshot_service)
        mock_crunchbase_scraper._initialize.side_effect = lambda: mock_initialize_side_effect(mock_crunchbase_scraper)
        mock_linkedin_scraper._initialize.side_effect = lambda: mock_initialize_side_effect(mock_linkedin_scraper)
        mock_airtable_updater._initialize.side_effect = lambda: mock_initialize_side_effect(mock_airtable_updater)
        mock_zerodb_updater._initialize.side_effect = lambda: mock_initialize_side_effect(mock_zerodb_updater)

        mock_get_service_instance.side_effect = [
            mock_snapshot_service,
            mock_crunchbase_scraper,
            mock_linkedin_scraper,
            mock_airtable_updater,
            mock_zerodb_updater,
        ]

        yield {
            "snapshot_service": mock_snapshot_service,
            "crunchbase_scraper": mock_crunchbase_scraper,
            "linkedin_scraper": mock_linkedin_scraper,
            "airtable_updater": mock_airtable_updater,
            "zerodb_updater": mock_zerodb_updater,
            "find_json_diff": MagicMock(name="find_json_diff_mock"),
        }


@pytest.mark.asyncio
async def test_process_company_data_new_entry(mock_services):
    company_id = "new_company_id"
    permalink = "new-company-permalink"

    mock_services["snapshot_service"].get_latest_snapshot.return_value = None
    mock_services["crunchbase_scraper"].scrape.return_value = {
        "data": {"name": "New Company", "funding": 1000000}
    }
    mock_services["linkedin_scraper"].scrape.return_value = {
        "data": {"employees": 50, "website": "http://new.com"}
    }
    mock_services["find_json_diff"].return_value = {"name": (None, "New Company")}

    result = await process_company_data(company_id, permalink=permalink)

    mock_services["snapshot_service"].get_latest_snapshot.assert_called_once_with(company_id)
    mock_services["crunchbase_scraper"].scrape.assert_called_once_with(company_id, permalink=permalink)
    mock_services["linkedin_scraper"].scrape.assert_called_once_with(company_id)
    mock_services["find_json_diff"].assert_called_once()
    mock_services["airtable_updater"].update.assert_called_once()
    mock_services["zerodb_updater"].update.assert_called_once()
    mock_services["snapshot_service"].save_snapshot.assert_called_once()
    mock_services["zerodb_updater"].invalidate_cache.assert_called_once_with([company_id])

    assert result["company_id"] == company_id
    assert result["status"] == "updated"
    assert "changes" in result


@pytest.mark.asyncio
async def test_process_company_data_no_changes(mock_services):
    company_id = "existing_company_id"
    old_data = {"name": "Existing Company", "funding": 500000}

    mock_services["snapshot_service"].get_latest_snapshot.return_value = old_data
    mock_services["crunchbase_scraper"].scrape.return_value = {
        "data": {"name": "Existing Company", "funding": 500000}
    }
    mock_services["linkedin_scraper"].scrape.return_value = {
        "data": {"employees": 30, "website": "http://existing.com"}
    }
    mock_services["find_json_diff"].return_value = {}

    result = await process_company_data(company_id)

    mock_services["snapshot_service"].get_latest_snapshot.assert_called_once_with(company_id)
    mock_services["crunchbase_scraper"].scrape.assert_called_once_with(company_id, permalink=None)
    mock_services["linkedin_scraper"].scrape.assert_called_once_with(company_id)
    mock_services["find_json_diff"].assert_called_once()
    mock_services["airtable_updater"].update.assert_not_called()
    mock_services["zerodb_updater"].update.assert_not_called()
    mock_services["snapshot_service"].save_snapshot.assert_not_called()
    mock_services["zerodb_updater"].invalidate_cache.assert_not_called()

    assert result["company_id"] == company_id
    assert result["status"] == "no_changes"
    assert result["changes"] == {}


@pytest.mark.asyncio
async def test_process_company_data_with_changes(mock_services):
    company_id = "changed_company_id"
    old_data = {"name": "Old Name", "funding": 1000000}
    new_scraped_data = {"name": "New Name", "funding": 2000000, "employees": 75}
    detected_changes = {"name": ("Old Name", "New Name"), "funding": (1000000, 2000000)}

    mock_services["snapshot_service"].get_latest_snapshot.return_value = old_data
    mock_services["crunchbase_scraper"].scrape.return_value = {"data": new_scraped_data}
    mock_services["linkedin_scraper"].scrape.return_value = {"data": {"employees": 75}}
    mock_services["find_json_diff"].return_value = detected_changes

    result = await process_company_data(company_id)

    mock_services["snapshot_service"].get_latest_snapshot.assert_called_once_with(company_id)
    mock_services["crunchbase_scraper"].scrape.assert_called_once_with(company_id, permalink=None)
    mock_services["linkedin_scraper"].scrape.assert_called_once_with(company_id)
    mock_services["find_json_diff"].assert_called_once()
    mock_services["airtable_updater"].update.assert_called_once()
    mock_services["zerodb_updater"].update.assert_called_once()
    mock_services["snapshot_service"].save_snapshot.assert_called_once()
    mock_services["zerodb_updater"].invalidate_cache.assert_called_once_with([company_id])

    assert result["company_id"] == company_id
    assert result["status"] == "updated"
    assert result["changes"] == detected_changes


@pytest.mark.asyncio
async def test_process_company_data_scraper_error(mock_services):
    company_id = "error_company_id"

    mock_services["snapshot_service"].get_latest_snapshot.return_value = None
    mock_services["crunchbase_scraper"].scrape.side_effect = Exception("Scraper failed")

    with pytest.raises(Exception, match="Scraper failed"):
        await process_company_data(company_id)

    mock_services["airtable_updater"].update.assert_not_called()
    mock_services["zerodb_updater"].update.assert_not_called()
    mock_services["snapshot_service"].save_snapshot.assert_not_called()
    mock_services["zerodb_updater"].invalidate_cache.assert_not_called()