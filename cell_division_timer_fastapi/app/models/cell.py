"""Cell / Biological Sample SQLAlchemy ORM model."""

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class Cell(Base, TimestampMixin):
    """Represents a biological cell sample or lineage under observation."""

    __tablename__ = "cells"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False, index=True)
    organism = Column(String(128), nullable=False, index=True)
    cell_type = Column(String(128), nullable=False, index=True)
    passage_number = Column(Integer, nullable=True, default=1)
    source_line = Column(String(128), nullable=True)
    description = Column(Text, nullable=True)

    # Relationships
    division_records = relationship(
        "CellDivisionRecord",
        back_populates="cell",
        cascade="all, delete-orphan",
        order_by="CellDivisionRecord.generation",
    )

    def __repr__(self) -> str:
        return f"<Cell(id='{self.id}', name='{self.name}', organism='{self.organism}', cell_type='{self.cell_type}')>"
