"""Global error handler middleware."""
import uuid
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.error_codes import BusinessException, ErrorCode
from app.core.logging_config import trace_id_var


logger = logging.getLogger(__name__)


async def error_handler_middleware(request: Request, call_next):
    """Global error handler middleware."""
    trace_id = str(uuid.uuid4())
    request.state.trace_id = trace_id
    token = trace_id_var.set(trace_id)

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
        logger.error("Unhandled exception", exc_info=True)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": ErrorCode.INTERNAL_ERROR[0],
                "message": ErrorCode.INTERNAL_ERROR[1],
                "trace_id": trace_id
            }
        )
    finally:
        trace_id_var.reset(token)
