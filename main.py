#!/usr/bin/env python3
"""
VoluptAS - Universal QA Functional Coverage and Traceability Tool
Main entry point for the application

Author: Anatol-19
Date: 2025-10-13
"""

import sys
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.config import Config


def main():
    """
    Главная функция запуска приложения
    """
    # Инициализация конфигурации
    config = Config()
    
    # Создание приложения PyQt6
    app = QApplication(sys.argv)
    app.setApplicationName("VoluptAS")
    app.setOrganizationName("Anatol-19")
    app.setOrganizationDomain("github.com/Anatol-19")
    
    # Создание и отображение главного окна
    main_window = MainWindow(config)
    main_window.show()
    
    # Запуск event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
