# core/opengl/procedural.py
"""Процедурные текстуры для батча: мягкие круги, тени, искры.

Генерируются один раз и живут в атласе под служебными именами.
"""
import pygame
import math


def soft_circle(radius: int = 32) -> pygame.Surface:
    """Белый круг с плавным затуханием к краю. Цвет задаётся при отрисовке квада."""
    size = radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    for r in range(radius, 0, -1):
        # квадратичное затухание — ярче в центре
        t = r / radius
        alpha = int(255 * (1.0 - t) ** 2)
        pygame.draw.circle(surf, (255, 255, 255, alpha), (radius, radius), r)
    return surf


def hard_circle(radius: int = 16) -> pygame.Surface:
    """Плотный круг с тонкой мягкой кромкой (для частиц-капель)."""
    size = radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    pygame.draw.circle(surf, (255, 255, 255, 255), (radius, radius), radius - 2)
    pygame.draw.circle(surf, (255, 255, 255, 120), (radius, radius), radius, 2)
    return surf


def shadow_ellipse(w: int = 30, h: int = 10) -> pygame.Surface:
    surf = pygame.Surface((w, h), pygame.SRCALPHA, 32)
    pygame.draw.ellipse(surf, (0, 0, 0, 255), (0, 0, w, h))
    return surf


def vignette(size: int = 256) -> pygame.Surface:
    """Радиальное затемнение к краям: белый = прозрачно в центре,
    альфа растёт к краям. Цвет задаётся при отрисовке (обычно чёрный)."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    cx = cy = size / 2
    max_d = (2 * (size / 2) ** 2) ** 0.5
    px = pygame.PixelArray(surf)
    for y in range(size):
        for x in range(size):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 / max_d
            # альфа 0 в центре, плавно до 255 на углах (степень — крутизна)
            a = int(255 * max(0.0, (d - 0.45) / 0.55) ** 1.6)
            px[x, y] = (255, 255, 255, a)
    del px
    return surf


def ensure_builtins(renderer):
    """Гарантирует наличие служебных текстур в атласе. Идемпотентно."""
    if not renderer.has_texture('__soft__'):
        renderer.load_texture('__soft__', soft_circle(32))
    if not renderer.has_texture('__dot__'):
        renderer.load_texture('__dot__', hard_circle(16))
    if not renderer.has_texture('__shadow__'):
        renderer.load_texture('__shadow__', shadow_ellipse(30, 10))
    if not renderer.has_texture('__vignette__'):
        renderer.load_texture('__vignette__', vignette(256))
