from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Entity(Base):
    __tablename__ = "entities"

    icao24: Mapped[str] = mapped_column(Text, primary_key=True)
    callsign: Mapped[str | None] = mapped_column(Text, nullable=True)
    origin_country: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    positions: Mapped[list["Position"]] = relationship(back_populates="entity")


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    icao24: Mapped[str] = mapped_column(
        Text, ForeignKey("entities.icao24", ondelete="CASCADE"), nullable=False
    )
    t: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    geom: Mapped[object] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326), nullable=False
    )
    baro_altitude_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    velocity_m_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    true_track_deg: Mapped[float | None] = mapped_column(Float, nullable=True)
    vertical_rate_m_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    on_ground: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    entity: Mapped["Entity"] = relationship(back_populates="positions")
