import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
...
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.database import Base, get_db
from app.dependencies import get_auth_service
from app.services.auth_service import AuthService
import main as main_module

TEST_DB_URL = "sqlite+aiosqlite:///file:memdb_test?mode=memory&cache=shared&uri=true"

engine = create_async_engine(TEST_DB_URL, future=True)
TestSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


def override_get_auth_service():
    return AuthService(secret_key="test-secret")


main_module.app.dependency_overrides[get_db] = override_get_db
main_module.app.dependency_overrides[get_auth_service] = override_get_auth_service


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture()
async def client():
    transport = ASGITransport(app=main_module.app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
