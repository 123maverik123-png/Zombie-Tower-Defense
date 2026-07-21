# core/opengl/atlas.py
"""Текстурный атлас: упаковывает спрайты в страницы 2048x2048.

Все входящие поверхности блитятся на CPU-страницу единого формата
(SRCALPHA 32bit), поэтому порядок каналов внутри страницы всегда один.
На GPU порядок исправляется swizzle'ом — без перестановки байтов на CPU.
"""
import pygame
import moderngl
from dataclasses import dataclass

PAGE_SIZE = 2048
_PAD = 1  # зазор между спрайтами против bleeding


@dataclass
class AtlasRegion:
    page: int
    x: int
    y: int
    w: int
    h: int
    u0: float = 0.0
    v0: float = 0.0
    u1: float = 0.0
    v1: float = 0.0

    def __post_init__(self):
        # Half-texel inset: сдвигаем UV на пол-пикселя внутрь региона, чтобы
        # при семплинге на границе не захватывался соседний пиксель атласа
        # (иначе слева/сверху появлялась полоса в 1px у прозрачных спрайтов).
        eps = 0.5 / PAGE_SIZE
        self.u0 = self.x / PAGE_SIZE + eps
        self.v0 = self.y / PAGE_SIZE + eps
        self.u1 = (self.x + self.w) / PAGE_SIZE - eps
        self.v1 = (self.y + self.h) / PAGE_SIZE - eps


def surface_swizzle(surface: pygame.Surface) -> str:
    """Определяет какой swizzle нужен GL-текстуре для байтов get_view('1')."""
    r_shift, g_shift, b_shift, a_shift = surface.get_shifts()
    order = sorted([(r_shift, 'R'), (g_shift, 'G'), (b_shift, 'B'), (a_shift or 24, 'A')])
    return ''.join(ch for _, ch in order)


class _Shelf:
    __slots__ = ('y', 'height', 'x')

    def __init__(self, y: int, height: int):
        self.y = y
        self.height = height
        self.x = 0


class _Page:
    """Одна страница атласа: CPU-поверхность + GPU-текстура + shelf-упаковка."""

    def __init__(self, ctx: moderngl.Context, index: int):
        self.index = index
        self.surface = pygame.Surface((PAGE_SIZE, PAGE_SIZE), pygame.SRCALPHA, 32)
        self.texture = ctx.texture((PAGE_SIZE, PAGE_SIZE), 4)
        self.texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.texture.swizzle = surface_swizzle(self.surface)
        self.shelves: list[_Shelf] = []
        self.next_y = 0

    def try_pack(self, w: int, h: int):
        """Возвращает (x, y) или None если не влезло."""
        pw, ph = w + _PAD, h + _PAD
        for shelf in self.shelves:
            if ph <= shelf.height and shelf.x + pw <= PAGE_SIZE:
                x, y = shelf.x, shelf.y
                shelf.x += pw
                return x, y
        if self.next_y + ph <= PAGE_SIZE:
            shelf = _Shelf(self.next_y, ph)
            self.shelves.append(shelf)
            self.next_y += ph
            x, y = shelf.x, shelf.y
            shelf.x += pw
            return x, y
        return None

    def upload_region(self, x: int, y: int, w: int, h: int):
        """Заливает регион CPU-страницы в GPU-текстуру."""
        region = pygame.Surface((w, h), pygame.SRCALPHA, 32)
        region.blit(self.surface, (0, 0), pygame.Rect(x, y, w, h))
        self.texture.write(bytes(region.get_view('1')), viewport=(x, y, w, h))

    def destroy(self):
        self.texture.release()


class TextureAtlas:
    def __init__(self, ctx: moderngl.Context):
        self.ctx = ctx
        self.pages: list[_Page] = []
        self.regions: dict[str, AtlasRegion] = {}
        # Белый пиксель — для цветных квадов (HP-бары, линии, молнии)
        white = pygame.Surface((2, 2), pygame.SRCALPHA, 32)
        white.fill((255, 255, 255, 255))
        self.white = self.add('__white__', white)

    def add(self, name: str, surface: pygame.Surface) -> AtlasRegion:
        """Добавляет спрайт в атлас (или возвращает уже существующий регион)."""
        existing = self.regions.get(name)
        if existing is not None:
            return existing

        w, h = surface.get_size()
        if w > PAGE_SIZE or h > PAGE_SIZE:
            scale = min(PAGE_SIZE / w, PAGE_SIZE / h)
            surface = pygame.transform.smoothscale(surface, (int(w * scale), int(h * scale)))
            w, h = surface.get_size()

        placed = None
        for page in self.pages:
            pos = page.try_pack(w, h)
            if pos:
                placed = (page, pos)
                break
        if placed is None:
            page = _Page(self.ctx, len(self.pages))
            self.pages.append(page)
            pos = page.try_pack(w, h)
            if pos is None:
                raise RuntimeError(f"Sprite '{name}' {w}x{h} не влезает в страницу атласа")
            placed = (page, pos)

        page, (x, y) = placed
        # Блит нормализует формат каналов к формату страницы
        page.surface.blit(surface, (x, y))
        page.upload_region(x, y, w, h)

        region = AtlasRegion(page.index, x, y, w, h)
        self.regions[name] = region
        return region

    def get(self, name: str) -> AtlasRegion | None:
        return self.regions.get(name)

    def has(self, name: str) -> bool:
        return name in self.regions

    def texture(self, page_index: int) -> moderngl.Texture:
        return self.pages[page_index].texture

    def clear(self):
        """Полный сброс (смена уровня/масштаба тайлов)."""
        for page in self.pages:
            page.destroy()
        self.pages.clear()
        self.regions.clear()
        white = pygame.Surface((2, 2), pygame.SRCALPHA, 32)
        white.fill((255, 255, 255, 255))
        self.white = self.add('__white__', white)

    def destroy(self):
        for page in self.pages:
            page.destroy()
        self.pages.clear()
        self.regions.clear()
