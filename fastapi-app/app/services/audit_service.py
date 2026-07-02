"""Audit log - background task example, run via FastAPI's BackgroundTasks."""
import asyncio
import logging
import time

logger = logging.getLogger("fastapi_app.audit")

AUDIT_LOG = []


async def create_audit_log_entry(action: str, entity: str, entity_id: int):
    """Runs after the response has been sent to the client (FastAPI BackgroundTasks)."""
    await asyncio.sleep(0.5)  # simulate I/O e.g. writing to an external audit service
    entry = {"action": action, "entity": entity, "entity_id": entity_id, "ts": time.time()}
    AUDIT_LOG.append(entry)
    logger.info("Audit log recorded: %s", entry)
    return entry
