# core/opengl/batch.py
"""Батч-рендер квадов: один upload и минимум draw call'ов за кадр.

Квады накапливаются в numpy-массиве в порядке вызовов (порядок = слои).
Смена страницы атласа или режима блендинга начинает новый "run";
flush() рисует все run'ы подряд из одного VBO.
"""
import math
import numpy as np
import moderngl

from .atlas import AtlasRegion, TextureAtlas

BLEND_ALPHA = 0
BLEND_ADDITIVE = 1

_FLOATS_PER_VERTEX = 8   # x, y, u, v, r, g, b, a
_VERTS_PER_QUAD = 6
_START_CAPACITY = 4096   # квадов

_VERTEX_SHADER = """
#version 330
uniform vec2 u_screen_size;
in vec2 in_position;
in vec2 in_texcoord;
in vec4 in_color;
out vec2 v_texcoord;
out vec4 v_color;
void main() {
    vec2 ndc = (in_position / u_screen_size) * 2.0 - 1.0;
    gl_Position = vec4(ndc.x, -ndc.y, 0.0, 1.0);
    v_texcoord = in_texcoord;
    v_color = in_color;
}
"""

_FRAGMENT_SHADER = """
#version 330
uniform sampler2D u_texture;
in vec2 v_texcoord;
in vec4 v_color;
out vec4 f_color;
void main() {
    f_color = texture(u_texture, v_texcoord) * v_color;
}
"""


class SpriteBatch:
    def __init__(self, ctx: moderngl.Context, atlas: TextureAtlas, width: int, height: int):
        self.ctx = ctx
        self.atlas = atlas
        self.program = ctx.program(vertex_shader=_VERTEX_SHADER,
                                   fragment_shader=_FRAGMENT_SHADER)
        self.program['u_screen_size'].value = (float(width), float(height))
        self.program['u_texture'].value = 0

        self._capacity = _START_CAPACITY
        self._data = np.empty(self._capacity * _VERTS_PER_QUAD * _FLOATS_PER_VERTEX,
                              dtype=np.float32)
        self._quad_count = 0
        # runs: (page, blend, first_quad, quad_count)
        self._runs: list[list[int]] = []

        self.vbo = ctx.buffer(reserve=self._data.nbytes, dynamic=True)
        self.vao = ctx.vertex_array(
            self.program,
            [(self.vbo, '2f 2f 4f', 'in_position', 'in_texcoord', 'in_color')]
        )

    def set_screen_size(self, width: int, height: int):
        self.program['u_screen_size'].value = (float(width), float(height))

    def _grow(self):
        self._capacity *= 2
        new = np.empty(self._capacity * _VERTS_PER_QUAD * _FLOATS_PER_VERTEX,
                       dtype=np.float32)
        new[:self._data.size] = self._data
        self._data = new
        self.vbo.release()
        self.vbo = self.ctx.buffer(reserve=self._data.nbytes, dynamic=True)
        content = [(self.vbo, '2f 2f 4f', 'in_position', 'in_texcoord', 'in_color')]
        self.vao.release()
        self.vao = self.ctx.vertex_array(self.program, content)

    def draw(self, region: AtlasRegion, x: float, y: float,
             w: float, h: float, rotation: float = 0.0,
             color=(255, 255, 255, 255), blend: int = BLEND_ALPHA,
             centered: bool = True):
        """Добавляет квад. x,y — центр (centered=True) или левый верхний угол."""
        if self._quad_count >= self._capacity:
            self._grow()

        if not self._runs or self._runs[-1][0] != region.page or self._runs[-1][1] != blend:
            self._runs.append([region.page, blend, self._quad_count, 0])
        self._runs[-1][3] += 1

        if centered:
            cx, cy = x, y
        else:
            cx, cy = x + w * 0.5, y + h * 0.5

        hw, hh = w * 0.5, h * 0.5
        if rotation:
            rad = math.radians(rotation)
            c, s = math.cos(rad), math.sin(rad)
            corners = (
                (cx + (-hw) * c - (-hh) * s, cy + (-hw) * s + (-hh) * c),
                (cx + hw * c - (-hh) * s, cy + hw * s + (-hh) * c),
                (cx + hw * c - hh * s, cy + hw * s + hh * c),
                (cx + (-hw) * c - hh * s, cy + (-hw) * s + hh * c),
            )
        else:
            corners = (
                (cx - hw, cy - hh), (cx + hw, cy - hh),
                (cx + hw, cy + hh), (cx - hw, cy + hh),
            )

        r = color[0] / 255.0
        g = color[1] / 255.0
        b = color[2] / 255.0
        a = (color[3] if len(color) > 3 else 255) / 255.0

        u0, v0, u1, v1 = region.u0, region.v0, region.u1, region.v1
        (x0, y0), (x1, y1), (x2, y2), (x3, y3) = corners

        base = self._quad_count * _VERTS_PER_QUAD * _FLOATS_PER_VERTEX
        self._data[base:base + 48] = (
            x0, y0, u0, v0, r, g, b, a,
            x1, y1, u1, v0, r, g, b, a,
            x2, y2, u1, v1, r, g, b, a,
            x0, y0, u0, v0, r, g, b, a,
            x2, y2, u1, v1, r, g, b, a,
            x3, y3, u0, v1, r, g, b, a,
        )
        self._quad_count += 1

    def draw_rect(self, x: float, y: float, w: float, h: float,
                  color, blend: int = BLEND_ALPHA):
        """Цветной прямоугольник (левый верхний угол) — белый пиксель атласа."""
        self.draw(self.atlas.white, x, y, w, h, 0.0, color, blend, centered=False)

    def draw_line(self, x1: float, y1: float, x2: float, y2: float,
                  width: float, color, blend: int = BLEND_ALPHA):
        """Линия как повёрнутый квад."""
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy)
        if length < 0.001:
            return
        angle = math.degrees(math.atan2(dy, dx))
        self.draw(self.atlas.white, (x1 + x2) * 0.5, (y1 + y2) * 0.5,
                  length, width, angle, color, blend)

    def flush(self):
        """Заливает вершины на GPU и рисует все run'ы по порядку."""
        if self._quad_count == 0:
            return

        used = self._quad_count * _VERTS_PER_QUAD * _FLOATS_PER_VERTEX
        self.vbo.orphan()
        self.vbo.write(self._data[:used])

        ctx = self.ctx
        current_blend = -1
        for page, blend, first, count in self._runs:
            if blend != current_blend:
                if blend == BLEND_ADDITIVE:
                    ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE)
                else:
                    ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)
                current_blend = blend
            self.atlas.texture(page).use(0)
            self.vao.render(moderngl.TRIANGLES,
                            vertices=count * _VERTS_PER_QUAD,
                            first=first * _VERTS_PER_QUAD)

        if current_blend == BLEND_ADDITIVE:
            ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)

        self._quad_count = 0
        self._runs.clear()

    def destroy(self):
        self.vao.release()
        self.vbo.release()
        self.program.release()
