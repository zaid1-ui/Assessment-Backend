"""Pagination helper for async SQLAlchemy queries."""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession


async def paginate(db: AsyncSession, base_stmt, page: int, page_size: int):
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    result = await db.execute(base_stmt.offset((page - 1) * page_size).limit(page_size))
    items = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size if page_size else 1
    meta = {"page": page, "page_size": page_size, "total_items": total, "total_pages": total_pages}
    return items, meta
