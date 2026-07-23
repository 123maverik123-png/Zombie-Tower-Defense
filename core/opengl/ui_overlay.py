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
        # Тройная буферизация текстуры: пишем каждый кадр в следующую из трёх.
        # Иначе texture.write() бьёт в текстуру, которую GPU ещё рисует из прошлого
        # кадра — драйвер NVIDIA плодит теневые копии (renaming), и в 2K они
        # (14 МБ каждая) копятся до заполнения VRAM. Ping-pong даёт текстуре 3
        # кадра «остыть», прежде чем в неё снова пишут — копии не нужны.
        self._textures = []
        for _ in range(3):
            tex = ctx.texture((width, height), 4)
            tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
            tex.swizzle = surface_swizzle(self.surface)
            self._textures.append(tex)
        self._tex_index = 0
        self.texture = self._textures[0]

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
        # Пишем в следующую текстуру цикла (тройная буферизация — см. __init__)
        self._tex_index = (self._tex_index + 1) % len(self._textures)
        self.texture = self._textures[self._tex_index]
        self.texture.write(bytes(self.surface.get_view('1')))
        self.texture.use(0)
        self.vao.render(moderngl.TRIANGLES)

    def resize(self, width: int, height: int):
        if (width, height) == (self.width, self.height):
            return
        self.width = width
        self.height = height
        for tex in self._textures:
            tex.release()
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
        self._textures = []
        for _ in range(3):
            tex = self.ctx.texture((width, height), 4)
            tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
            tex.swizzle = surface_swizzle(self.surface)
            self._textures.append(tex)
        self._tex_index = 0
        self.texture = self._textures[0]

    def destroy(self):
        for tex in self._textures:
            tex.release()
        self.vao.release()
        self.vbo.release()
        self.program.release()
