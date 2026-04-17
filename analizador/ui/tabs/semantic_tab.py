"""
ui/tabs/semantic_tab.py — Tab Semántico. Dumb Component para tabla de símbolos y log de errores.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QListWidget, QLabel
from PyQt6.QtGui import QColor
from typing import List, Dict, Any

class SemanticTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Tabla de Símbolos
        lbl_sym = QLabel("Tabla de Símbolos")
        lbl_sym.setObjectName("section_title")
        layout.addWidget(lbl_sym)

        self.sym_table = QTableWidget()
        self.sym_table.setColumnCount(4)
        self.sym_table.setHorizontalHeaderLabels(["Nombre", "Tipo", "Línea", "¿Utilizada?"])
        self.sym_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.sym_table.verticalHeader().setVisible(False)
        self.sym_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.sym_table)

        # Log de Errores y Output
        lbl_err = QLabel("Registro de Análisis Semántico")
        lbl_err.setObjectName("section_title")
        layout.addWidget(lbl_err)

        self.error_list = QListWidget()
        self.error_list.setObjectName("error_list")
        layout.addWidget(self.error_list)

        self.setLayout(layout)

    def populate(self, symbols: List[Dict[str, Any]], errors: List[Any]) -> None:
        """Llena la información de símbolos y el log de validación."""
        # 1. Tabla de Símbolos
        self.sym_table.setRowCount(0)
        for row_idx, sym in enumerate(symbols):
            self.sym_table.insertRow(row_idx)
            is_warn = not sym.get("is_used", False)
            bg_color = QColor("#EEEEE8")  # Color por defecto neutro
            
            used_str = "Sí" if sym.get("is_used") else "No"
            
            items = [
                QTableWidgetItem(str(sym.get("name", ""))),
                QTableWidgetItem(str(sym.get("type_", ""))),
                QTableWidgetItem(str(sym.get("line", ""))),
                QTableWidgetItem(used_str)
            ]

            for col_idx, item in enumerate(items):
                item.setBackground(bg_color)
                # Resaltar en naranja si no se usa
                if is_warn and col_idx == 3:
                     item.setForeground(QColor("#D35400"))
                self.sym_table.setItem(row_idx, col_idx, item)

        # 2. Log de Errores
        self.error_list.clear()
        if not errors:
            self.error_list.addItem("✓ Análisis semántico finalizado sin errores críticos.")
        else:
            for err in errors:
                self.error_list.addItem(str(err))
