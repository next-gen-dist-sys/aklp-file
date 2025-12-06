"""File API endpoints."""

from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response

from app.core.config import settings
from app.core.deps import DBSession
from app.schemas.file import FileListResponse, FileResponse, FileUpdate
from app.services.file_service import FileService

router = APIRouter()

FILES_PER_PAGE = 10


@router.post(
    "",
    response_model=FileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a file",
)
async def upload_file(
    db: DBSession,
    file: UploadFile = File(..., description="File to upload"),
    description: str | None = Form(None, description="File description"),
    session_id: UUID | None = Form(None, description="AI session ID"),
) -> FileResponse:
    """Upload a new file.

    Args:
        db: Database session
        file: File to upload
        description: Optional file description
        session_id: Optional AI session ID

    Returns:
        Uploaded file metadata

    Raises:
        HTTPException: 413 if file is too large
    """
    # Read file content
    content = await file.read()

    # Check file size
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE // (1024 * 1024)}MB",
        )

    service = FileService(db)
    saved_file = await service.create(
        filename=file.filename or "unnamed",
        content_type=file.content_type or "application/octet-stream",
        content=content,
        session_id=session_id,
        description=description,
    )

    return FileResponse.model_validate(saved_file)


@router.get(
    "",
    response_model=FileListResponse,
    summary="Get list of files",
)
async def list_files(
    db: DBSession,
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    session_id: UUID | None = Query(default=None, description="Filter by session ID"),
) -> FileListResponse:
    """Get paginated list of files.

    Args:
        db: Database session
        page: Page number (1-indexed)
        session_id: Optional session ID filter

    Returns:
        Paginated file list
    """
    service = FileService(db)
    files, total = await service.get_list(page=page, session_id=session_id)

    return FileListResponse(
        items=[FileResponse.model_validate(f) for f in files],
        total=total,
        page=page,
        limit=FILES_PER_PAGE,
    )


@router.get(
    "/{file_id}",
    response_model=FileResponse,
    summary="Get file metadata",
)
async def get_file(
    file_id: UUID,
    db: DBSession,
) -> FileResponse:
    """Get file metadata by ID.

    Args:
        file_id: File UUID
        db: Database session

    Returns:
        File metadata

    Raises:
        HTTPException: 404 if file not found
    """
    service = FileService(db)
    file = await service.get_by_id(file_id)

    if file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {file_id} not found",
        )

    return FileResponse.model_validate(file)


@router.get(
    "/{file_id}/download",
    summary="Download file content",
)
async def download_file(
    file_id: UUID,
    db: DBSession,
) -> Response:
    """Download file content.

    Args:
        file_id: File UUID
        db: Database session

    Returns:
        File content with appropriate headers

    Raises:
        HTTPException: 404 if file not found
    """
    service = FileService(db)
    file = await service.get_by_id(file_id)

    if file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {file_id} not found",
        )

    return Response(
        content=file.content,
        media_type=file.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{file.filename}"',
            "Content-Length": str(file.size),
        },
    )


@router.patch(
    "/{file_id}",
    response_model=FileResponse,
    summary="Update file metadata",
)
async def update_file_metadata(
    file_id: UUID,
    file_data: FileUpdate,
    db: DBSession,
) -> FileResponse:
    """Update file metadata (filename, description).

    Args:
        file_id: File UUID
        file_data: Update data
        db: Database session

    Returns:
        Updated file metadata

    Raises:
        HTTPException: 404 if file not found
    """
    service = FileService(db)
    file = await service.update_metadata(file_id, file_data)

    if file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {file_id} not found",
        )

    return FileResponse.model_validate(file)


@router.put(
    "/{file_id}",
    response_model=FileResponse,
    summary="Replace file content",
)
async def replace_file(
    file_id: UUID,
    db: DBSession,
    file: UploadFile = File(..., description="New file content"),
) -> FileResponse:
    """Replace file content entirely.

    Args:
        file_id: File UUID
        db: Database session
        file: New file to upload

    Returns:
        Updated file metadata

    Raises:
        HTTPException: 404 if file not found
        HTTPException: 413 if file is too large
    """
    # Read file content
    content = await file.read()

    # Check file size
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE // (1024 * 1024)}MB",
        )

    service = FileService(db)
    updated_file = await service.update_content(
        file_id=file_id,
        filename=file.filename or "unnamed",
        content_type=file.content_type or "application/octet-stream",
        content=content,
    )

    if updated_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {file_id} not found",
        )

    return FileResponse.model_validate(updated_file)


@router.delete(
    "/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a file",
)
async def delete_file(
    file_id: UUID,
    db: DBSession,
) -> None:
    """Delete a file.

    Args:
        file_id: File UUID
        db: Database session

    Raises:
        HTTPException: 404 if file not found
    """
    service = FileService(db)
    deleted = await service.delete(file_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {file_id} not found",
        )
