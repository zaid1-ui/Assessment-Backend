"""FastAPI application entrypoint."""
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import get_settings
from app.database import init_db
from app.utils.logger import configure_logging
from app.routers import users, projects, tasks, comments, reports

settings = get_settings()
logger = configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up FastAPI app (env=%s)", settings.app_env)
    await init_db()
    yield
    logger.info("Shutting down FastAPI app")


app = FastAPI(title="Task Management API (FastAPI)", version="1.0.0", lifespan=lifespan)

app.include_router(users.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(comments.router)
app.include_router(reports.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s", request.url.path)
    return JSONResponse(status_code=500, content={"success": False, "message": "Internal server error"})
