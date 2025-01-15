from enum import Enum
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import ClassVar, Set, Dict, Union, Callable
import logging
import os

from fasthtml.common import Div, NotStr
from tw_merge import tw_merge
from .config import config, Size, Style
from .build_sprite import IconConfig

logger = logging.getLogger(__name__)

class IconMeta(type):
    def __getattr__(cls, name: str) -> Callable[..., 'Icon']:
        """Handle dynamic icon method creation"""
        if name.startswith('__') and name.endswith('__'):
            raise AttributeError(name)
            
        if name in ['name', 'size', 'style', 'cls']:
            raise AttributeError(name)
            
        try:
            return cls._create_icon_method(name)
        except AttributeError:
            logger.warning(f"Icon '{name}' not found, using fallback")
            return cls._create_fallback_icon(name)

@dataclass
class Icon(metaclass=IconMeta):
    """SVG icon component using sprite system"""
    __slots__ = ['name', 'size', 'style', 'cls']
    
    # Remove default values from dataclass fields
    name: str
    size: Union[Size, str]
    style: Union[Style, str]
    cls: str
    
    def __init__(self, 
                 name: str, 
                 size: Union[Size, str] = Size.MD,
                 style: Union[Style, str] = Style.OG,
                 cls: str = "") -> None:
        """Initialize with defaults in __init__ instead of class level"""
        self.name = name
        self.size = size
        self.style = style
        self.cls = cls
    
    _page_icons: ClassVar[Set[str]] = set()
    _symbol_cache: ClassVar[Dict[str, str]] = {}
    
    @classmethod
    def get_sprite_path(cls) -> Path:
        """Get sprite path from environment or use default"""
        return Path(os.getenv('FT_ICON_OUTPUT_DIR', 'static')) / 'sprite.svg'
    
    @classmethod
    def _create_fallback_icon(cls, name: str):
        """Create a method that returns a simple fallback for missing icons"""
        def fallback_method(*args, **kwargs):
            # Return an empty div if question icon isn't available
            if "icons.question" not in cls._symbol_cache:
                return Div(cls="w-6 h-6")
            return cls(name="icons.question", cls="text-error")
        return fallback_method
    
    @classmethod
    def _create_icon_method(cls, name: str) -> Callable[..., 'Icon']:
        """Create an icon method for the given name"""
        # Convert name to symbol ID, replacing underscores with dashes
        normalized_name = name.replace('_', '-')
        symbol_id = f"icons.{normalized_name}"
        
        # Load sprite file if not already loaded
        if not cls._symbol_cache:
            cls._symbol_cache = cls._load_sprite_file()
            
        if symbol_id not in cls._symbol_cache:
            # Try the underscore version as fallback
            alt_symbol_id = f"icons.{name}"
            if alt_symbol_id not in cls._symbol_cache:
                logger.debug(f"Icon '{name}' not found in available icons: {sorted(cls._symbol_cache.keys())}")
                raise AttributeError(f"Icon '{name}' not found")
            symbol_id = alt_symbol_id
        
        def icon_method(*args, **kwargs) -> 'Icon':
            size = Size.MD
            style = Style.OG
            classes = ""
            
            # Process args looking for Size, Style, or string classes
            for arg in args:
                if isinstance(arg, Size):
                    size = arg
                elif isinstance(arg, Style):
                    style = arg
                elif isinstance(arg, str):
                    if any(size_class in arg for size_class in ["w-", "h-", "size-"]):
                        size = arg
                    else:
                        classes = arg
            
            # kwargs override args if specified
            size = kwargs.get('size', size)
            style = kwargs.get('style', style)
            classes = kwargs.get('cls', classes)
            
            return cls(name=symbol_id, size=size, style=style, cls=classes)
        
        return icon_method
    
    @classmethod
    @lru_cache
    def _load_sprite_file(cls) -> Dict[str, str]:
        """Load and parse the sprite file once, caching the result"""
        sprite_path = IconConfig.get_sprite_path()
        logger.info(f"Loading sprite file from: {sprite_path.absolute()}")
        
        if not sprite_path.exists():
            logger.error(f"Sprite file not found at: {sprite_path.absolute()}")
            raise FileNotFoundError("sprite.svg not found. Run build_sprites first.")
        
        try:
            tree = ET.parse(sprite_path)
            root = tree.getroot()
            
            # Register the SVG namespace
            ns = {'svg': 'http://www.w3.org/2000/svg'}
            symbols = {}
            
            for symbol in root.findall('.//svg:symbol', namespaces=ns):
                symbol_id = symbol.get('id')
                if not symbol_id:
                    continue
                
                # Remove namespace prefixes from tags
                for elem in symbol.iter():
                    elem.tag = elem.tag.split('}')[-1]
                
                # Convert to string without namespace declarations
                symbol_str = ET.tostring(symbol, encoding='unicode')
                symbol_str = symbol_str.replace(' xmlns:ns0="http://www.w3.org/2000/svg"', '')
                
                symbols[symbol_id] = symbol_str
            
            logger.debug(f"Loaded {len(symbols)} symbols: {sorted(symbols.keys())}")
            return symbols
            
        except ET.ParseError as e:
            logger.error(f"Parse error in sprite file: {e}")
            raise ValueError("Invalid sprite.svg format") from e
    
    @classmethod
    def _load_symbol(cls, icon_id: str) -> str:
        """Load symbol definition from sprite.svg"""
        if not cls._symbol_cache:
            cls._symbol_cache = cls._load_sprite_file()
        # Convert any remaining / to . when looking up in cache
        cache_id = icon_id.replace("/", ".")
        return cls._symbol_cache.get(cache_id, "")
    
    @classmethod
    def get_sprite_defs(cls) -> NotStr:
        """Get SVG definitions for all icons used on the current page"""
        if not cls._page_icons:
            return NotStr("")
        
        symbols = [
            cls._load_symbol(icon_id)
            for icon_id in cls._page_icons
        ]
        
        symbols = [s for s in symbols if s]  # Filter out empty symbols
        logger.debug(f"Generated {len(symbols)} symbol definitions")
        
        return NotStr(f"""
            <svg xmlns="http://www.w3.org/2000/svg" style="display:none">
                {' '.join(symbols)}
            </svg>
        """)
    
    @staticmethod
    def _get_og_classes(symbol_xml: str) -> list[str]:
        """Extract OG classes from symbol XML based on data-og-* attributes"""
        symbol = ET.fromstring(symbol_xml)
        classes = []
        
        # Base styling based on pattern
        pattern = symbol.get('data-og-pattern')
        if pattern == 'stroke':
            classes.extend(['fill-none', 'stroke-current'])
        elif pattern == 'fill':
            classes.extend(['fill-current'])
        elif pattern == 'mixed':
            if symbol.get('data-og-fill') == 'none':
                classes.append('fill-none')
            if symbol.get('data-og-fill') == 'currentColor':
                classes.append('fill-current')
            if symbol.get('data-og-stroke') == 'currentColor':
                classes.append('stroke-current')
        
        # Additional style attributes
        if symbol.get('data-og-stroke-width'):
            classes.append(f"stroke-{symbol.get('data-og-stroke-width')}")
        if symbol.get('data-og-fill-rule'):
            classes.append(f"fill-rule-{symbol.get('data-og-fill-rule')}")
        if symbol.get('data-og-fill-opacity'):
            classes.append(f"fill-opacity-{symbol.get('data-og-fill-opacity')}")
        if symbol.get('data-og-opacity'):
            classes.append(f"opacity-{symbol.get('data-og-opacity')}")
        
        return classes
    
    def __ft__(self) -> NotStr:
        """Generate FastHTML node with appropriate classes"""
        base_classes = ["inline-block"]
        
        # Add size classes
        size_classes = (
            config.sizes.get(self.size, config.sizes[Size.MD])
            if isinstance(self.size, Size)
            else self.size
        )
        base_classes.append(size_classes)
        
        # Add style classes
        if self.style == Style.OG:
            icon_id = str(self.name).replace("/", ".")
            if icon_id in self._symbol_cache:
                base_classes.extend(self._get_og_classes(self._symbol_cache[icon_id]))
        else:
            style_classes = self.style.value if isinstance(self.style, Style) else self.style
            base_classes.extend(style_classes.split())
        
        # Merge all classes
        default_classes = " ".join(base_classes)
        final_classes = tw_merge(default_classes, self.cls) if self.cls else default_classes
        
        icon_id = str(self.name).replace("/", ".")
        self._page_icons.add(icon_id)
        
        return NotStr(
            f"""<svg class="{final_classes}" data-icon="{icon_id}">
                <use href="#{icon_id}"/>
            </svg>"""
        )