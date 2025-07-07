"""
Data Pipeline Service

Orchestrates the complete data flow for FounderCap:
1. Scrapes data from LinkedIn and Crunchbase
2. Detects changes using snapshots and diff engine
3. Updates Airtable and ZeroDB
4. Handles caching and error recovery
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.snapshot import SnapshotService
from app.core.diff import find_json_diff
from app.services.linkedin.service import LinkedInService
from app.services.crunchbase.service import CrunchbaseService
from app.services.updater.airtable import AirtableUpdater
from app.services.updater.zerodb import ZeroDBUpdater
from app.models.company import Company

logger = logging.getLogger(__name__)


class DataPipelineService:
    """Main data pipeline service for processing company data."""
    
    def __init__(self):
        """Initialize the data pipeline service."""
        self.snapshot_service = SnapshotService()
        self.linkedin_service = None
        self.crunchbase_service = None
        self.airtable_updater = AirtableUpdater()
        self.zerodb_updater = ZeroDBUpdater()
        self._processing_lock = asyncio.Lock()
        self._active_processes: Set[str] = set()
        
    async def initialize(self):
        """Initialize all services."""
        logger.info("Initializing data pipeline...")
        
        await self.snapshot_service._initialize()
        await self.airtable_updater._initialize()
        await self.zerodb_updater._initialize()
        
        logger.info("Data pipeline initialized successfully")
    
    async def shutdown(self):
        """Shutdown all services."""
        logger.info("Shutting down data pipeline...")
        
        await self.snapshot_service._shutdown()
        await self.airtable_updater._shutdown()
        await self.zerodb_updater._shutdown()
        
        if self.linkedin_service:
            await self.linkedin_service._close_scraper()
        if self.crunchbase_service:
            await self.crunchbase_service.close()
            
        logger.info("Data pipeline shut down successfully")
    
    async def process_company(
        self, 
        company_name: str, 
        company_domain: Optional[str] = None,
        force_update: bool = False
    ) -> Dict[str, Any]:
        """Process a single company through the complete data pipeline.
        
        Args:
            company_name: Name of the company to process
            company_domain: Optional domain for enhanced Crunchbase lookup
            force_update: If True, bypasses caching and forces fresh data fetch
            
        Returns:
            Dictionary containing processing results and any changes detected
        """
        company_key = company_domain or company_name.lower().replace(" ", "-")
        
        async with self._processing_lock:
            if company_key in self._active_processes:
                logger.warning(f"Company {company_name} is already being processed")
                return {"status": "already_processing", "company": company_name}
            
            self._active_processes.add(company_key)
        
        try:
            logger.info(f"Starting pipeline processing for company: {company_name}")
            
            # Step 1: Get current snapshot
            current_snapshot = await self.snapshot_service.get_latest_snapshot(company_key)
            
            # Step 2: Collect fresh data from all sources
            fresh_data = await self._collect_company_data(company_name, company_domain, force_update)
            
            if not fresh_data:
                logger.warning(f"No data collected for company: {company_name}")
                return {"status": "no_data", "company": company_name}
            
            # Step 3: Detect changes
            changes = {}
            if current_snapshot and not force_update:
                changes = find_json_diff(current_snapshot, fresh_data)
                
                if not changes:
                    logger.info(f"No changes detected for company: {company_name}")
                    return {
                        "status": "no_changes",
                        "company": company_name,
                        "last_updated": current_snapshot.get("metadata", {}).get("last_updated")
                    }
            
            # Step 4: Process the data through updaters
            update_results = await self._update_data_stores(company_key, fresh_data, changes)
            
            # Step 5: Save new snapshot
            fresh_data["metadata"] = {
                "last_updated": datetime.utcnow().isoformat(),
                "changes_detected": len(changes),
                "processing_time": datetime.utcnow().isoformat()
            }
            await self.snapshot_service.save_snapshot(company_key, fresh_data)
            
            return {
                "status": "success",
                "company": company_name,
                "changes_count": len(changes),
                "changes": changes,
                "update_results": update_results,
                "data": fresh_data
            }
            
        except Exception as e:
            logger.error(f"Error processing company {company_name}: {e}", exc_info=True)
            return {
                "status": "error",
                "company": company_name,
                "error": str(e)
            }
        finally:
            self._active_processes.discard(company_key)
    
    async def _collect_company_data(
        self, 
        company_name: str, 
        company_domain: Optional[str] = None,
        force_update: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Collect data from all sources (LinkedIn, Crunchbase)."""
        logger.info(f"Collecting data for company: {company_name}")
        
        # Initialize services
        if not self.linkedin_service:
            self.linkedin_service = LinkedInService()
        if not self.crunchbase_service:
            self.crunchbase_service = CrunchbaseService()
        
        collected_data = {
            "name": company_name,
            "domain": company_domain,
            "linkedin_data": None,
            "crunchbase_data": None,
            "sources": [],
            "collection_timestamp": datetime.utcnow().isoformat()
        }
        
        # Collect LinkedIn data
        try:
            async with self.linkedin_service:
                linkedin_data = await self.linkedin_service.get_company_info(
                    company_name, 
                    use_cache=not force_update
                )
                if linkedin_data:
                    collected_data["linkedin_data"] = linkedin_data
                    collected_data["sources"].append("linkedin")
                    logger.info(f"LinkedIn data collected for {company_name}")
        except Exception as e:
            logger.error(f"Error collecting LinkedIn data for {company_name}: {e}")
        
        # Collect Crunchbase data
        try:
            if company_domain:
                crunchbase_data = await self.crunchbase_service.get_company_by_domain(
                    company_domain,
                    use_cache=not force_update
                )
            else:
                # Try to find by company name in Crunchbase
                search_results = await self.crunchbase_service.search_companies(
                    company_name,
                    limit=1,
                    use_cache=not force_update
                )
                crunchbase_data = search_results.get("results", [{}])[0] if search_results.get("results") else None
            
            if crunchbase_data:
                collected_data["crunchbase_data"] = crunchbase_data
                collected_data["sources"].append("crunchbase")
                logger.info(f"Crunchbase data collected for {company_name}")
        except Exception as e:
            logger.error(f"Error collecting Crunchbase data for {company_name}: {e}")
        
        # Merge and normalize data
        if collected_data["sources"]:
            normalized_data = self._normalize_company_data(collected_data)
            return normalized_data
        
        return None
    
    def _normalize_company_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize data from different sources into a unified format."""
        normalized = {
            "name": raw_data.get("name"),
            "domain": raw_data.get("domain"),
            "description": None,
            "website": None,
            "linkedin_url": None,
            "crunchbase_url": None,
            "founded_year": None,
            "employee_count": None,
            "industry": None,
            "funding_stage": None,
            "total_funding": None,
            "last_funding_date": None,
            "location": {
                "city": None,
                "state": None,
                "country": None
            },
            "funding_rounds": [],
            "sources": raw_data.get("sources", []),
            "raw_data": raw_data
        }
        
        # Extract from LinkedIn data
        linkedin_data = raw_data.get("linkedin_data")
        if linkedin_data:
            normalized.update({
                "description": linkedin_data.get("description") or linkedin_data.get("headline"),
                "website": linkedin_data.get("website"),
                "linkedin_url": linkedin_data.get("linkedin_url"),
                "employee_count": self._parse_employee_count(linkedin_data.get("company_size")),
                "industry": linkedin_data.get("industry"),
                "location": {
                    "city": linkedin_data.get("headquarters", "").split(",")[0].strip() if linkedin_data.get("headquarters") else None,
                    "state": None,
                    "country": None
                }
            })
            
            if linkedin_data.get("founded"):
                try:
                    normalized["founded_year"] = int(linkedin_data["founded"])
                except (ValueError, TypeError):
                    pass
        
        # Extract from Crunchbase data
        crunchbase_data = raw_data.get("crunchbase_data")
        if crunchbase_data:
            company_info = crunchbase_data.get("company", {})
            funding_rounds = crunchbase_data.get("funding_rounds", [])
            
            # Prefer Crunchbase data for financial information
            normalized.update({
                "description": normalized["description"] or company_info.get("description"),
                "website": normalized["website"] or company_info.get("website"),
                "crunchbase_url": company_info.get("crunchbase_url"),
                "founded_year": normalized["founded_year"] or company_info.get("founded_year"),
                "total_funding": company_info.get("total_funding_usd"),
                "last_funding_date": company_info.get("last_funding_date"),
                "funding_rounds": funding_rounds
            })
            
            # Extract location from Crunchbase
            location = company_info.get("location", {})
            if location:
                normalized["location"].update({
                    "city": location.get("city"),
                    "state": location.get("region"),
                    "country": location.get("country")
                })
            
            # Determine funding stage from latest round
            if funding_rounds:
                latest_round = max(funding_rounds, key=lambda x: x.get("announced_date", ""))
                normalized["funding_stage"] = latest_round.get("round_type")
        
        return normalized
    
    def _parse_employee_count(self, company_size_str: Optional[str]) -> Optional[int]:
        """Parse employee count from LinkedIn company size string."""
        if not company_size_str:
            return None
        
        # Handle ranges like "11-50 employees"
        size_str = company_size_str.lower().replace("employees", "").replace("employee", "").strip()
        
        if "-" in size_str:
            try:
                # Take the upper bound of the range
                parts = size_str.split("-")
                return int(parts[1].replace(",", "").strip())
            except (ValueError, IndexError):
                pass
        
        # Handle single numbers
        try:
            return int(size_str.replace(",", "").strip())
        except ValueError:
            pass
        
        # Handle special cases
        if "10,000+" in size_str or "10000+" in size_str:
            return 10000
        elif "1,000+" in size_str or "1000+" in size_str:
            return 1000
        elif "500+" in size_str:
            return 500
        
        return None
    
    async def _update_data_stores(
        self, 
        company_key: str, 
        data: Dict[str, Any], 
        changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update all data stores (Airtable, ZeroDB) with the new data."""
        update_results = {}
        
        # Update Airtable
        try:
            airtable_result = await self.airtable_updater.update(company_key, data)
            update_results["airtable"] = {
                "status": "success",
                "result": airtable_result
            }
            logger.info(f"Successfully updated Airtable for {company_key}")
        except Exception as e:
            logger.error(f"Error updating Airtable for {company_key}: {e}")
            update_results["airtable"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Update ZeroDB
        try:
            zerodb_result = await self.zerodb_updater.update(company_key, data)
            update_results["zerodb"] = {
                "status": "success", 
                "result": zerodb_result
            }
            logger.info(f"Successfully updated ZeroDB for {company_key}")
        except Exception as e:
            logger.error(f"Error updating ZeroDB for {company_key}: {e}")
            update_results["zerodb"] = {
                "status": "error",
                "error": str(e)
            }
        
        return update_results
    
    async def process_companies_batch(
        self, 
        companies: List[Dict[str, str]], 
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """Process multiple companies concurrently.
        
        Args:
            companies: List of dicts with 'name' and optional 'domain' keys
            max_concurrent: Maximum number of concurrent processes
            
        Returns:
            List of processing results for each company
        """
        logger.info(f"Processing batch of {len(companies)} companies")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_single(company_info):
            async with semaphore:
                return await self.process_company(
                    company_info["name"],
                    company_info.get("domain")
                )
        
        tasks = [process_single(company) for company in companies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "status": "error",
                    "company": companies[i]["name"],
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        logger.info(f"Batch processing completed: {len(processed_results)} results")
        return processed_results
    
    async def get_pipeline_status(self) -> Dict[str, Any]:
        """Get the current status of the data pipeline."""
        snapshot_health = await self.snapshot_service.health_check()
        
        return {
            "pipeline_status": "active",
            "active_processes": len(self._active_processes),
            "currently_processing": list(self._active_processes),
            "services": {
                "snapshot_service": snapshot_health,
                "linkedin_service": "initialized" if self.linkedin_service else "not_initialized",
                "crunchbase_service": "initialized" if self.crunchbase_service else "not_initialized",
                "airtable_updater": "initialized",
                "zerodb_updater": "initialized"
            },
            "timestamp": datetime.utcnow().isoformat()
        }


# Global pipeline instance
_pipeline_instance = None

def get_pipeline() -> DataPipelineService:
    """Get the global pipeline instance."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = DataPipelineService()
    return _pipeline_instance