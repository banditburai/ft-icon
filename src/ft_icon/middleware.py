from fasthtml.common import Middleware, FT
from .icon import Icon
from starlette.types import ASGIApp, Message, Receive, Scope, Send
import logging

logger = logging.getLogger(__name__)

class _IconSpriteMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app
        try:
            Icon._load_sprite_file()
            logger.info("Successfully loaded sprite file in middleware")
        except Exception as e:
            logger.error(f"Failed to load sprite file: {e}")
            raise
            
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http" or not self._should_process(scope):
            return await self.app(scope, receive, send)

        response_headers = {}
        body_buffer = b""

        async def wrapped_send(message: Message):
            nonlocal body_buffer
            
            if message["type"] == "http.response.start":
                # Store headers to check content type
                response_headers.update({
                    k.decode().lower(): v.decode().lower()
                    for k, v in message.get("headers", [])
                })
                # Remove content-length header since we'll modify the body
                message["headers"] = [
                    (k, v) for k, v in message.get("headers", [])
                    if k.decode().lower() != "content-length"
                ]
                await send(message)
                
            elif message["type"] == "http.response.body":
                if response_headers.get("content-type", "").startswith("text/html"):
                    body_buffer += message.get("body", b"")
                    
                    if not message.get("more_body", False):
                        # Process complete HTML response
                        try:
                            decoded_body = body_buffer.decode()
                            if "<body" in decoded_body and Icon._page_icons:
                                sprite_defs = Icon.get_sprite_defs()
                                body_pos = decoded_body.find("<body") 
                                body_pos += decoded_body[body_pos:].find(">") + 1
                                modified_body = (
                                    decoded_body[:body_pos] + 
                                    str(sprite_defs) + 
                                    decoded_body[body_pos:]
                                )
                                await send({
                                    "type": "http.response.body",
                                    "body": modified_body.encode()
                                })
                                return
                        except UnicodeDecodeError:
                            pass  # Fall through to original send
                        
                # Forward unmodified response for non-HTML or errors
                await send(message)
                
            else:
                await send(message)

        await self.app(scope, receive, wrapped_send)

    def _should_process(self, scope: Scope) -> bool:
        """Determine if request should be processed by this middleware"""
        path = scope.get("path", "")
        return (
            scope["method"] == "GET" and
            not path.startswith("/static/") and
            not any(path.endswith(ext) for ext in (
                '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', 
                '.css', '.js', '.webp', '.avif'
            ))
        )

IconSpriteMiddleware = Middleware(_IconSpriteMiddleware)