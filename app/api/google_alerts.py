from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
import logging
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

router = APIRouter()

class GoogleAlertEntry(BaseModel):
    title: str
    link: HttpUrl
    published: str
    summary: Optional[str] = None
    source: Optional[str] = None

class GoogleAlertWebhookPayload(BaseModel):
    # This model is a placeholder. Google Alerts typically sends RSS feeds
    # which would be parsed, not a direct JSON payload like this.
    # The actual parsing logic will be implemented in the endpoint.
    pass

async def process_alert_entry(entry_data: GoogleAlertEntry):
    """Process a single Google Alert entry (e.g., store in DB, queue for further processing)."""
    logger.info(f"Processing Google Alert: {entry_data.title} from {entry_data.link}")
    # TODO: Implement actual storage to DB or queuing to Celery
    pass

@router.post("/google-alerts", summary="Receive Google Alerts via Webhook")
async def receive_google_alerts(request: Request, background_tasks: BackgroundTasks):
    """Receives Google Alert RSS feed via webhook, parses it, and queues entries for processing.

    This endpoint expects an XML payload, typically from a service like Zapier
    that converts Google Alert RSS feeds into a POST request.
    """
    try:
        body = await request.body()
        root = ET.fromstring(body.decode('utf-8'))

        # Google Alerts RSS namespace
        namespace = {'atom': 'http://www.w3.org/2005/Atom'}

        entries = []
        for entry in root.findall('atom:entry', namespace):
            title = entry.find('atom:title', namespace).text if entry.find('atom:title', namespace) is not None else "No Title"
            link_elem = entry.find('atom:link', namespace)
            link = link_elem.get('href') if link_elem is not None else ""
            published = entry.find('atom:published', namespace).text if entry.find('atom:published', namespace) is not None else ""
            summary = entry.find('atom:summary', namespace).text if entry.find('atom:summary', namespace) is not None else ""
            source_elem = entry.find('atom:source', namespace)
            source_title = source_elem.find('atom:title', namespace).text if source_elem is not None and source_elem.find('atom:title', namespace) is not None else None

            if link:
                try:
                    alert_entry = GoogleAlertEntry(
                        title=title,
                        link=link,
                        published=published,
                        summary=summary,
                        source=source_title
                    )
                    background_tasks.add_task(process_alert_entry, alert_entry)
                    entries.append(alert_entry)
                except Exception as e:
                    logger.error(f"Error parsing Google Alert entry: {e} - Data: {title}, {link}")
            else:
                logger.warning(f"Google Alert entry skipped due to missing link: {title}")

        logger.info(f"Received and queued {len(entries)} Google Alert entries.")
        return {"message": f"Successfully received and queued {len(entries)} Google Alert entries.", "queued_entries": [e.model_dump() for e in entries]}

    except ET.ParseError as e:
        logger.error(f"Failed to parse XML payload for Google Alerts: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid XML payload: {e}")
    except Exception as e:
        logger.error(f"Unexpected error receiving Google Alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
