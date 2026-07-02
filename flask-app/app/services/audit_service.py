"""Audit log - background task example (Email Notification / Audit Log Creation)."""
import logging
import time

logger = logging.getLogger("flask_app.audit")

# In-memory audit log store for demo purposes (would be a DB table / external
# service in a real system).
AUDIT_LOG = []


def create_audit_log_entry(action: str, entity: str, entity_id: int):
    """Simulates writing an audit entry + notifying, run off the request thread."""
    time.sleep(0.5)  # simulate I/O (e.g. writing to an external audit service)
    entry = {"action": action, "entity": entity, "entity_id": entity_id, "ts": time.time()}
    AUDIT_LOG.append(entry)
    logger.info("Audit log recorded: %s", entry)
    return entry
