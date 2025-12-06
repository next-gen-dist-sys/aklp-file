"""File model for database."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, LargeBinary, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class File(Base):
    """File model for storing uploaded files."""

    __tablename__ = "files"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    filename: Mapped[str] = mapped_column(nullable=False)
    content_type: Mapped[str] = mapped_column(nullable=False)  # MIME type
    size: Mapped[int] = mapped_column(Integer, nullable=False)  # bytes
    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    session_id: Mapped[UUID | None] = mapped_column(nullable=True, default=None)
    description: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        """String representation of File."""
        return f"<File(id={self.id}, filename={self.filename}, size={self.size})>"