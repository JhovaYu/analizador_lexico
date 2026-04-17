"""
ui/tabs/lexical_tab.py — Tab Léxico. Dumb Component para visualizar tokens.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtGui import QColor
from typing import List, Dict, Any

class LexicalTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Línea", "Col", "Tipo", "Valor"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.table)
        self.setLayout(layout)

    def populate(self, tokens: List[Dict[str, Any]]) -> None:
        """
        Recibe una lista de diccionarios con la estructura:
        {'line': int, 'col': int, 'type': str, 'value': str, 'error': bool}
        """
        self.table.setRowCount(0)
        for row_idx, tok in enumerate(tokens):
            self.table.insertRow(row_idx)
            is_err = tok.get("error", False)
            bg_color = QColor("#FDECEA") if is_err else None
            fg_color = QColor("#C0392B") if is_err else None

            # Creación de celdas
            items = [
                QTableWidgetItem(str(tok.get("line", ""))),
                QTableWidgetItem(str(tok.get("col", ""))),
                QTableWidgetItem(str(tok.get("type", ""))),
                QTableWidgetItem(str(tok.get("value", "")))
            ]

            for col_idx, item in enumerate(items):
                if bg_color:
                    item.setBackground(bg_color)
                if fg_color:
                    item.setForeground(fg_color)
                self.table.setItem(row_idx, col_idx, item)
