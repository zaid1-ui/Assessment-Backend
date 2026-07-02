"""Simple background task runner for Flask (thread-based).

Flask has no first-class background task primitive like FastAPI's
BackgroundTasks, so we implement a lightweight thread pool executor.
In production this would typically be replaced with Celery / RQ.
"""
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger("flask_app.background")

_executor = ThreadPoolExecutor(max_workers=4)


def run_in_background(func, *args, **kwargs):
    logger.info("Scheduling background task: %s", func.__name__)

    def _wrapped():
        try:
            func(*args, **kwargs)
            logger.info("Background task completed: %s", func.__name__)
        except Exception:
            logger.exception("Background task failed: %s", func.__name__)

    return _executor.submit(_wrapped)
