"""Pydantic schemas for File API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, computed_field


class FileUpload(BaseModel):
    """Schema for file upload metadata (file content comes separately)."""

    description: str | None = Field(None, max_length=1000, description="File description")
    session_id: UUID | None = Field(None, description="AI session ID")


class FileUpdate(BaseModel):
    """Schema for updating file metadata."""

    filename: str | None = Field(None, min_length=1, max_length=255, description="New filename")
    description: str | None = Field(None, max_length=1000, description="File description")


class FileResponse(BaseModel):
    """Schema for file response (without content)."""

    id: UUID
    filename: str
    content_type: str
    size: int
    session_id: UUID | None
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FileListResponse(BaseModel):
    """Schema for paginated file list response."""

    items: list[FileResponse]
    total: int = Field(..., description="Total number of files")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")

    @computed_field  # type: ignore
    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        if self.limit == 0:
            return 0
        return (self.total + self.limit - 1) // self.limit

    @computed_field  # type: ignore
    @property
    def has_next(self) -> bool:
        """Check if there is a next page."""
        return self.page < self.total_pages

    @computed_field  # type: ignore
    @property
    def has_prev(self) -> bool:
        """Check if there is a previous page."""
        return self.page > 1
