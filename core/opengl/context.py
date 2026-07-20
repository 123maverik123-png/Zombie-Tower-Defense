# core/opengl/context.py
"""OpenGL контекст поверх окна pygame."""
import moderngl


class GLContext:
    """Владеет moderngl-контекстом. Обычный объект, не синглтон."""

    def __init__(self):
        self.ctx: moderngl.Context | None = None
        self.width = 0
        self.height = 0

    def init(self, width: int, height: int, standalone: bool = False):
        """Создаёт контекст. Бросает RuntimeError с понятным текстом при неудаче."""
        self.width = width
        self.height = height
        try:
            self.ctx = moderngl.create_context(standalone=standalone)
        except Exception as e:
            raise RuntimeError(
                "Не удалось создать OpenGL 3.3 контекст. "
                "Обновите драйвер видеокарты или проверьте поддержку OpenGL 3.3.\n"
                f"Ошибка: {e}"
            ) from e

        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)
        if not standalone:
            self.ctx.viewport = (0, 0, width, height)

        info = self.ctx.info
        print(f"🎮 OpenGL {self.ctx.version_code}: "
              f"{info.get('GL_RENDERER', '?')} ({info.get('GL_VENDOR', '?')})")
        return self.ctx

    def resize(self, width: int, height: int):
        self.width = width
        self.height = height
        if self.ctx:
            self.ctx.viewport = (0, 0, width, height)

    def clear(self, color=(0.04, 0.04, 0.06, 1.0)):
        if self.ctx:
            self.ctx.clear(*color)

    def destroy(self):
        if self.ctx:
            self.ctx.release()
            self.ctx = None
