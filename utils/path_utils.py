# utils/path_utils.py
import os
import sys
import json

def resource_path(relative_path):
    """Получить путь к файлу, работает и для .exe, и для .py"""
    try:
        # PyInstaller создаёт временную папку _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def get_data_path(relative_path):
    """Получить путь к данным (создаёт папку, если нужно)"""
    path = resource_path(relative_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path

def get_save_path(filename="game.db"):
    """
    Путь к файлу сохранения (в папке saves рядом с игрой)
    Теперь работает правильно на всех системах
    """
    # Используем папку, где находится main.py или .exe
    if getattr(sys, 'frozen', False):
        # Запущено как .exe
        base_path = os.path.dirname(sys.executable)
    else:
        # Запущено как .py
        base_path = os.path.dirname(os.path.abspath(__file__))
        # Поднимаемся на уровень выше (из utils/ в корень)
        base_path = os.path.dirname(base_path)
    
    save_dir = os.path.join(base_path, "saves")
    
    # Создаём папку, если её нет
    try:
        os.makedirs(save_dir, exist_ok=True)
    except PermissionError:
        # Если нет прав, используем папку пользователя
        save_dir = os.path.join(os.path.expanduser("~"), "Documents", "ZombieTowerDefense", "saves")
        os.makedirs(save_dir, exist_ok=True)
    
    return os.path.join(save_dir, filename)