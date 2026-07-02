"""Pagination, filtering and search helpers."""
from flask import current_app


def paginate_query(query, request_args):
    default_size = current_app.config.get("PAGE_SIZE_DEFAULT", 20)
    max_size = current_app.config.get("PAGE_SIZE_MAX", 100)

    try:
        page = max(int(request_args.get("page", 1)), 1)
    except ValueError:
        page = 1
    try:
        page_size = int(request_args.get("page_size", default_size))
    except ValueError:
        page_size = default_size
    page_size = min(max(page_size, 1), max_size)

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if page_size else 1

    meta = {
        "page": page,
        "page_size": page_size,
        "total_items": total,
        "total_pages": total_pages,
    }
    return items, meta
