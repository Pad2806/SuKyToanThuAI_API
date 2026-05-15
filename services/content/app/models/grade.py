from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from common.db.base import Base


class Grade(Base):
    __tablename__ = "grades"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    tag: Mapped[str] = mapped_column(String, unique=True)
    label: Mapped[str] = mapped_column(String)
    order_index: Mapped[int] = mapped_column(Integer)

