from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from common.db.base import Base


class Era(Base):
    __tablename__ = "eras"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    slug: Mapped[str] = mapped_column(String, unique=True)
    name: Mapped[str] = mapped_column(String)
    year_range: Mapped[str] = mapped_column(String)
    start_year: Mapped[int | None] = mapped_column(Integer)
    end_year: Mapped[int | None] = mapped_column(Integer)
    summary: Mapped[str] = mapped_column(String)
    cover_image: Mapped[str | None] = mapped_column(String)
    fallback_image: Mapped[str | None] = mapped_column(String)
    featured_event_ids: Mapped[list[str]] = mapped_column(ARRAY(String))
    order_index: Mapped[int] = mapped_column(Integer)

