"""Best-effort Redis telemetry publisher; local WebSocket delivery remains authoritative."""
import json
import logging
import os
from server.observability.metrics import REDIS_PUBLISH_FAILURES

logger = logging.getLogger(__name__)

class TelemetryPublisher:
    def __init__(self):
        self.url = os.getenv("RACE_REDIS_URL")
        self.client = None

    async def start(self):
        if not self.url:
            return False
        try:
            from redis.asyncio import Redis
            self.client = Redis.from_url(self.url, decode_responses=True, socket_connect_timeout=1)
            await self.client.ping()
            return True
        except Exception:
            logger.exception("Redis unavailable; using in-process telemetry")
            self.client = None
            return False

    async def publish(self, session_id, payload):
        if not self.client:
            return
        try:
            await self.client.publish(f"race:simulation:{session_id}", json.dumps(payload, separators=(",", ":")))
        except Exception:
            REDIS_PUBLISH_FAILURES.inc()
            logger.exception("Redis telemetry publish failed")

    async def close(self):
        if self.client:
            await self.client.aclose()
            self.client = None
