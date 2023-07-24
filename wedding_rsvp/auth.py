from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

from flask import current_app
from flask_httpauth import HTTPBasicAuth  # type: ignore[import]
from werkzeug.security import check_password_hash

if TYPE_CHECKING:
    from typing import Optional


http_auth = HTTPBasicAuth()


class UserType(Enum):
    ADMIN = auto()


@http_auth.verify_password
def verify_password(username: str, password: str) -> UserType | None:
    """
    Verifies the admin password for HTTP Basic Auth protected view functions.
    """

    if username == "admin" and check_password_hash(current_app.config["ADMIN_PASSWORD"], password):
        return UserType.ADMIN

    return None
