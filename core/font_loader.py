# core/font_loader.py
import pygame
import os

def load_font(size, use_toxic=True):
    """
    Загружает шрифт ToxicRot для больших размеров,
    и стандартный для мелких
    """
    # Для размера меньше 30 — используем стандартный шрифт
    if size < 30:
        return pygame.font.Font(None, size)
    
    # Для больших размеров — пробуем ToxicRot
    if use_toxic:
        try:
            return pygame.font.Font("assets/fonts/ToxicRot-Regular.ttf", size)
        except:
            return pygame.font.Font(None, size)
    
    return pygame.font.Font(None, size)

def load_title_font(size):
    """Для заголовков — ToxicRot"""
    try:
        return pygame.font.Font("assets/fonts/ToxicRot-Regular.ttf", size)
    except:
        return pygame.font.Font(None, size)

def load_ui_font(size):
    """Для UI и кнопок — стандартный читаемый шрифт"""
    return pygame.font.Font(None, size)