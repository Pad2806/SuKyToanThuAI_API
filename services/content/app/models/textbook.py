from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from common.db.base import Base


class TextbookPart(Base):
    __tablename__ = "textbook_parts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    grade_id: Mapped[str] = mapped_column(String)
    part_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String)
    order_index: Mapped[int] = mapped_column(Integer)


class TextbookLesson(Base):
    __tablename__ = "textbook_lessons"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    part_id: Mapped[str] = mapped_column(String)
    event_id: Mapped[str] = mapped_column(String)
    lesson_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String)
    order_index: Mapped[int] = mapped_column(Integer)

