import logging
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.services.updater.base import BaseUpdater

logger = logging.getLogger(__name__)


class ZeroDBUpdater(BaseUpdater):
    """Updater for ZeroDB company data using JWT authentication and project-scoped endpoints."""

    def __init__(self):
        """Initialize the ZeroDB updater."""
        super().__init__()
        self._client: Optional[httpx.AsyncClient] = None
        self._jwt_token: Optional[str] = None
        self._project_id: Optional[str] = None

    @property
    def name(self) -> str:
        """Return the name of the updater."""
        return "zerodb"

    async def _authenticate(self) -> str:
        """Authenticate with ZeroDB and get JWT token.
        
        Returns:
            JWT access token.
            
        Raises:
            ValueError: If authentication credentials are missing.
            httpx.HTTPError: If authentication fails.
        """
        if not settings.ZERODB_EMAIL or not settings.ZERODB_PASSWORD:
            raise ValueError("ZERODB_EMAIL and ZERODB_PASSWORD are required")

        auth_client = httpx.AsyncClient(
            base_url=settings.ZERODB_API_URL,
            timeout=30.0,
        )
        
        try:
            response = await auth_client.post(
                "/auth/",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "username": settings.ZERODB_EMAIL,
                    "password": settings.ZERODB_PASSWORD,
                }
            )
            response.raise_for_status()
            auth_data = response.json()
            logger.info("Successfully authenticated with ZeroDB")
            return auth_data["access_token"]
        except httpx.HTTPStatusError as e:
            logger.error(f"Authentication failed: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error during authentication: {e}")
            raise
        finally:
            await auth_client.aclose()

    async def _ensure_project(self) -> str:
        """Ensure a ZeroDB project exists for this application.
        
        Returns:
            Project ID.
            
        Raises:
            RuntimeError: If client is not initialized.
            httpx.HTTPError: If project operations fail.
        """
        if not self._client:
            raise RuntimeError("ZeroDB client not initialized")

        # Try to list existing projects first
        try:
            response = await self._client.get("/projects/")
            response.raise_for_status()
            projects = response.json()
            
            # Look for existing FounderCap project
            for project in projects:
                if project.get("name") == "FounderCap":
                    logger.info(f"Found existing FounderCap project: {project['id']}")
                    return project["id"]
            
            # Create new project if none exists
            response = await self._client.post(
                "/projects/",
                json={
                    "name": "FounderCap",
                    "description": "Startup Funding Tracker & Dashboard Automation"
                }
            )
            response.raise_for_status()
            project = response.json()
            logger.info(f"Created new FounderCap project: {project['id']}")
            return project["id"]
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Project management failed: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error during project management: {e}")
            raise

    async def _ensure_database_enabled(self) -> None:
        """Ensure ZeroDB is enabled for the project.
        
        Raises:
            RuntimeError: If client is not initialized.
            httpx.HTTPError: If database operations fail.
        """
        if not self._client or not self._project_id:
            raise RuntimeError("ZeroDB client and project not initialized")

        try:
            # Check if database is already enabled
            response = await self._client.get(f"/projects/{self._project_id}/database")
            response.raise_for_status()
            db_status = response.json()
            
            if db_status.get("enabled"):
                logger.info("ZeroDB already enabled for project")
                return
            
            # Enable database
            response = await self._client.post(f"/projects/{self._project_id}/database")
            response.raise_for_status()
            logger.info("Successfully enabled ZeroDB for project")
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Database setup failed: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error during database setup: {e}")
            raise

    async def _initialize(self) -> None:
        """Initialize the ZeroDB updater with JWT authentication."""
        if not settings.ZERODB_API_URL:
            raise ValueError("ZERODB_API_URL is required")

        # Authenticate and get JWT token
        self._jwt_token = await self._authenticate()

        # Initialize client with JWT authentication
        self._client = httpx.AsyncClient(
            base_url=settings.ZERODB_API_URL,
            headers={
                "Authorization": f"Bearer {self._jwt_token}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

        # Ensure project exists and database is enabled
        self._project_id = await self._ensure_project()
        await self._ensure_database_enabled()
        
        logger.info(f"ZeroDB updater initialized with project: {self._project_id}")

    async def _shutdown(self) -> None:
        """Shut down the ZeroDB updater."""
        if self._client:
            await self._client.aclose()
            self._client = None
        self._jwt_token = None
        self._project_id = None
        logger.info("ZeroDB updater shut down")

    def _transform_company_data(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform company data to ZeroDB schema format.
        
        Args:
            company_data: Raw company data from internal models.
            
        Returns:
            Transformed data suitable for ZeroDB storage.
        """
        # Transform the company data to match ZeroDB expectations
        transformed = {
            "company_id": company_data.get("id"),
            "name": company_data.get("name"),
            "description": company_data.get("description"),
            "website": company_data.get("website"),
            "linkedin_url": company_data.get("linkedin_url"),
            "crunchbase_url": company_data.get("crunchbase_url"),
            "location": {
                "city": company_data.get("city"),
                "state": company_data.get("state"),
                "country": company_data.get("country"),
            },
            "financial": {
                "valuation": company_data.get("valuation"),
                "funding_stage": company_data.get("funding_stage"),
                "total_funding": company_data.get("total_funding"),
                "last_funding_date": company_data.get("last_funding_date"),
                "employee_count": company_data.get("employee_count"),
                "revenue": company_data.get("revenue"),
            },
            "metadata": {
                "industry": company_data.get("industry"),
                "founded_year": company_data.get("founded_year"),
                "tags": company_data.get("tags", []),
                "last_updated": company_data.get("updated_at"),
                "data_sources": company_data.get("data_sources", []),
            }
        }
        
        # Remove None values
        return {k: v for k, v in transformed.items() if v is not None}

    async def update(self, company_id: str, data: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """Store/update company data in ZeroDB.

        Args:
            company_id: The ID of the company to update.
            data: The company data to store.
            **kwargs: Additional arguments.

        Returns:
            A dictionary containing the storage result.

        Raises:
            RuntimeError: If updater is not initialized.
            httpx.HTTPError: If API request fails.
        """
        if not self._client or not self._project_id:
            raise RuntimeError("ZeroDB updater not initialized")

        try:
            # Transform data for ZeroDB
            transformed_data = self._transform_company_data(data)
            
            # Store as memory record for semantic search
            memory_payload = {
                "content": f"Company: {data.get('name', 'Unknown')} - {data.get('description', '')}",
                "agent_id": "foundercap-system",
                "session_id": f"company-{company_id}",
                "role": "system",
                "metadata": transformed_data
            }
            
            response = await self._client.post(
                f"/projects/{self._project_id}/database/memory/store",
                json=memory_payload
            )
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Successfully stored company {company_id} in ZeroDB")
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error storing company {company_id}: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error storing company {company_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error storing company {company_id}: {e}")
            raise

    async def search_companies(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for companies using semantic search.
        
        Args:
            query: Search query.
            limit: Maximum number of results.
            
        Returns:
            List of matching companies with similarity scores.
        """
        if not self._client or not self._project_id:
            raise RuntimeError("ZeroDB updater not initialized")

        try:
            search_payload = {
                "query": query,
                "agent_id": "foundercap-system",
                "limit": limit
            }
            
            response = await self._client.post(
                f"/projects/{self._project_id}/database/memory/search",
                json=search_payload
            )
            response.raise_for_status()
            results = response.json()
            
            logger.info(f"Found {len(results)} companies matching query: {query}")
            return results
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error searching companies: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error searching companies: {e}")
            raise

    async def invalidate_cache(self, company_ids: List[str]) -> Dict[str, Any]:
        """Invalidate cached entries for companies in ZeroDB.

        Args:
            company_ids: A list of company IDs whose cache entries should be invalidated.

        Returns:
            A dictionary containing the cache invalidation result.

        Note:
            ZeroDB handles caching internally, so this is a no-op for compatibility.
        """
        logger.info(f"Cache invalidation requested for {len(company_ids)} companies")
        return {"success": True, "message": "ZeroDB handles caching internally"}
