import hashlib
import logging
import uuid

from fastapi import Request

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# Configure logging for the middleware domain
logger = logging.getLogger(__name__)


class GlobalExceptionMiddleware(BaseHTTPMiddleware):
    """
    Middleware that catches unhandled exceptions across the entire request lifecycle.

    It ensures the API never leaks raw Python stack traces to the client. Instead,
    it logs the full error context internally and returns a sanitized JSON response
    with a tracking ID for debugging.
    """
    # TODO: LOG THE UNEXCEPTED ERROR TO DEBUG AND TRACE
    
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        
        except Exception:
            # Retrieve request_id from state if available, otherwise generate a fallback
            request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

            # Log the full stack trace with structured metadata for log aggregation
            logger.exception(
                "Unhandled exception",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "client_ip": getattr(request.state, "client_ip", "unknown"),
                },
            )
            
            # Return a generic 500 error to the client to maintain security
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
    Middleware responsible for extracting and attaching request metadata to the state.

    It handles request identification (UUID), IP extraction (considering proxies),
    and device fingerprinting. This data is then available to all downstream 
    handlers and services via 'request.state'.
    """

    @staticmethod
    def extract_client_ip(request: Request) -> str:
        """
        Retrieves the real client IP, prioritizing headers set by reverse proxies.

        Args:
            request: The incoming Starlette/FastAPI request.

        Returns:
            str: The detected IP address or 'unknown'.
        """

        # Common header used by Load Balancers (like Nginx/AWS) to pass the original IP
        forwarded_for = request.headers.get("X-Forwarded-For")

        if forwarded_for:
            # The first IP in the list is the original client
            return forwarded_for.split(",")[0].strip()
        
        if request.client:
            return request.client.host
        
        return "unknown"
    
    
    @staticmethod
    def build_device_fingerpint(ip_address: str, user_agent: str, accept_langauge: str) -> str:
        """
        Generates a SHA-256 hash representing a unique combination of request headers.

        This fingerprint can be used for basic session tracking, rate limiting, 
        or detecting suspicious behavior without relying solely on cookies.
        """

        fingerprint_source = (f"{ip_address}:{user_agent}:{accept_langauge}")
        return hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()
    

    async def dispatch(self, request: Request, call_next):
        """
        Processes the request to inject context and signs the outgoing response.
        """

        # Assign a unique ID to this request for end-to-end tracing
        request.state.request_id = str(uuid.uuid4())

        # Collect client metadata
        client_ip = self.extract_client_ip(request=request)
        user_agent = request.headers.get(key="User-Agent", default="unknown")
        accept_language = request.headers.get("Accept-Language", "unknown")

        # Create a stable fingerprint for this specific client/device
        device_fingerprint = (
            self.build_device_fingerpint(
                ip_address=client_ip,
                user_agent=user_agent,
                accept_langauge=accept_language
            )
        )

        # Attach metadata to request state for use in routes and services
        request.state.client_ip = client_ip
        request.state.user_agent = user_agent
        request.state.device_fingerprint = (device_fingerprint)
        
        # Proceed with the request chain
        response = await call_next(request)

        # Add the tracking ID to the response headers for client-side logging
        response.headers["X-Request-ID"] = request.state.request_id

        return response
        
