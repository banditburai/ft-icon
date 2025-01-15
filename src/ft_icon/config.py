from dataclasses import dataclass
from enum import Enum
from typing import Dict, Union

class Size(str, Enum):
    XS = "xs"
    SM = "sm"
    MD = "md"
    LG = "lg"
    XL = "xl"
    
    # Responsive variants
    XS_TO_SM = "xs-to-sm"
    XS_TO_MD = "xs-to-md"
    XS_TO_LG = "xs-to-lg"
    SM_TO_MD = "sm-to-md"
    SM_TO_LG = "sm-to-lg"
    MD_TO_LG = "md-to-lg"
    MD_TO_XL = "md-to-xl"
    
    @classmethod
    def add(cls, name: str):
        """Add a new size enum value"""
        name = name.upper()
        if not hasattr(cls, name):
            cls._member_map_[name] = cls._value2member_map_[name.lower()] = cls(name.lower())
        return getattr(cls, name)

class Style(Enum):
    OG = ""  # No fill/stroke classes, preserve original colors
    SIMPLE = "fill-current"
    SOLID = "fill-current stroke-0"
    OUTLINE = "fill-none stroke-2 stroke-current"
    OUTLINE_THIN = "fill-none stroke-[1.5px] stroke-current"
    OUTLINE_THICK = "fill-none stroke-[4px] stroke-current"
    DUOTONE = "fill-current fill-opacity-20 stroke-[1.5px] stroke-current"
    BRAND = "fill-primary stroke-0 opacity-90"
    
    # Color variants
    SOLID_PRIMARY = "fill-primary stroke-0"
    SOLID_SECONDARY = "fill-secondary stroke-0"
    OUTLINE_PRIMARY = "fill-none stroke-[1.5px] stroke-primary"
    OUTLINE_SECONDARY = "fill-none stroke-[1.5px] stroke-secondary"
    
    # Opacity variants
    SIMPLE_FADED = "fill-current opacity-70"
    SOLID_FADED = "fill-current stroke-0 opacity-70"
    OUTLINE_FADED = "fill-none stroke-[1.5px] stroke-current opacity-70"

# Default mappings
DEFAULT_SIZES = {
    Size.XS: "h-4 w-4",
    Size.SM: "h-5 w-5",
    Size.MD: "h-6 w-6",
    Size.LG: "h-8 w-8",
    Size.XL: "h-10 w-10",
    
    # Responsive variants
    Size.XS_TO_SM: "h-4 w-4 md:h-5 md:w-5",
    Size.XS_TO_MD: "h-4 w-4 md:h-6 md:w-6",
    Size.XS_TO_LG: "h-4 w-4 md:h-8 md:w-8",
    Size.SM_TO_MD: "h-5 w-5 md:h-6 md:w-6",
    Size.SM_TO_LG: "h-5 w-5 md:h-8 md:w-8",
    Size.MD_TO_LG: "h-6 w-6 md:h-8 md:w-8",
    Size.MD_TO_XL: "h-6 w-6 md:h-10 md:w-10",
}

DEFAULT_STYLES = {
    Style.OG: "",  # No classes, preserve original colors
    Style.SIMPLE: "fill-current",
    Style.SOLID: "fill-current stroke-0",
    Style.OUTLINE: "fill-none stroke-2 stroke-current",
    Style.OUTLINE_THIN: "fill-none stroke-[1.5px] stroke-current",
    Style.OUTLINE_THICK: "fill-none stroke-[4px] stroke-current",
    Style.DUOTONE: "fill-current fill-opacity-20 stroke-[1.5px] stroke-current",
    Style.BRAND: "fill-primary stroke-0 opacity-90",
    
    # Color variants
    Style.SOLID_PRIMARY: "fill-primary stroke-0",
    Style.SOLID_SECONDARY: "fill-secondary stroke-0",
    Style.OUTLINE_PRIMARY: "fill-none stroke-[1.5px] stroke-primary",
    Style.OUTLINE_SECONDARY: "fill-none stroke-[1.5px] stroke-secondary",
    
    # Opacity variants
    Style.SIMPLE_FADED: "fill-current opacity-70",
    Style.SOLID_FADED: "fill-current stroke-0 opacity-70",
    Style.OUTLINE_FADED: "fill-none stroke-[1.5px] stroke-current opacity-70",
}

@dataclass
class IconConfig:
    """Configuration for icon sizes and styles"""
    sizes: Dict[Union[Size, str], str]
    styles: Dict[Union[Style, str], str]

# Global configuration instance
config = IconConfig(
    sizes=DEFAULT_SIZES.copy(),
    styles=DEFAULT_STYLES.copy(),
)

def configure(*, sizes: Dict[str, str] = None, styles: Dict[str, str] = None):
    """Update the global icon configuration
    
    Updates existing enum mappings or creates new ones:
    configure(
        sizes={"huge": "h-20 w-20", "sm": "h-4 w-4"},  # "sm" overrides existing
        styles={"fancy": "fill-current stroke-2", "simple": "fill-current"}  # "simple" overrides existing
    )
    """
    if sizes:
        for name, classes in sizes.items():
            size = Size.add(name) if name.upper() not in Size.__members__ else getattr(Size, name.upper())
            config.sizes[size] = classes
            
    if styles:
        for name, classes in styles.items():
            style = Style.add(name) if name.upper() not in Style.__members__ else getattr(Style, name.upper())
            config.styles[style] = classes 