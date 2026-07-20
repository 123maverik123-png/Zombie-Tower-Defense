# core/opengl/ui_overlay.py
"""UI-оверлей: pygame рисует на прозрачную поверхность, GPU показывает её поверх сцены."""
import pygame
import moderngl
import numpy as np

from .atlas import surface_swizzle

_VERTEX_SHADER = """
#version 330
in vec2 in_position;
in vec2 in_texcoord;
out vec2 v_texcoord;
void main() {
    gl_Position = vec4(in_position, 0.0, 1.0);
    v_texcoord = in_texcoord;
}
"""

_FRAGMENT_SHADER = """
#version 330
uniform sampler2D u_texture;
in vec2 v_texcoord;
out vec4 f_color;
void main() {
    f_color = texture(u_texture, v_texcoord);
}
"""


class UIOverlay:
    def __init__(self, ctx: moderngl.Context, width: int, height: int):
        self.ctx = ctx
        self.width = width
        self.height = height

        self.surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
        self.texture = ctx.texture((width, height), 4)
        self.texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.texture.swizzle = surface_swizzle(self.surface)

        self.program = ctx.program(vertex_shader=_VERTEX_SHADER,
                                   fragment_shader=_FRAGMENT_SHADER)
        self.program['u_texture'].value = 0

        # Fullscreen quad, V перевёрнут (экранные координаты pygame сверху вниз)
        vertices = np.array([
            -1.0, -1.0, 0.0, 1.0,
             1.0, -1.0, 1.0, 1.0,
             1.0,  1.0, 1.0, 0.0,
            -1.0, -1.0, 0.0, 1.0,
             1.0,  1.0, 1.0, 0.0,
            -1.0,  1.0, 0.0, 0.0,
        ], dtype=np.float32)
        self.vbo = ctx.buffer(vertices.tobytes())
        self.vao = ctx.vertex_array(
            self.program,
            [(self.vbo, '2f 2f', 'in_position', 'in_texcoord')]
        )

    def begin_frame(self) -> pygame.Surface:
        """Очищает поверхность и возвращает её для pygame-отрисовки."""
        self.surface.fill((0, 0, 0, 0))
        return self.surface

    def render(self):
        """Загружает поверхность в текстуру и рисует поверх сцены."""
        self.texture.write(bytes(self.surface.get_view('1')))
        self.texture.use(0)
        self.vao.render(moderngl.TRIANGLES)

    def resize(self, width: int, height: int):
        if (width, height) == (self.width, self.height):
            return
        self.width = width
        self.height = height
        self.texture.release()
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
        self.texture = self.ctx.texture((width, height), 4)
        self.texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.texture.swizzle = surface_swizzle(self.surface)

    def destroy(self):
        self.texture.release()
        self.vao.release()
        self.vbo.release()
        self.program.release()
