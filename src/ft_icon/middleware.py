# ft_icon/middleware.py
from fasthtml.common import Middleware, FT
from .icon import Icon
from starlette.types import ASGIApp, Message, Receive, Scope, Send
import logging
import xml.etree.ElementTree as ET
from fasthtml.common import Div, NotStr

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

    @classmethod
    def get_sprite_defs(cls) -> NotStr:
        """Get SVG definitions with attributes renamed to data-og-*"""
        if not cls._page_icons:
            logger.warning("No page icons found for sprite injection")
            return NotStr("")
        
        symbols = []
        logger.debug(f"Processing {len(cls._page_icons)} icons for sprite injection")
        
        for icon_id in cls._page_icons:
            symbol_xml = cls._load_symbol(icon_id)
            if not symbol_xml:
                logger.warning(f"Could not load symbol for {icon_id}")
                continue
                
            try:
                root = ET.fromstring(symbol_xml)
                logger.debug(f"Original attributes for {icon_id}: {root.attrib}")
                
                # Store essential attributes
                pattern = root.get('data-og-pattern', '')
                view_box = root.get('viewBox')
                original_id = root.get('id')

                # Create fresh attributes dictionary
                new_attrib = {
                    'id': original_id,
                    'viewBox': view_box,
                    'data-og-pattern': pattern
                }

                # Process all attributes except special cases
                for attr_name, attr_value in root.attrib.items():
                    if attr_name in ['id', 'viewBox', 'data-og-pattern']:
                        continue
                    new_attrib[f'data-og-{attr_name}'] = attr_value

                # Validate transformation
                logger.debug(f"New attributes for {icon_id}: {new_attrib}")

                # Apply changes
                root.attrib.clear()
                root.attrib.update(new_attrib)
                
                symbol_xml = ET.tostring(root, encoding='unicode')
                symbols.append(symbol_xml)
                
            except ET.ParseError as e:
                logger.error(f"Error processing {icon_id}: {str(e)}")
                continue

        logger.info(f"Injected {len(symbols)} symbols with data-og attributes")
        return NotStr(f"""
            <svg xmlns="http://www.w3.org/2000/svg" style="display:none">
                {''.join(symbols)}
            </svg>
        """)

IconSpriteMiddleware = Middleware(_IconSpriteMiddleware)