"""Base model definitions and mixins."""

from datetime import datetime
from sqlalchemy import Column, DateTime, func


class TimestampMixin:
    """Mixin for models requiring created_at and updated_at audit timestamps."""

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
