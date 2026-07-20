# core/states/menu/button.py
import pygame


class MenuButton:
    """Класс кнопки главного меню"""
    
    def __init__(self, rect, icon, title, subtitle=""):
        self.rect = rect
        self.icon = icon
        self.title = title
        self.subtitle = subtitle
        self.hovered = False
    
    def handle_hover(self, pos):
        """Обновляет состояние наведения"""
        self.hovered = self.rect.collidepoint(pos)
        return self.hovered
    
    def handle_click(self, pos):
        """Проверяет клик по кнопке"""
        return self.rect.collidepoint(pos)