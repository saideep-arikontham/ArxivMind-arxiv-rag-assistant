from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import Integer, String

Base = declarative_base()

class FirstTable(Base):
    __tablename__ = "first_table"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
