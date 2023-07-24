from __future__ import annotations

import random
import string
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, MetaData
from sqlalchemy.orm import DeclarativeMeta, declarative_base
from sqlalchemy.sql.schema import (
    CheckConstraint,
    ForeignKeyConstraint,
    Index,
    PrimaryKeyConstraint,
    UniqueConstraint,
)
from sqlalchemy.types import DateTime, TypeDecorator

from wedding_rsvp.utils import local_now

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from typing import Any

    from sqlalchemy.engine import Dialect
    from sqlalchemy.engine.default import DefaultExecutionContext
    from sqlalchemy.sql.schema import Column


naming_convention = {
    PrimaryKeyConstraint: "pk_%(table_name)s",
    ForeignKeyConstraint: "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    CheckConstraint: "ck_%(table_name)s_%(constraint_name)s",
    UniqueConstraint: "uq_%(table_name)s_%(column_0_N_name)s",
    Index: "ix_%(column_0_N_label)s",
}

metadata = MetaData(naming_convention=naming_convention)  # type: ignore[arg-type]


db = SQLAlchemy(model_class=declarative_base(metadata=metadata, metaclass=DeclarativeMeta))


def from_column(column: Column[Any]) -> Callable[[DefaultExecutionContext], Any]:
    """
    Returns a context-sensitive function that returns the Pythonic value from another column.

    This allows for setting a (default) value in one column that is automatically copied over to
    another column.
    """

    def context_sensitive_default(context: DefaultExecutionContext) -> Any:
        return context.get_current_parameters().get(column.name)

    return context_sensitive_default


def generate_rsvp_code() -> str:
    """
    Generates a guest code with a combination of uppercase characters and digits.
    """

    rsvp_code = ""

    while len(rsvp_code) < RSVP.RSVP_CODE_LENGTH:
        char = random.SystemRandom().choice(string.ascii_uppercase)
        if char in rsvp_code:
            continue

        rsvp_code += char

        if (
            len(rsvp_code) == RSVP.RSVP_CODE_LENGTH
            and RSVP.get_by_rsvp_code(rsvp_code=rsvp_code) is not None
        ):
            rsvp_code = ""

    return rsvp_code


class TZDateTime(TypeDecorator[datetime]):
    """
    DateTime data type for transparently handling timezones.

    Values are stored as naive UTC timestamps and returned as aware local timestamps.

    Requires timezone aware `datetime` objects to be used in queries.
    """

    impl = DateTime(timezone=False)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        """
        Processes timezone aware `datetime` objects for use in queries.

        The given `value` is converted to a naive `datetime` object in the UTC timezone.
        """

        if value is not None:
            if value.tzinfo is None:
                raise ValueError("Timezone aware `datetime` object is required.")

            value = value.astimezone(timezone.utc).replace(tzinfo=None)

        return value

    def process_literal_param(self, value: Any | None, dialect: Dialect) -> str:
        """
        Renders the given Python `value` into a literal string, for use in SQL query previews.

        Processes the value as for bound parameters and returns it in ISO-8601 string format.
        """

        bound_value = self.process_bind_param(value=value, dialect=dialect)

        if bound_value is not None:
            return bound_value.isoformat(sep="T")

        return str(bound_value)

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        """
        Processes naive `datetime` objects returned in query results.

        The given `value` is converted to an aware `datetime` object in the local timezone.
        """

        if value is not None:
            if value.tzinfo is not None:
                raise ValueError("Naive `datetime` object is required.")

            value = value.replace(tzinfo=timezone.utc).astimezone()

        return value

    @property
    def python_type(self) -> type:
        """
        Returns the Python type used for parameter and result values.
        """

        return type(self.impl.python_type)


class RSVP(db.Model):  # type: ignore[name-defined]
    """
    Model class that stores the RSVPs.
    """

    RSVP_CODE_LENGTH = 4

    __tablename__ = "rsvp"

    id = db.Column(
        db.BigInteger().with_variant(Integer, "sqlite"),
        name="id",
        nullable=False,
        primary_key=True,
    )

    rsvp_code = db.Column(
        db.String(RSVP_CODE_LENGTH), nullable=False, unique=True, default=generate_rsvp_code
    )

    guest_first_name = db.Column(db.String(50), nullable=False)
    guest_last_name = db.Column(db.String(50), nullable=False)
    guest_present = db.Column(db.Boolean, nullable=False)
    guest_present_ceremony = db.Column(db.Boolean, nullable=False)
    guest_present_reception = db.Column(db.Boolean, nullable=False)
    guest_present_dinner = db.Column(db.Boolean, nullable=False)
    guest_email = db.Column(db.String(254), nullable=True, unique=True)
    guest_diet_meat = db.Column(db.Boolean, nullable=False)
    guest_diet_fish = db.Column(db.Boolean, nullable=False)
    guest_diet_vega = db.Column(db.Boolean, nullable=False)

    with_partner = db.Column(db.Boolean, nullable=False)
    partner_first_name = db.Column(db.String(50), nullable=False, default="")
    partner_last_name = db.Column(db.String(50), nullable=False, default="")
    partner_diet_meat = db.Column(db.Boolean, nullable=True, default=None)
    partner_diet_fish = db.Column(db.Boolean, nullable=True, default=None)
    partner_diet_vega = db.Column(db.Boolean, nullable=True, default=None)

    remarks = db.Column(db.String(250), nullable=False, default="")

    created_at = db.Column(
        TZDateTime,
        name="created_at",
        nullable=False,
        default=local_now,
    )

    updated_at = db.Column(
        TZDateTime,
        name="updated_at",
        nullable=False,
        default=from_column(created_at),
        onupdate=local_now,
    )

    @classmethod
    def get_all(cls) -> Sequence[RSVP]:
        return db.session.query(cls).order_by(cls.guest_first_name, cls.guest_last_name).all()

    @classmethod
    def get_by_guest_email(cls, *, guest_email: str) -> RSVP | None:
        return db.session.query(cls).filter(cls.guest_email == guest_email).first()

    @classmethod
    def get_by_rsvp_code(cls, *, rsvp_code: str) -> RSVP | None:
        return db.session.query(cls).filter(cls.rsvp_code == rsvp_code).first()
