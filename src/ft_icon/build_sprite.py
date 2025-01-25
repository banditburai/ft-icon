from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Optional, Dict, List, Literal, Union
import tomllib
import sys
import logging
import argparse
import os

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(message)s')

@dataclass
class IconConfig:
    icons_dir: Path
    output_dir: Path
    types_path: Path
    
    @staticmethod
    def get_sprite_path() -> Path:
        """Get sprite path from environment or use default"""
        return Path(os.getenv('FT_ICON_OUTPUT_DIR', 'static')) / 'sprite.svg'
    
def build_sprites(icons_dir: Path, output_dir: Path, types_path: Optional[Path] = None) -> None:
    """Build SVG sprite sheet from individual SVG files"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create root SVG element with proper namespace
    root_svg = ET.Element("svg", {
        "xmlns": "http://www.w3.org/2000/svg",
        "style": "display:none"
    })
    
    categories: Dict[str, List[str]] = {}
    
    for svg_file in icons_dir.rglob("*.svg"):
        category = svg_file.parent.name if svg_file.parent.name != icons_dir.name else "icons"
        icon_name = svg_file.stem
        
        try:
            symbol = _create_symbol_from_svg(svg_file, f"{category}/{icon_name}")
            root_svg.append(symbol)
            
            # Track for type generation
            categories.setdefault(category, []).append(icon_name)
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse {svg_file}: {e}")
            continue
    
    # Use the same sprite path method
    sprite_path = IconConfig.get_sprite_path()
    _write_sprite_file(sprite_path, root_svg)
    
    # Generate types if path provided
    if types_path:
        _generate_types(types_path, categories)

def _create_symbol_from_svg(svg_file: Path, symbol_id: str) -> ET.Element:
    """Create a symbol element from an SVG file"""
    tree = ET.parse(svg_file)
    svg_root = tree.getroot()
    
    # Create symbol with basic attributes
    symbol = ET.Element("symbol")
    symbol.set("id", symbol_id.replace("_", "-").replace("/", "."))
    symbol.set("viewBox", svg_root.get("viewBox", "0 0 24 24"))
    
    # Track dominant style pattern
    has_stroke = False
    has_fill = False
    
    # Collect all unique style attributes from the SVG
    styles = {
        'stroke': None,
        'stroke-width': None,
        'stroke-linecap': None,
        'stroke-linejoin': None,
        'fill': None,
        'fill-rule': None,
        'fill-opacity': None,
        'opacity': None
    }
    
    # Check root element first, then its descendants
    elements = [svg_root] + list(svg_root.iter())
    
    for elem in elements:
        # Parse both direct attributes and style attribute
        style_dict = {}
        if 'style' in elem.attrib:
            style_dict.update(parse_style_attribute(elem.attrib['style']))
        
        for style in styles:
            # Check both direct attribute and style attribute
            attr_value = elem.attrib.get(style) or style_dict.get(style)
            if attr_value and styles[style] is None:
                # Clean stroke-width values (e.g. "2px" -> "2")
                if style == 'stroke-width' and attr_value.endswith('px'):
                    attr_value = attr_value[:-2]
                
                styles[style] = attr_value
                if style.startswith('stroke'):
                    has_stroke = True
                elif style.startswith('fill'):
                    has_fill = True
    
    # Set pattern attribute to help with styling
    if has_stroke and not has_fill:
        symbol.set('data-og-pattern', 'stroke')
    elif has_fill and not has_stroke:
        symbol.set('data-og-pattern', 'fill')
    else:
        symbol.set('data-og-pattern', 'mixed')
    
    # Apply collected styles to symbol level
    for style, value in styles.items():
        if value is not None:
            symbol.set(f'data-og-{style}', value)
    
    # Copy structure without style attributes
    def copy_element(src: ET.Element, dest: ET.Element):
        for child in src:
            tag = child.tag.split('}')[-1]
            new_elem = ET.SubElement(dest, tag)
            # Copy only non-style attributes
            for key, value in child.attrib.items():
                if key not in styles:
                    new_elem.set(key, value)
            copy_element(child, new_elem)
    
    copy_element(svg_root, symbol)
    return symbol

def parse_style_attribute(style_str: str) -> Dict[str, str]:
    """Parse SVG style attribute into key-value pairs"""
    return dict(
        item.strip().split(":", 1) 
        for item in style_str.split(";") 
        if ":" in item
    )

def _write_sprite_file(sprite_path: Path, root_svg: ET.Element) -> None:
    """Write the sprite file with clean XML output"""
    tree = ET.ElementTree(root_svg)
    ET.indent(tree, space="  ")
    
    with open(sprite_path, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n')
        f.write(ET.tostring(root_svg, encoding='unicode', method='xml'))

def _generate_types(types_path: Path, categories: Dict[str, List[str]]) -> None:
    """Generate a Python file with type hints"""
    with open(types_path, 'w', encoding='utf-8') as f:
        f.write("# Generated file - do not edit directly\n\n")
        f.write("from typing import Protocol\n")
        f.write("from ft_icon.icon import Icon\n\n")
                
        f.write("# <!-- Tailwind scan triggers --> \n")
        f.write("# [stroke-linecap:round] [stroke-linejoin:round] \n")
        
        f.write("class IconClass(Protocol):\n")
        f.write('    """Available icon methods"""\n')
        
        for category, icons in categories.items():
            for icon in icons:
                name = icon.replace("-", "_").lower()
                f.write(f"    @classmethod\n")
                f.write(f"    def {name}(cls, *args, **kwargs) -> Icon: ...\n")
        
        f.write("\n# Type hint for Icon class\n")
        f.write("IconType = IconClass\n")

def main() -> None:
    """CLI entry point - builds sprites"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--icons-dir', help='Icons source directory')
    parser.add_argument('--output-dir', help='Output directory')
    parser.add_argument('--types-path', help='Path for generated types file')
    
    args = parser.parse_args()
    cwd = Path.cwd()
    
    # Set environment variable for Icon class to use
    if args.output_dir:
        os.environ['FT_ICON_OUTPUT_DIR'] = str(Path(args.output_dir).resolve())
    
    config = IconConfig(
        icons_dir=Path(args.icons_dir or os.getenv('FT_ICON_SOURCE_DIR') or cwd / 'icons'),
        output_dir=Path(args.output_dir or os.getenv('FT_ICON_OUTPUT_DIR') or cwd / 'static'),
        types_path=Path(args.types_path or os.getenv('FT_ICON_TYPES_PATH') or cwd / 'icon_types.py')
    )
    
    logger.info(f"📁 Icons directory: {config.icons_dir}")
    logger.info(f"📂 Output directory: {config.output_dir}")
    logger.info(f"📄 Types path: {config.types_path}")
    
    if not config.icons_dir.exists():
        logger.error(f"Icons directory not found at {config.icons_dir}")
        sys.exit(1)
        
    build_sprites(config.icons_dir, config.output_dir, config.types_path)
    logger.info(f"✅ Built sprite file at {IconConfig.get_sprite_path()}")
    logger.info(f"✅ Generated types at {config.types_path}")

if __name__ == "__main__":
    main()