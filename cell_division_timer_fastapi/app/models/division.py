"""Cell Division Event / Cycle Timing SQLAlchemy ORM model."""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class CellDivisionRecord(Base, TimestampMixin):
    """Represents a measured cell-cycle division event and biological kinetic observation."""

    __tablename__ = "cell_division_records"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    cell_id = Column(
        String(64),
        ForeignKey("cells.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    experimental_batch = Column(String(64), nullable=False, index=True)
    replicate = Column(Integer, nullable=False, default=1)
    experimental_condition = Column(String(128), nullable=False, index=True)
    medium = Column(String(128), nullable=False)
    temperature_celsius = Column(Float, nullable=False, index=True)
    generation = Column(Integer, nullable=False, default=1, index=True)

    # Timing metrics
    division_start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    division_end_time = Column(DateTime(timezone=True), nullable=False, index=True)

    # `division_duration_minutes` and `growth_rate` are the OFFICIAL, STORED values
    # used everywhere else in the application (QC evaluation, filtering, sorting,
    # analytics, CSV export). They are always either:
    #   (a) mathematically derived from the source measurements
    #       (division_start_time/division_end_time, cell_cycle_duration_hours), or
    #   (b) an explicit, reason-documented manual override (see the
    #       *_override / *_override_reason columns below).
    # They must NEVER silently diverge from (a) unless (b) applies. This is
    # enforced in DivisionService, not just at the schema layer, so it also
    # holds for updates that only touch one side of a derived pair.
    division_duration_minutes = Column(Float, nullable=False, index=True)
    cell_cycle_duration_hours = Column(Float, nullable=False, index=True)
    growth_rate = Column(Float, nullable=False, index=True)  # Specific growth rate mu (hr^-1)

    # Explicit manual overrides (OBSERVED != CALCULATED != OVERRIDE).
    # These are ONLY populated when a scientist deliberately overrides the
    # mathematically-derived value (e.g. correcting for known instrument clock
    # drift). They are never set implicitly, and a value/reason pair must
    # always be supplied together (enforced by CellDivisionCreate/Update).
    duration_override_minutes = Column(Float, nullable=True)
    duration_override_reason = Column(Text, nullable=True)
    growth_rate_override = Column(Float, nullable=True)
    growth_rate_override_reason = Column(Text, nullable=True)

    # Quality control & biological classification
    is_outlier = Column(Boolean, nullable=False, default=False, index=True)
    quality_flag = Column(String(32), nullable=False, default="PASS", index=True)
    notes = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)

    # Relationships
    cell = relationship("Cell", back_populates="division_records")

    __table_args__ = (
        CheckConstraint(
            "division_end_time >= division_start_time",
            name="ck_division_end_after_start",
        ),
        CheckConstraint(
            "division_duration_minutes >= 0",
            name="ck_positive_division_duration",
        ),
        CheckConstraint(
            "cell_cycle_duration_hours > 0",
            name="ck_positive_cell_cycle_duration",
        ),
        CheckConstraint(
            "temperature_celsius >= -10.0 AND temperature_celsius <= 100.0",
            name="ck_plausible_temperature",
        ),
        CheckConstraint(
            "(duration_override_minutes IS NULL) = (duration_override_reason IS NULL)",
            name="ck_duration_override_requires_reason",
        ),
        CheckConstraint(
            "(growth_rate_override IS NULL) = (growth_rate_override_reason IS NULL)",
            name="ck_growth_rate_override_requires_reason",
        ),
        Index("ix_divisions_batch_condition", "experimental_batch", "experimental_condition"),
        Index("ix_divisions_cell_gen", "cell_id", "generation"),
    )

    def __repr__(self) -> str:
        return (
            f"<CellDivisionRecord(id={self.id}, cell_id='{self.cell_id}', "
            f"batch='{self.experimental_batch}', gen={self.generation}, "
            f"duration_min={self.division_duration_minutes})>"
        )
