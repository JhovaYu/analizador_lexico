"""
app.py — Ventana principal PyQt6 de Jarvis.

Layout:
  ┌─────────────────────────────────────────────────────────┐
  │ Topbar: Logo | Título | [Analizar] [Limpiar] [Exportar] │
  ├──────────────────────┬──────────────────────────────────┤
  │ Editor (60%)         │ Tabs: Léxico | Sintáctico |      │
  │                      │       Semántico (40%)            │
  ├──────────────────────┴──────────────────────────────────┤
  │ Grafo AST — QGraphicsView (35% altura, resizable)       │
  └─────────────────────────────────────────────────────────┘
"""
from __future__ import annotations
import csv
import sys
from typing import List, Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QTabWidget, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QStatusBar, QFileDialog, QApplication,
    QFrame,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QColor, QFont, QIcon

from ui.editor_panel import CodeEditorWidget
from ui.token_table import TokenTableWidget
from ui.ast_graph import ASTGraphWidget

from core.lexer import DFALexer
from core.ast_nodes import Program, ASTNode
from utils.error_handler import AnalysisError, Severity


# ---------------------------------------------------------------------------
# Worker thread para análisis (evitar congelar UI)
# ---------------------------------------------------------------------------

class _AnalysisWorker(QThread):
    finished = pyqtSignal(list, object, list, object)  # tokens, ast, sem_errors, sym_table
    error = pyqtSignal(str)

    def __init__(self, source: str) -> None:
        super().__init__()
        self._source = source

    def run(self) -> None:
        try:
            from core.lexer import DFALexer
            from core.parser import parse, ParseError
            from core.semantic import SemanticAnalyzer

            tokens = DFALexer().tokenize(self._source)

            ast_root: Optional[ASTNode] = None
            parse_error: Optional[str] = None
            try:
                ast_root = parse(self._source)
            except Exception as e:
                parse_error = str(e)

            sem_errors: List[AnalysisError] = []
            sym_table = None
            if ast_root is not None:
                analyzer = SemanticAnalyzer()
                sem_errors = analyzer.analyze(ast_root)
                sym_table = analyzer.symbol_table

            self.finished.emit(tokens, ast_root, sem_errors, sym_table)
        except Exception as e:
            self.error.emit(str(e))


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Jarvis — Analizador Léxico, Sintáctico y Semántico")
        self.resize(1280, 800)
        self.setMinimumSize(900, 600)

        self._worker: Optional[_AnalysisWorker] = None
        self._last_tokens: List = []

        self._build_ui()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Topbar
        root_layout.addWidget(self._build_topbar())

        # Main splitter (vertical: top-area | ast-graph)
        self._main_splitter = QSplitter(Qt.Orientation.Vertical)
        self._main_splitter.setChildrenCollapsible(False)

        # Top area splitter (horizontal: editor | right-panel)
        self._h_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._h_splitter.setChildrenCollapsible(False)

        # Editor
        self._editor = CodeEditorWidget()
        self._h_splitter.addWidget(self._editor)

        # Right panel
        self._h_splitter.addWidget(self._build_right_panel())
        self._h_splitter.setSizes([760, 520])

        self._main_splitter.addWidget(self._h_splitter)

        # AST Graph panel
        self._main_splitter.addWidget(self._build_ast_panel())
        self._main_splitter.setSizes([520, 280])

        root_layout.addWidget(self._main_splitter)

        # Status bar
        self._status = QStatusBar()
        self._status.showMessage("Listo.")
        self.setStatusBar(self._status)

        # Cursor position tracking
        self._editor.cursorPositionChanged.connect(self._update_cursor_pos)

    def _build_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("topbar")
        bar.setFixedHeight(48)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(8)

        # Logo SVG text
        logo = QLabel()
        logo.setText(
            '<span style="font-size:20px; font-weight:800; color:#006565; '
            'font-family:Inter;">⬡</span>'
        )
        logo.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(logo)

        # Title
        title_block = QWidget()
        vl = QVBoxLayout(title_block)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(0)
        t1 = QLabel("Jarvis")
        t1.setObjectName("app_title")
        t2 = QLabel("Analizador Léxico · Sintáctico · Semántico")
        t2.setObjectName("app_subtitle")
        vl.addWidget(t1)
        vl.addWidget(t2)
        layout.addWidget(title_block)

        layout.addStretch()

        # Buttons
        self._btn_analyze = QPushButton("▶  Analizar")
        self._btn_analyze.setObjectName("btn_analyze")
        self._btn_analyze.setFixedHeight(34)
        self._btn_analyze.clicked.connect(self._on_analyze)
        layout.addWidget(self._btn_analyze)

        btn_clear = QPushButton("Limpiar")
        btn_clear.setObjectName("btn_clear")
        btn_clear.setFixedHeight(34)
        btn_clear.clicked.connect(self._on_clear)
        layout.addWidget(btn_clear)

        btn_export = QPushButton("⬇  Exportar")
        btn_export.setObjectName("btn_export")
        btn_export.setFixedHeight(34)
        btn_export.setToolTip("Exportar tokens como CSV")
        btn_export.clicked.connect(self._on_export)
        layout.addWidget(btn_export)

        return bar

    def _build_right_panel(self) -> QWidget:
        container = QWidget()
        container.setObjectName("right_panel")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._tabs = QTabWidget()
        self._tabs.setObjectName("analysis_tabs")
        self._tabs.setDocumentMode(True)

        # Tab 1: Léxico
        self._token_table = TokenTableWidget()
        self._tabs.addTab(self._token_table, "Léxico")

        # Tab 2: Sintáctico
        self._syntax_view = QTextEdit()
        self._syntax_view.setReadOnly(True)
        self._syntax_view.setObjectName("code_editor")
        self._syntax_view.setFont(QFont("Fira Code", 12))
        self._syntax_view.setPlaceholderText("El árbol de derivación aparecerá aquí...")
        self._tabs.addTab(self._syntax_view, "Sintáctico")

        # Tab 3: Semántico
        self._tabs.addTab(self._build_semantic_tab(), "Semántico")

        layout.addWidget(self._tabs)
        return container

    def _build_semantic_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Symbol table
        sym_label = QLabel("TABLA DE SÍMBOLOS")
        sym_label.setObjectName("section_title")
        layout.addWidget(sym_label)

        self._symbol_table = QTableWidget()
        self._symbol_table.setObjectName("symbol_table")
        self._symbol_table.setColumnCount(4)
        self._symbol_table.setHorizontalHeaderLabels(["Nombre", "Tipo", "Línea decl.", "Usos"])
        self._symbol_table.horizontalHeader().setStretchLastSection(True)
        self._symbol_table.verticalHeader().setVisible(False)
        self._symbol_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._symbol_table.setShowGrid(False)
        self._symbol_table.setFont(QFont("Fira Code", 12))
        self._symbol_table.setFixedHeight(160)
        layout.addWidget(self._symbol_table)

        # Errors / warnings
        err_label = QLabel("ERRORES Y ADVERTENCIAS")
        err_label.setObjectName("section_title")
        layout.addWidget(err_label)

        self._error_view = QTextEdit()
        self._error_view.setObjectName("error_list")
        self._error_view.setReadOnly(True)
        self._error_view.setFont(QFont("Fira Code", 12))
        self._error_view.setPlaceholderText("Sin errores semánticos.")
        layout.addWidget(self._error_view)

        return container

    def _build_ast_panel(self) -> QWidget:
        container = QWidget()
        container.setObjectName("ast_panel")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header bar
        header = QWidget()
        header.setFixedHeight(32)
        header.setStyleSheet("background:#EEEEE8; border-top: 1px solid #DDDDD6;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(12, 0, 12, 0)
        hl.setSpacing(8)

        icon_lbl = QLabel("⬡  Árbol de Sintaxis Abstracta (AST)")
        icon_lbl.setObjectName("section_title")
        hl.addWidget(icon_lbl)
        hl.addStretch()

        # Zoom buttons
        for text, slot in [("−", self._ast_zoom_out), ("+", self._ast_zoom_in), ("⊙", self._ast_zoom_reset)]:
            btn = QPushButton(text)
            btn.setObjectName("ast_zoom_btn")
            btn.setFixedSize(28, 24)
            btn.clicked.connect(slot)
            hl.addWidget(btn)

        layout.addWidget(header)

        self._ast_graph = ASTGraphWidget()
        layout.addWidget(self._ast_graph)

        return container

    # ------------------------------------------------------------------
    # Analysis flow
    # ------------------------------------------------------------------

    def _on_analyze(self) -> None:
        source = self._editor.toPlainText().strip()
        if not source:
            self._status.showMessage("⚠  El editor está vacío.")
            return

        # Loading state
        self._btn_analyze.setText("⟳  Analizando...")
        self._btn_analyze.setEnabled(False)
        self._status.showMessage("Analizando...")

        self._worker = _AnalysisWorker(source)
        self._worker.finished.connect(self._on_analysis_done)
        self._worker.error.connect(self._on_analysis_error)
        self._worker.start()

    def _on_analysis_done(
        self, tokens: list, ast_root, sem_errors: list, sym_table
    ) -> None:
        # Reset button
        self._btn_analyze.setText("▶  Analizar")
        self._btn_analyze.setEnabled(True)

        # Count errors per phase
        lex_errors = sum(1 for t in tokens if t.get("attribute") == -1)
        sem_error_count = sum(1 for e in sem_errors if e.severity == Severity.ERROR)
        sem_warn_count = sum(1 for e in sem_errors if e.severity == Severity.WARNING)
        self._last_tokens = tokens

        # --- Tab: Léxico ---
        self._token_table.load_tokens(tokens)
        tab_text_lex = f"Léxico {'🔴' if lex_errors else ''}"
        self._tabs.setTabText(0, tab_text_lex.strip())

        # --- Tab: Sintáctico ---
        if ast_root is not None:
            self._syntax_view.setPlainText(self._ast_to_text(ast_root))
            self._tabs.setTabText(1, "Sintáctico")
        else:
            self._syntax_view.setPlainText("❌ Error de análisis sintáctico.")
            self._tabs.setTabText(1, "Sintáctico 🔴")

        # --- Tab: Semántico ---
        self._populate_symbol_table(sym_table)
        self._populate_errors(sem_errors)
        badge = ""
        if sem_error_count:
            badge = f" 🔴"
        elif sem_warn_count:
            badge = f" 🟡"
        self._tabs.setTabText(2, f"Semántico{badge}")

        # --- AST Graph ---
        self._ast_graph.render_ast(ast_root)

        # Status
        n = len(tokens)
        msg = f"✓ {n} tokens | {lex_errors} errores léxicos | {sem_error_count} errores semánticos | {sem_warn_count} advertencias"
        self._status.showMessage(msg)

    def _on_analysis_error(self, msg: str) -> None:
        self._btn_analyze.setText("▶  Analizar")
        self._btn_analyze.setEnabled(True)
        self._status.showMessage(f"❌ Error interno: {msg}")

    def _populate_symbol_table(self, sym_table) -> None:
        self._symbol_table.setRowCount(0)
        if sym_table is None:
            return
        symbols = sym_table.all_symbols()
        self._symbol_table.setRowCount(len(symbols))
        for row, sym in enumerate(symbols):
            for col, val in enumerate([
                sym.name, sym.type_, str(sym.line), str(len(sym.usages))
            ]):
                item = QTableWidgetItem(val)
                item.setFont(QFont("Fira Code", 12))
                self._symbol_table.setItem(row, col, item)
            self._symbol_table.setRowHeight(row, 28)

    def _populate_errors(self, errors: List[AnalysisError]) -> None:
        if not errors:
            self._error_view.setPlainText("")
            self._error_view.setPlaceholderText("✓ Sin errores semánticos.")
            return
        lines = []
        for e in errors:
            icon = "❌" if e.severity == Severity.ERROR else "⚠"
            lines.append(f"{icon} Línea {e.line}: {e.message}")
        self._error_view.setPlainText("\n".join(lines))

    def _ast_to_text(self, node: ASTNode, indent: int = 0) -> str:
        """Representación textual indentada del AST."""
        prefix = "  " * indent + ("└─ " if indent > 0 else "")
        result = prefix + node.label() + "\n"
        for child in node.children():
            if child is not None:
                result += self._ast_to_text(child, indent + 1)
        return result

    # ------------------------------------------------------------------
    # Clear
    # ------------------------------------------------------------------

    def _on_clear(self) -> None:
        self._editor.clear()
        self._token_table.clear_tokens()
        self._syntax_view.clear()
        self._error_view.clear()
        self._symbol_table.setRowCount(0)
        self._ast_graph.clear_graph()
        self._tabs.setTabText(0, "Léxico")
        self._tabs.setTabText(1, "Sintáctico")
        self._tabs.setTabText(2, "Semántico")
        self._status.showMessage("Listo.")

    # ------------------------------------------------------------------
    # Export CSV
    # ------------------------------------------------------------------

    def _on_export(self) -> None:
        if not self._last_tokens:
            self._status.showMessage("⚠  No hay tokens para exportar. Analiza primero.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar tokens", "tokens.csv", "CSV (*.csv)"
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["token", "attribute", "type", "line"])
                writer.writeheader()
                writer.writerows(self._last_tokens)
            self._status.showMessage(f"✓ Exportado en: {path}")
        except Exception as e:
            self._status.showMessage(f"❌ Error al exportar: {e}")

    # ------------------------------------------------------------------
    # AST zoom
    # ------------------------------------------------------------------

    def _ast_zoom_in(self) -> None:
        self._ast_graph.zoom_in()

    def _ast_zoom_out(self) -> None:
        self._ast_graph.zoom_out()

    def _ast_zoom_reset(self) -> None:
        self._ast_graph.zoom_reset()

    # ------------------------------------------------------------------
    # Status bar cursor position
    # ------------------------------------------------------------------

    def _update_cursor_pos(self) -> None:
        cursor = self._editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self._status.showMessage(f"Línea {line}, Columna {col}")
