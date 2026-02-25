"""Custom exception handlers for the API."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class ACRASError(Exception):
    """Base exception for ACRAS."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class CameraNotFoundError(ACRASError):
    def __init__(self, camera_id: str):
        super().__init__(f"Camera {camera_id} not found", status_code=404)


class IncidentNotFoundError(ACRASError):
    def __init__(self, incident_id: str):
        super().__init__(f"Incident {incident_id} not found", status_code=404)


class StreamConnectionError(ACRASError):
    def __init__(self, camera_id: str, reason: str):
        super().__init__(f"Failed to connect to camera {camera_id}: {reason}", status_code=502)


class DetectionError(ACRASError):
    def __init__(self, message: str):
        super().__init__(f"Detection pipeline error: {message}", status_code=500)


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers with the FastAPI app."""

    @app.exception_handler(ACRASError)
    async def acras_exception_handler(request: Request, exc: ACRASError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )
