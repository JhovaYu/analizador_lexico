"""
token_table.py — TokenTableWidget: tabla de tokens con chips de color.

Fix: Eliminado _ChipLabel + setCellWidget() — causaba doble render en columna Tipo.
     Ahora se usa QTableWidgetItem con colores directos (background + foreground),
     lo que es sortable y sin superposición visual.
"""
from __future__ import annotations
from typing import List, Dict, Any

from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QBrush

Token = Dict[str, Any]

# Mapa tipo → (color chip fondo, color chip texto)
TYPE_COLORS: Dict[str, tuple] = {
    "Palabra Reservada": ("#D4EFEF", "#006565"),
    "Identificador":     ("#EBEBEB", "#3A3A3A"),
    "Número Entero":     ("#DBEAFE", "#1E6BB8"),
    "Número Real":       ("#DBEAFE", "#1367A8"),
    "Cadena":            ("#FDE8D8", "#8B4823"),
    "Operador":          ("#FEF0E0", "#B05A00"),
    "Delimitador":       ("#F0F0F0", "#5A5A5A"),
    "RESERVED":          ("#D4EFEF", "#006565"),
    "IDENTIFIER":        ("#EBEBEB", "#3A3A3A"),
}

ERROR_BG = QColor("#FDECEA")
MONO_FONT = QFont("Fira Code", 12)


class TokenTableWidget(QTableWidget):
    """Tabla de tokens con 4 columnas: Token | Atributo | Tipo | Línea."""

    row_clicked = pyqtSignal(int)  # emite el número de línea del token

    HEADERS = ["Token", "Atributo", "Tipo", "Línea"]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("token_table")
        self._setup_table()

    def _setup_table(self) -> None:
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(self.HEADERS)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(False)
        self.setSortingEnabled(True)

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(1, 90)
        self.setColumnWidth(3, 60)

        self.cellClicked.connect(self._on_cell_clicked)

    def _on_cell_clicked(self, row: int, _col: int) -> None:
        item = self.item(row, 3)
        if item:
            try:
                self.row_clicked.emit(int(item.text()))
            except ValueError:
                pass

    def load_tokens(self, tokens: List[Token]) -> None:
        """Cargar lista de tokens con animación de fade-in secuencial."""
        self.setSortingEnabled(False)
        self.setRowCount(0)
        self.setRowCount(len(tokens))

        ANIMATE_MAX = 20
        for idx, tok in enumerate(tokens):
            self._fill_row(idx, tok)
            if idx < ANIMATE_MAX:
                self.setRowHidden(idx, True)

        self.setSortingEnabled(True)

        animate_count = min(ANIMATE_MAX, len(tokens))
        for idx in range(animate_count):
            QTimer.singleShot(idx * 50, lambda i=idx: self.setRowHidden(i, False))
        for idx in range(animate_count, len(tokens)):
            self.setRowHidden(idx, False)

    def _make_item(
        self,
        text: str,
        align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
        fg: str | None = None,
        bg: QColor | None = None,
    ) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFont(MONO_FONT)
        item.setTextAlignment(align)
        if fg:
            item.setForeground(QBrush(QColor(fg)))
        if bg:
            item.setBackground(QBrush(bg))
        return item

    def _fill_row(self, row: int, tok: Token) -> None:
        is_error = tok.get("attribute", 0) == -1
        center = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignCenter
        left   = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft

        row_bg = ERROR_BG if is_error else None

        # Col 0: Token
        col0 = self._make_item(
            str(tok.get("token", "")),
            align=left,
            fg="#C0392B" if is_error else None,
            bg=row_bg,
        )
        self.setItem(row, 0, col0)

        # Col 1: Atributo
        col1 = self._make_item(
            str(tok.get("attribute", "")),
            align=center,
            bg=row_bg,
        )
        self.setItem(row, 1, col1)

        # Col 2: Tipo — un único QTableWidgetItem con colores del chip
        type_str = str(tok.get("type", ""))
        chip_bg_hex, chip_fg_hex = TYPE_COLORS.get(type_str, ("#EBEBEB", "#3A3A3A"))
        if is_error:
            chip_bg_hex, chip_fg_hex = "#FDECEA", "#C0392B"

        col2 = self._make_item(
            type_str,
            align=center,
            fg=chip_fg_hex,
            bg=QColor(chip_bg_hex),
        )
        # Bold para el chip
        bold_font = QFont(MONO_FONT)
        bold_font.setBold(True)
        col2.setFont(bold_font)
        self.setItem(row, 2, col2)

        # Col 3: Línea
        col3 = self._make_item(
            str(tok.get("line", "")),
            align=center,
            bg=row_bg,
        )
        self.setItem(row, 3, col3)

        self.setRowHeight(row, 34)

    def clear_tokens(self) -> None:
        self.setRowCount(0)
