from __future__ import annotations

from datetime import datetime


def local_now() -> datetime:
    """
    Returns a timezone aware datetime object in the host's timezone.
    """

    return datetime.now().astimezone()
