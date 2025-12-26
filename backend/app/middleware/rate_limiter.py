"""
Rate Limiter Middleware
"""
import time
import logging
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # 1 minute
        self._requests: Dict[str, list] = defaultdict(list)
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request."""
        # Try to get user_id from query params or body
        user_id = request.query_params.get("user_id")
        
        if not user_id:
            # Fall back to IP
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                user_id = forwarded.split(",")[0].strip()
            else:
                user_id = request.client.host if request.client else "unknown"
        
        return user_id
    
    def _cleanup_old_requests(self, client_id: str, current_time: float) -> None:
        """Remove requests outside the time window."""
        cutoff = current_time - self.window_size
        self._requests[client_id] = [
            t for t in self._requests[client_id] if t > cutoff
        ]
    
    def is_allowed(self, request: Request) -> Tuple[bool, int]:
        """
        Check if request is allowed.
        
        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        client_id = self._get_client_id(request)
        current_time = time.time()
        
        # Cleanup old requests
        self._cleanup_old_requests(client_id, current_time)
        
        # Check count
        request_count = len(self._requests[client_id])
        
        if request_count >= self.requests_per_minute:
            return False, 0
        
        # Record request
        self._requests[client_id].append(current_time)
        
        return True, self.requests_per_minute - request_count - 1


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware for chat endpoints.
    """
    
    def __init__(self, app, rate_limit_paths: list = None):
        super().__init__(app)
        settings = get_settings()
        self.limiter = RateLimiter(requests_per_minute=settings.rate_limit_per_minute)
        self.rate_limit_paths = rate_limit_paths or ["/api/messages"]
    
    async def dispatch(self, request: Request, call_next):
        # Only rate limit specific paths
        should_limit = any(
            request.url.path.startswith(path) 
            for path in self.rate_limit_paths
        )
        
        # Only limit POST requests (sending messages)
        if should_limit and request.method == "POST":
            is_allowed, remaining = self.limiter.is_allowed(request)
            
            if not is_allowed:
                logger.warning(f"Rate limit exceeded for: {request.url.path}")
                raise HTTPException(
                    status_code=429,
                    detail="Too many messages. Please slow down and try again in a minute."
                )
            
            # Add rate limit headers
            response = await call_next(request)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            return response
        
        return await call_next(request)
