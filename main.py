import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.config import Config

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Настройка логирования с ротацией
log_dir = project_root / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'voluptas.log'

file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s [%(levelname)-8s] %(name)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(
    '%(asctime)s [%(levelname)-8s] %(message)s',
    datefmt='%H:%M:%S'
))

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[file_handler, console_handler]
)

logger = logging.getLogger(__name__)
logger.info("="*60)
logger.info(f"VoluptAS starting... Working directory: {project_root}")
logger.info(f"Log file: {log_file}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    config = Config()
    window = MainWindow(config)
    window.show()
    sys.exit(app.exec())
