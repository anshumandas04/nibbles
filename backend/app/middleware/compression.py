import gzip
import zlib
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class DecompressionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_encoding = request.headers.get("content-encoding", "").lower()
        if content_encoding in ("gzip", "deflate"):
            body = await request.body()
            try:
                if content_encoding == "gzip":
                    body = gzip.decompress(body)
                elif content_encoding == "deflate":
                    body = zlib.decompress(body)
                
                # Mock request.body() to return decompressed data
                async def decompressed_body():
                    return body
                request.body = decompressed_body
            except (gzip.BadGzipFile, zlib.error) as e:
                return Response(
                    content=f"Invalid compressed body: {str(e)}", 
                    status_code=400
                )
        
        response = await call_next(request)
        return response
