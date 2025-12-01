"""
Custom exception handlers for the API.
"""
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Custom handler for request validation errors.
    
    Converts 422 validation errors for UUID path parameters to 400 Bad Request
    as per API specification.
    """
    # Check if the validation error is related to UUID in path parameters
    for error in exc.errors():
        if error.get("type") in ["uuid_parsing", "uuid_type"] and error.get("loc", [None])[0] == "path":
            # Return 400 for invalid UUID format in path
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Invalid job_id format. Must be a valid UUID."}
            )
    
    # For other validation errors, return standard 422
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )
