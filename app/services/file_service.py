"""File service for CRUD operations."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file import File
from app.schemas.file import FileUpdate


class FileService:
    """Service for managing files."""

    def __init__(self, db: AsyncSession):
        """Initialize file service.

        Args:
            db: Database session
        """
        self.db = db

    async def create(
        self,
        filename: str,
        content_type: str,
        content: bytes,
        session_id: UUID | None = None,
        description: str | None = None,
    ) -> File:
        """Create a new file.

        Args:
            filename: Original filename
            content_type: MIME type
            content: File content bytes
            session_id: Optional AI session ID
            description: Optional file description

        Returns:
            Created file
        """
        file = File(
            filename=filename,
            content_type=content_type,
            size=len(content),
            content=content,
            session_id=session_id,
            description=description,
        )
        self.db.add(file)
        await self.db.commit()
        await self.db.refresh(file)
        return file

    async def get_by_id(self, file_id: UUID) -> File | None:
        """Get a file by ID.

        Args:
            file_id: File UUID

        Returns:
            File if found, None otherwise
        """
        result = await self.db.execute(select(File).where(File.id == file_id))
        return result.scalar_one_or_none()

    async def get_list(
        self,
        page: int = 1,
        session_id: UUID | None = None,
    ) -> tuple[list[File], int]:
        """Get paginated list of files.

        Args:
            page: Page number (1-indexed)
            session_id: Optional session ID filter

        Returns:
            Tuple of (files list, total count)
        """
        limit = 10
        offset = (page - 1) * limit

        # Build queries (exclude content for list)
        query = select(File)
        count_query = select(func.count()).select_from(File)

        # Apply filters
        if session_id is not None:
            query = query.where(File.session_id == session_id)
            count_query = count_query.where(File.session_id == session_id)

        # Sort by updated_at desc
        query = query.order_by(File.updated_at.desc())

        # Apply pagination
        query = query.offset(offset).limit(limit)

        # Execute queries
        files_result = await self.db.execute(query)
        files = list(files_result.scalars().all())

        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one()

        return files, total

    async def update_metadata(self, file_id: UUID, file_data: FileUpdate) -> File | None:
        """Update file metadata (filename, description).

        Args:
            file_id: File UUID
            file_data: Update data

        Returns:
            Updated file if found, None otherwise
        """
        file = await self.get_by_id(file_id)
        if file is None:
            return None

        if file_data.filename is not None:
            file.filename = file_data.filename
        if file_data.description is not None:
            file.description = file_data.description

        await self.db.commit()
        await self.db.refresh(file)
        return file

    async def update_content(
        self,
        file_id: UUID,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> File | None:
        """Replace file content.

        Args:
            file_id: File UUID
            filename: New filename
            content_type: New MIME type
            content: New file content

        Returns:
            Updated file if found, None otherwise
        """
        file = await self.get_by_id(file_id)
        if file is None:
            return None

        file.filename = filename
        file.content_type = content_type
        file.size = len(content)
        file.content = content

        await self.db.commit()
        await self.db.refresh(file)
        return file

    async def delete(self, file_id: UUID) -> bool:
        """Delete a file.

        Args:
            file_id: File UUID

        Returns:
            True if deleted, False if not found
        """
        file = await self.get_by_id(file_id)
        if file is None:
            return False

        await self.db.delete(file)
        await self.db.commit()
        return True
