import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import xml.etree.ElementTree as ET

from app.main import app

client = TestClient(app)

@pytest.fixture
def mock_process_alert_entry():
    with patch("app.api.google_alerts.process_alert_entry", new_callable=AsyncMock) as mock:
        yield mock

def test_receive_google_alerts_success(mock_process_alert_entry):
    xml_payload = """
    <feed xmlns="http://www.w3.org/2005/Atom">
        <title>Google Alert - test company</title>
        <link href="https://www.google.com/alerts/feeds/test" rel="self"/>
        <updated>2025-06-29T12:00:00Z</updated>
        <entry>
            <title type="html">Test Company raises $10M</title>
            <link href="http://example.com/news/1" rel="alternate" type="text/html"/>
            <published>2025-06-29T11:00:00Z</published>
            <updated>2025-06-29T11:00:00Z</updated>
            <summary type="html">Summary of the news.</summary>
            <source>
                <title>News Source A</title>
            </source>
        </entry>
        <entry>
            <title type="html">Another Test Company article</title>
            <link href="http://example.com/news/2" rel="alternate" type="text/html"/>
            <published>2025-06-29T10:00:00Z</published>
            <updated>2025-06-29T10:00:00Z</updated>
            <summary type="html">Another summary.</summary>
            <source>
                <title>News Source B</title>
            </source>
        </entry>
    </feed>
    """

    response = client.post(
        "/api/v1/google-alerts",
        headers={'Content-Type': 'application/xml'},
        content=xml_payload.encode('utf-8')
    )

    assert response.status_code == 200
    assert response.json()["message"].startswith("Successfully received and queued")
    assert len(response.json()["queued_entries"]) == 2
    mock_process_alert_entry.assert_called()

def test_receive_google_alerts_invalid_xml():
    invalid_xml_payload = "<invalid_xml>"

    response = client.post(
        "/api/v1/google-alerts",
        headers={'Content-Type': 'application/xml'},
        content=invalid_xml_payload.encode('utf-8')
    )

    assert response.status_code == 400
    assert "Invalid XML payload" in response.json()["detail"]

def test_receive_google_alerts_missing_link():
    xml_payload_missing_link = """
    <feed xmlns="http://www.w3.org/2005/Atom">
        <title>Google Alert - test company</title>
        <link href="https://www.google.com/alerts/feeds/test" rel="self"/>
        <updated>2025-06-29T12:00:00Z</updated>
        <entry>
            <title type="html">Test Company raises $10M</title>
            <published>2025-06-29T11:00:00Z</published>
            <updated>2025-06-29T11:00:00Z</updated>
            <summary type="html">Summary of the news.</summary>
            <source>
                <title>News Source A</title>
            </source>
        </entry>
    </feed>
    """

    response = client.post(
        "/api/v1/google-alerts",
        headers={'Content-Type': 'application/xml'},
        content=xml_payload_missing_link.encode('utf-8')
    )

    assert response.status_code == 200
    assert "Successfully received and queued 0 Google Alert entries." in response.json()["message"]
    assert len(response.json()["queued_entries"]) == 0

