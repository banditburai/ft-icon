# ============================================================================
#  FastHTML + TailwindCSS + DaisyUI Template
# ============================================================================
from fasthtml.common import *
from ft_icon import Icon, Size, Style, IconSpriteMiddleware
from icon_types import IconType


Icon: IconType

styles = Link(rel="stylesheet", href="/styles/output.css", type="text/css")

app, rt = fast_app(
    pico=False,
    surreal=False,
    live=True,
    hdrs=(styles,),
    htmlkw=dict(lang="en", dir="ltr", data_theme="dark"),
    bodykw=dict(cls="min-h-screen bg-base-100"),
    middleware=[IconSpriteMiddleware]
)

@rt("/")
def get():
    return Div(
        Div(
            H1("Icon Demo", 
               cls="text-2xl font-bold mb-6"),
            
            # Icon examples
            Div(                
                Icon.home(Style.OUTLINE, "text-orange-500"),  
                Icon.menu_bars(cls="stroke-current stroke-2 fill-none text-primary"),
                Icon.smol_sun(),                
                Icon.heart(Size.LG),
                Icon.user(Size.MD),                
                Icon.lightning(Style.OUTLINE, Size.LG),
                                
                Icon.moon(Size.XL, Style.DUOTONE, cls="text-secondary"),                                
                Icon.star("h-16 w-16", "fill-current stroke-2"),

                Icon.heart(Size.XL, Style.SOLID,"text-red-500"),
                cls="flex gap-4 items-center"
            ),
            
            cls="text-center"
        ),
        cls="min-h-screen flex items-center justify-center"
    )

if __name__ == "__main__":
    serve()