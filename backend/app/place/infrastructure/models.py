"""SQLAlchemy persistence model for public TourAPI place data."""

from sqlalchemy import CheckConstraint, Float, Index, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Place(Base):
    """A TourAPI place plus fields reserved for course recommendation enrichment."""

    __tablename__ = "places"
    __table_args__ = (
        CheckConstraint(
            "content_type_id IN (12, 14, 25, 28, 32, 38, 39)",
            name="ck_places_content_type_id",
        ),
        CheckConstraint(
            "is_recommendable IN (0, 1)",
            name="ck_places_is_recommendable",
        ),
        Index("ix_places_content_type_id", "content_type_id"),
        Index("ix_places_district", "district"),
        Index("ix_places_recommendable", "is_recommendable"),
        Index("ix_places_title", "title"),
        Index("ix_places_coordinates", "latitude", "longitude"),
    )

    content_id: Mapped[str] = mapped_column(Text, primary_key=True)
    content_type_id: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    address_detail: Mapped[str] = mapped_column(Text, nullable=False)
    zipcode: Mapped[str] = mapped_column(Text, nullable=False)
    telephone: Mapped[str] = mapped_column(Text, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    map_level: Mapped[int | None] = mapped_column(Integer)
    area_code: Mapped[str] = mapped_column(Text, nullable=False)
    sigungu_code: Mapped[str] = mapped_column(Text, nullable=False)
    legal_region_code: Mapped[str] = mapped_column(Text, nullable=False)
    legal_sigungu_code: Mapped[str] = mapped_column(Text, nullable=False)
    category1: Mapped[str] = mapped_column(Text, nullable=False)
    category2: Mapped[str] = mapped_column(Text, nullable=False)
    category3: Mapped[str] = mapped_column(Text, nullable=False)
    class_code1: Mapped[str] = mapped_column(Text, nullable=False)
    class_code2: Mapped[str] = mapped_column(Text, nullable=False)
    class_code3: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_url: Mapped[str] = mapped_column(Text, nullable=False)
    copyright_code: Mapped[str] = mapped_column(Text, nullable=False)
    source_created_at: Mapped[str | None] = mapped_column(Text)
    source_modified_at: Mapped[str | None] = mapped_column(Text)

    district: Mapped[str | None] = mapped_column(Text)
    space_type: Mapped[str | None] = mapped_column(Text)
    moods_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    activities_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    keywords_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    description: Mapped[str | None] = mapped_column(Text)
    estimated_stay_minutes: Mapped[int | None] = mapped_column(Integer)
    estimated_cost: Mapped[int | None] = mapped_column(Integer)
    rain_suitability: Mapped[float | None] = mapped_column(Float)
    conversation_score: Mapped[float | None] = mapped_column(Float)
    photo_score: Mapped[float | None] = mapped_column(Float)
    is_recommendable: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)
