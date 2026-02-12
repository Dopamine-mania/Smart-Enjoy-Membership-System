"""Global error handler middleware."""
import uuid
import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.error_codes import BusinessException, ErrorCode


async def error_handler_middleware(request: Request, call_next):
    """Global error handler middleware."""
    trace_id = str(uuid.uuid4())
    request.state.trace_id = trace_id

    try:
        response = await call_next(request)
        return response

    except BusinessException as e:
        # Business logic exception
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "code": e.code,
                "message": e.message,
                "trace_id": trace_id,
                "details": e.details
            }
        )

    except Exception as e:
        # Unexpected exception
        print(f"[ERROR] Trace ID: {trace_id}")
        print(traceback.format_exc())

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": ErrorCode.INTERNAL_ERROR[0],
                "message": ErrorCode.INTERNAL_ERROR[1],
                "trace_id": trace_id
            }
        )
