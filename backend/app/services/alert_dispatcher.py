"""Multi-channel alert dispatcher — webhooks, email, WebSocket, SMS.

Routes alerts based on alert configurations and handles retries.
"""

import asyncio
import logging
import smtplib
from datetime import UTC, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

SEVERITY_ORDER = {"minor": 0, "moderate": 1, "severe": 2, "critical": 3}


class AlertDispatcher:
    """Dispatches alerts across multiple channels with rate limiting and retries."""

    def __init__(self):
        self._last_sent: dict[str, datetime] = {}  # recipient -> last sent time
        self._http_client: httpx.AsyncClient | None = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=10)
        return self._http_client

    async def close(self) -> None:
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.close()

    async def dispatch(
        self,
        incident: dict,
        config: dict,
        report_summary: str | None = None,
    ) -> dict:
        """Send an alert based on the config. Returns alert record."""
        channel = config["channel"]
        recipient = config["recipient"]

        # Build payload
        payload = self._build_payload(incident, report_summary)

        result = {
            "incident_id": incident["id"],
            "channel": channel,
            "recipient": recipient,
            "payload": payload,
            "status": "pending",
            "sent_at": None,
            "error_message": None,
        }

        try:
            if channel == "webhook":
                await self._send_webhook(recipient, payload)
            elif channel == "email":
                await self._send_email(recipient, incident, report_summary)
            elif channel == "websocket":
                # WebSocket alerts are handled by the broadcast function
                from app.api.v1.websocket import broadcast
                await broadcast({"type": "incident.new", "data": payload})
            elif channel == "sms":
                await self._send_sms(recipient, incident)
            else:
                raise ValueError(f"Unknown channel: {channel}")

            result["status"] = "sent"
            result["sent_at"] = datetime.now(UTC).isoformat()
            self._last_sent[recipient] = datetime.now(UTC)
            logger.info("Alert sent via %s to %s for incident %s", channel, recipient, incident["id"])

        except Exception as e:
            result["status"] = "failed"
            result["error_message"] = str(e)
            logger.error("Alert failed (%s → %s): %s", channel, recipient, e)

        return result

    def should_alert(self, config: dict, incident: dict) -> bool:
        """Check if an alert should be sent based on config rules."""
        # Check severity threshold
        incident_sev = SEVERITY_ORDER.get(incident.get("severity", "minor"), 0)
        min_sev = SEVERITY_ORDER.get(config.get("min_severity", "moderate"), 1)
        if incident_sev < min_sev:
            return False

        # Check incident type filter
        allowed_types = config.get("incident_types", ["crash"])
        if incident.get("incident_type") not in allowed_types:
            return False

        # Check interstate filter
        allowed_interstates = config.get("interstates")
        if allowed_interstates and incident.get("interstate") not in allowed_interstates:
            return False

        # Check cooldown
        recipient = config["recipient"]
        last = self._last_sent.get(recipient)
        if last:
            cooldown = config.get("cooldown_minutes", 5)
            elapsed = (datetime.now(UTC) - last).total_seconds() / 60
            if elapsed < cooldown:
                return False

        return True

    def _build_payload(self, incident: dict, report_summary: str | None = None) -> dict:
        """Build alert payload from incident data."""
        return {
            "incident_id": incident["id"],
            "type": incident.get("incident_type", "unknown"),
            "severity": incident.get("severity", "unknown"),
            "confidence": incident.get("confidence", 0),
            "location": {
                "interstate": incident.get("interstate"),
                "direction": incident.get("direction"),
                "latitude": incident.get("latitude"),
                "longitude": incident.get("longitude"),
            },
            "detected_at": incident.get("detected_at"),
            "vehicle_count": incident.get("vehicle_count"),
            "summary": report_summary,
        }

    async def _send_webhook(self, url: str, payload: dict, retries: int = 3) -> None:
        """POST JSON payload to a webhook URL with retry."""
        client = await self._get_http_client()
        for attempt in range(retries):
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return
            except Exception as e:
                if attempt == retries - 1:
                    raise
                wait = 2 ** attempt
                logger.warning("Webhook attempt %d failed, retrying in %ds: %s", attempt + 1, wait, e)
                await asyncio.sleep(wait)

    async def _send_email(self, recipient: str, incident: dict, summary: str | None) -> None:
        """Send an alert email via SMTP."""
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.warning("SMTP not configured, skipping email alert")
            return

        msg = MIMEMultipart("alternative")
        severity = incident.get('severity', '').upper()
        inc_type = incident.get('incident_type', 'incident')
        road = incident.get('interstate', 'unknown')
        msg["Subject"] = f"[ACRAS] {severity} {inc_type} on {road}"
        msg["From"] = settings.SMTP_USER
        msg["To"] = recipient

        text_body = summary or f"Incident detected on {incident.get('interstate')}"
        msg.attach(MIMEText(text_body, "plain"))

        # Run SMTP in thread to avoid blocking
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._smtp_send, msg)

    def _smtp_send(self, msg: MIMEMultipart) -> None:
        """Synchronous SMTP send."""
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

    async def _send_sms(self, phone: str, incident: dict) -> None:
        """Send SMS via Twilio (if configured)."""
        if not settings.TWILIO_ACCOUNT_SID:
            logger.warning("Twilio not configured, skipping SMS alert")
            return

        body = (
            f"ACRAS Alert: {incident.get('severity', '').upper()} "
            f"{incident.get('incident_type', 'incident')} detected on "
            f"{incident.get('interstate', 'unknown')} at "
            f"{incident.get('detected_at', 'unknown time')}"
        )

        client = await self._get_http_client()
        await client.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json",
            auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
            data={"From": settings.TWILIO_FROM_NUMBER, "To": phone, "Body": body},
        )
