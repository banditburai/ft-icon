from fasthtml.common import *
from fasthtml.svg import *

class ExtendedPathFT(PathFT):
    def l(self, x, y):
        "Relative line to."
        return self._append_cmd(f'l{x} {y}')

    def m(self, dx, dy):
        "Relative move to."
        return self._append_cmd(f'm{dx} {dy}')

    def c(self, dx1, dy1, dx2, dy2, dx, dy):
        "Relative cubic Bézier curve."
        return self._append_cmd(f'c{dx1} {dy1} {dx2} {dy2} {dx} {dy}')

    def s(self, dx2, dy2, dx, dy):
        "Relative smooth cubic Bézier curve."
        return self._append_cmd(f's{dx2} {dy2} {dx} {dy}')

    def q(self, dx1, dy1, dx, dy):
        "Relative quadratic Bézier curve."
        return self._append_cmd(f'q{dx1} {dy1} {dx} {dy}')

    def t(self, dx, dy):
        "Relative smooth quadratic Bézier curve."
        return self._append_cmd(f't{dx} {dy}')

    def a(self, rx, ry, x_axis_rotation, large_arc_flag, sweep_flag, dx, dy):
        "Relative elliptical arc."
        return self._append_cmd(f'a{rx} {ry} {x_axis_rotation} {large_arc_flag} {sweep_flag} {dx} {dy}')

    def h(self, dx):
        "Relative horizontal line to."
        return self._append_cmd(f'h{dx}')

    def v(self, dy):
        "Relative vertical line to."
        return self._append_cmd(f'v{dy}')
    
# Override the original Path function with our extended version
def Path(*args, **kwargs):
    kwargs['ft_cls'] = ExtendedPathFT
    return ft_svg('path', *args, **kwargs)