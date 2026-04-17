"""
main.py — Entry point de Jarvis.
"""
import sys
import os

# Asegurar que la raíz del proyecto esté en el path
sys.path.insert(0, os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QFontDatabase
from ui.main_window import MainWindow


def _load_stylesheet(app: QApplication) -> None:
    qss_path = os.path.join(os.path.dirname(__file__), "ui", "style.qss")
    try:
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print(f"[ADVERTENCIA] No se encontró style.qss en {qss_path}")


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Jarvis")
    app.setApplicationVersion("2.0")

    # Fuente base
    app.setFont(QFont("Segoe UI", 13))

    # Stylesheet
    _load_stylesheet(app)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
