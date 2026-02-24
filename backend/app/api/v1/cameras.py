"""Camera CRUD and stream management endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from geoalchemy2.elements import WKTElement
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthDep, get_db
from app.models.camera import Camera
from app.schemas.camera import (
    CameraBulkImport,
    CameraCreate,
    CameraListResponse,
    CameraResponse,
    CameraUpdate,
)

router = APIRouter()


def _camera_to_response(camera: Camera) -> CameraResponse:
    """Convert a Camera ORM object to a response schema."""
    return CameraResponse(
        id=camera.id,
        name=camera.name,
        description=camera.description,
        stream_url=camera.stream_url,
        stream_type=camera.stream_type,
        latitude=camera.latitude,
        longitude=camera.longitude,
        state_code=camera.state_code,
        interstate=camera.interstate,
        direction=camera.direction,
        mile_marker=camera.mile_marker,
        status=camera.status,
        last_frame_at=camera.last_frame_at,
        fps_actual=camera.fps_actual,
        resolution_width=camera.resolution_width,
        resolution_height=camera.resolution_height,
        source_agency=camera.source_agency,
        metadata=camera.metadata_,
        created_at=camera.created_at,
        updated_at=camera.updated_at,
    )


@router.get("", response_model=CameraListResponse)
async def list_cameras(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: str | None = None,
    state_code: str | None = None,
    interstate: str | None = None,
):
    """List cameras with optional filtering and pagination."""
    query = select(Camera)
    count_query = select(func.count(Camera.id))

    if status:
        query = query.where(Camera.status == status)
        count_query = count_query.where(Camera.status == status)
    if state_code:
        query = query.where(Camera.state_code == state_code)
        count_query = count_query.where(Camera.state_code == state_code)
    if interstate:
        query = query.where(Camera.interstate == interstate)
        count_query = count_query.where(Camera.interstate == interstate)

    total = (await db.execute(count_query)).scalar_one()
    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size).order_by(Camera.created_at.desc()))
    cameras = result.scalars().all()

    return CameraListResponse(
        items=[_camera_to_response(c) for c in cameras],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(camera_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get a single camera by ID."""
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return _camera_to_response(camera)


@router.post("", response_model=CameraResponse, status_code=201, dependencies=[AuthDep])
async def create_camera(data: CameraCreate, db: AsyncSession = Depends(get_db)):
    """Create a new camera."""
    camera = Camera(
        name=data.name,
        description=data.description,
        stream_url=data.stream_url,
        stream_type=data.stream_type,
        latitude=data.latitude,
        longitude=data.longitude,
        location=WKTElement(f"POINT({data.longitude} {data.latitude})", srid=4326),
        state_code=data.state_code.upper(),
        interstate=data.interstate,
        direction=data.direction,
        mile_marker=data.mile_marker,
        source_agency=data.source_agency,
        metadata_=data.metadata_ if data.metadata_ else {},
    )
    db.add(camera)
    await db.commit()
    await db.refresh(camera)
    return _camera_to_response(camera)


@router.patch("/{camera_id}", response_model=CameraResponse, dependencies=[AuthDep])
async def update_camera(camera_id: uuid.UUID, data: CameraUpdate, db: AsyncSession = Depends(get_db)):
    """Update an existing camera."""
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    update_data = data.model_dump(exclude_unset=True)
    if "latitude" in update_data or "longitude" in update_data:
        lat = update_data.get("latitude", camera.latitude)
        lon = update_data.get("longitude", camera.longitude)
        camera.location = WKTElement(f"POINT({lon} {lat})", srid=4326)

    if "metadata" in update_data:
        update_data["metadata_"] = update_data.pop("metadata")

    for key, value in update_data.items():
        setattr(camera, key, value)

    await db.commit()
    await db.refresh(camera)
    return _camera_to_response(camera)


@router.delete("/{camera_id}", status_code=204, dependencies=[AuthDep])
async def delete_camera(camera_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Delete a camera."""
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    await db.delete(camera)
    await db.commit()


@router.post("/bulk", response_model=dict, status_code=201, dependencies=[AuthDep])
async def bulk_import_cameras(data: CameraBulkImport, db: AsyncSession = Depends(get_db)):
    """Bulk import cameras from a list."""
    created = 0
    errors = []
    for i, cam_data in enumerate(data.cameras):
        try:
            camera = Camera(
                name=cam_data.name,
                description=cam_data.description,
                stream_url=cam_data.stream_url,
                stream_type=cam_data.stream_type,
                latitude=cam_data.latitude,
                longitude=cam_data.longitude,
                location=WKTElement(f"POINT({cam_data.longitude} {cam_data.latitude})", srid=4326),
                state_code=cam_data.state_code.upper(),
                interstate=cam_data.interstate,
                direction=cam_data.direction,
                mile_marker=cam_data.mile_marker,
                source_agency=cam_data.source_agency,
                metadata_=cam_data.metadata_ if cam_data.metadata_ else {},
            )
            db.add(camera)
            created += 1
        except Exception as e:
            errors.append({"index": i, "error": str(e)})

    await db.commit()
    return {"created": created, "errors": errors}
