import hashlib
import logging
import uuid

from fastapi import Request
from starlette.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class GlobalExceptionMiddleware(BaseHTTPMiddleware):
    """
    Logs unhandled exceptions and returns a stable error response.
    """

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception:
            request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

            logger.exception(
                "Unhandled exception",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "client_ip": getattr(request.state, "client_ip", "unknown"),
                },
            )

            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "request_id": request_id,
                },
                headers={
                    "X-Request-ID": request_id,
                },
            )

class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Injects request metadata into request state.
    """

    @staticmethod
    def extract_client_ip(request: Request) -> str:
        """
        Extract real client IP address.
        """
        forwarded_for = request.headers.get("X-Forwareded-For")

        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        if request.client:
            return request.client.host
        
        return "unknown"
    
    
    @staticmethod
    def build_device_fingerpint(ip_address: str, user_agent: str, accept_langauge: str) -> str:
        """
        Builds stable device fingerprint
        """

        fingerprint_source = (f"{ip_address}:{user_agent}:{accept_langauge}")

        return hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()
    

    async def dispatch(self, request: Request, call_next):
        request.state.request_id = str(uuid.uuid4())

        client_ip = self.extract_client_ip(request=request)

        user_agent = request.headers.get(key="User-Agent", default="unknown")

        accept_language = request.headers.get("Accept-Language", "unknown")

        device_fingerprint = (
            self.build_device_fingerpint(
                ip_address=client_ip,
                user_agent=user_agent,
                accept_langauge=accept_language
            )
        )

        request.state.client_ip = client_ip
        request.state.user_agent = user_agent
        request.state.device_fingerprint = (device_fingerprint)

        response = await call_next(request)

        response.headers["X-Request-ID"] = request.state.request_id

        return response
        
