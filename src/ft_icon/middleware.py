# ft_icon/middleware.py
from fasthtml.common import Middleware, FT
from .icon import Icon
from starlette.types import ASGIApp, Message, Receive, Scope, Send
import logging

logger = logging.getLogger(__name__)

class _IconSpriteMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app
        # Ensure sprite file is loaded at startup
        try:
            Icon._load_sprite_file()
            logger.info("Successfully loaded sprite file in middleware")
        except Exception as e:
            logger.error(f"Failed to load sprite file: {e}")
            raise
            
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
            
        # Collect response chunks
        response_chunks = []
        async def store_chunks(message: Message):
            if message["type"] == "http.response.start":
                start_dict = dict(message)
                # Remove content-length as we'll modify the body
                start_dict["headers"] = [
                    (k,v) for k,v in start_dict["headers"] 
                    if k.decode().lower() != "content-length"
                ]
                await send(start_dict)
            elif message["type"] == "http.response.body":
                response_chunks.append(message["body"])
                if not message.get("more_body", False):
                    # Last chunk - combine and inject sprites
                    body = b''.join(response_chunks).decode()
                    if "<body" in body and Icon._page_icons:
                        sprite_defs = Icon.get_sprite_defs()
                        body_pos = body.find("<body") + body[body.find("<body"):].find(">") + 1
                        body = body[:body_pos] + str(sprite_defs) + body[body_pos:]
                    await send({
                        "type": "http.response.body",
                        "body": body.encode()
                    })
            else:
                await send(message)

        await self.app(scope, receive, store_chunks)

IconSpriteMiddleware = Middleware(_IconSpriteMiddleware)