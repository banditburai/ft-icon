# FT-Icon

SVG sprite builder and Icon component system for FastHTML built on top of [tw-merge](https://github.com/banditburai/tw-merge) with Tailwind and DaisyUI. You could probably use this with any other CSS framework, just tweak the CSS classes and config defaults.

## Features

- Build SVG sprite sheets from individual SVG files
- Automatic type generation for available icons and IDE hints
- Tailwind CSS class merging support
- Just-in-time SVG injection - only icons used on the page are included
- Original SVG styles preserved with `Style.OG` or can be overridden with Tailwind classes
- Efficient symbol reuse - first usage defines the SVG, subsequent uses reference it
- Zero-overhead approach similar to Astro's icon system but with server-side SVG injection, icons are rendered during server-side page generation, no client-side loading or preloading required.

## Installation

```bash
pip install git+https://github.com/banditburai/ft-icon.git
```

## Usage

1. Set up your icons directory:
```
icons/
  ├── alert.svg
  ├── check.svg
  └── user.svg
```

2. Build the sprite sheet:
```bash
# After installation, run the build script
uv run build

# Optionally specify directories:
uv run build --icons-dir icons --output-dir static

# Or use environment variables:
export FT_ICON_SOURCE_DIR=icons
export FT_ICON_OUTPUT_DIR=static
uv run build
```

3. Set up your FastHTML app:
```python
from fasthtml.common import *
from ft_icon import Icon, Size, Style, IconSpriteMiddleware
from icon_types import IconType

# Type hint for better IDE support
Icon: IconType

app, rt = fast_app(
    # ... your other config ...
    middleware=[IconSpriteMiddleware]  # Add the middleware
)
```

4. Use icons in your components:
```python
def IconExamples():
    return Div(        
        Icon.home(Style.OUTLINE, "text-orange-500"),
        
        # Custom classes for styling
        Icon.menu_bars(cls="stroke-current stroke-2 fill-none text-primary"),
        
        # Original SVG styling
        Icon.smol_sun(),
        
        # Using size enums
        Icon.heart(Size.LG),
        Icon.user(Size.MD),
        
        # Combine style and size enums
        Icon.lightning(Style.OUTLINE, Size.LG),
        
        # Extra large duotone icon with color
        Icon.moon(Size.XL, Style.DUOTONE, cls="text-secondary"),
        
        # This svg doesn't exist so it will fallback to a question mark icon
        Icon.star("h-16 w-16", "fill-current stroke-2"),
        # Solid style with color
        Icon.heart(Size.XL, Style.SOLID, "text-red-500"),
        
        cls="flex gap-4 items-center"
    )
```

## Configuration

Environment variables:
- `FT_ICON_SOURCE_DIR`: Source directory for SVG icons (default: `./icons`)
- `FT_ICON_OUTPUT_DIR`: Output directory for sprite sheet (default: `./static`)
- `FT_ICON_TYPES_PATH`: Path for generated types file (default: `./icon_types.py`)

CLI arguments (override environment variables):
- `--icons-dir`: Source directory for SVG icons
- `--output-dir`: Output directory for sprite sheet
- `--types-path`: Path for generated types file

## Example

See the `example/` directory for a complete working example.

## License

MIT
