#!/usr/bin/env python3
"""
Простой подсчет файлов и строк в проекте
Запуск: python count_project.py
"""

import os
from pathlib import Path

# Путь к проекту (текущая папка)
PROJECT_ROOT = Path(__file__).parent

# Расширения для подсчета
EXTENSIONS = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.html': 'HTML',
    '.css': 'CSS',
    '.json': 'JSON',
    '.md': 'Markdown',
    '.txt': 'Text',
    '.sql': 'SQL',
    '.toml': 'TOML',
    '.yml': 'YAML',
    '.yaml': 'YAML',
    '.sh': 'Shell',
    '.bat': 'Batch',
    '.ps1': 'PowerShell',
    '.xml': 'XML',
}

def count_file(filepath):
    """Считает строки в файле"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return len(f.readlines())
    except:
        return 0

def main():
    print("=" * 60)
    print(f"📊 СТАТИСТИКА ПРОЕКТА")
    print("=" * 60)
    print(f"📂 {PROJECT_ROOT}")
    print("-" * 60)
    
    total_files = 0
    total_lines = 0
    by_ext = {}
    
    # Обходим все файлы
    for filepath in PROJECT_ROOT.rglob('*'):
        # Пропускаем системные папки
        if any(p in str(filepath) for p in ['__pycache__', '.git', 'venv', 'env', 'backups']):
            continue
        
        if filepath.is_file():
            ext = filepath.suffix.lower()
            # Считаем только файлы с известными расширениями
            if ext in EXTENSIONS:
                lines = count_file(filepath)
                total_files += 1
                total_lines += lines
                
                by_ext[ext] = by_ext.get(ext, 0) + 1
    
    # Вывод
    print(f"\n📄 Всего файлов: {total_files}")
    print(f"📝 Всего строк: {total_lines:,}")
    print("-" * 60)
    
    # По расширениям
    print("\n📂 По расширениям:")
    for ext, count in sorted(by_ext.items(), key=lambda x: x[1], reverse=True):
        name = EXTENSIONS.get(ext, ext)
        print(f"  {name:12} {count:4} файлов")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()