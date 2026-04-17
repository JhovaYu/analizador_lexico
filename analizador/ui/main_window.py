"""
ui/main_window.py — Orquestador Principal.
Responsabilidad:
- Integrar CodeEditor, Tabs y GraphView en el layout general.
- Ejecutar el flujo de compilación (Paso a Paso o Analizar Todo).
"""
import sys
from typing import Optional, List

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QLabel, QPushButton,
    QStatusBar, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# Componentes atómicos
from ui.widgets.code_editor import CodeEditorWidget
from ui.widgets.graph_view import ASTGraphWidget
from ui.tabs.lexical_tab import LexicalTab
from ui.tabs.syntactic_tab import SyntacticTab
from ui.tabs.semantic_tab import SemanticTab

# Core
from core.lexer import DFALexer
from core.parser import parse
from core.semantic import SemanticAnalyzer
from core.traversals import get_preorder, get_inorder, get_postorder

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Jarvis — Analizador de Arquitectura Atómica")
        self.resize(1200, 800)
        self.setMinimumSize(900, 600)
        
        # 0: Inicio, 1: Léxico listo, 2: Sintáctico listo, 3: Semántico listo
        self.pipe_state = 0
        
        # Guardado de state temporal
        self._current_tokens = []
        self._current_ast = None
        self._sem_errors = []
        
        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        
        layout.addWidget(self._build_topbar())
        
        self._editor = CodeEditorWidget()
        self._tabs = QTabWidget()
        
        self._lex_tab = LexicalTab()
        self._syn_tab = SyntacticTab()
        self._sem_tab = SemanticTab()
        
        self._tabs.addTab(self._lex_tab, "1. Léxico")
        self._tabs.addTab(self._syn_tab, "2. Sintáctico")
        self._tabs.addTab(self._sem_tab, "3. Semántico")
        
        # Splitter Editor | Tabs
        self._h_split = QSplitter(Qt.Orientation.Horizontal)
        self._h_split.addWidget(self._editor)
        self._h_split.addWidget(self._tabs)
        self._h_split.setSizes([600, 600])
        
        layout.addWidget(self._h_split)
        
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Listo para análisis.")

    def _build_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("topbar")
        hl = QHBoxLayout(bar)
        hl.setContentsMargins(15, 0, 15, 0)
        
        lbl = QLabel("Jarvis ⬡")
        lbl.setObjectName("app_title")
        hl.addWidget(lbl)
        hl.addStretch()
        
        self.btn_step = QPushButton("Paso a Paso")
        self.btn_step.setObjectName("btn_step")
        self.btn_step.clicked.connect(self._on_step)
        hl.addWidget(self.btn_step)
        
        self.btn_all = QPushButton("▶ Analizar Todo")
        self.btn_all.setObjectName("btn_analyze")
        self.btn_all.clicked.connect(self._on_analyze_all)
        hl.addWidget(self.btn_all)
        return bar

    # ----------------------------------------------------------------------
    # STATE MACHINE (Paso a Paso)
    # ----------------------------------------------------------------------
    def _on_step(self):
        source = self._editor.toPlainText().strip()
        if not source:
            self._status.showMessage("⚠ Editor vacío.")
            return
            
        if self.pipe_state == 0:
            self._do_lexical(source)
            self.pipe_state = 1
            self.btn_step.setText("Paso 2: Sintáctico")
            
        elif self.pipe_state == 1:
            success = self._do_syntactic(source)
            if success:
                self.pipe_state = 2
                self.btn_step.setText("Paso 3: Semántico")
            else:
                self._reset_state()
                
        elif self.pipe_state == 2:
            self._do_semantic()
            self.pipe_state = 3
            self.btn_step.setText("↻ Reiniciar Paso a Paso")
            
        else:
            self._reset_state()

    def _on_analyze_all(self):
        source = self._editor.toPlainText().strip()
        if not source:
            self._status.showMessage("⚠ Editor vacío.")
            return

        self._reset_state()
        self._do_lexical(source)
        if self._do_syntactic(source):
            self._do_semantic()

    def _reset_state(self):
        self.pipe_state = 0
        self.btn_step.setText("Paso a Paso")
        self._editor.highlight_errors([])
        self._current_ast = None
        self._current_tokens = []
        self._sem_errors = []
        self._status.showMessage("Estado reiniciado.")

    # ----------------------------------------------------------------------
    # PIPELINE ACTIONS
    # ----------------------------------------------------------------------
    def _do_lexical(self, source: str):
        lexer = DFALexer()
        tokens = lexer.tokenize(source)
        
        # Mapear al dumb component dict struct
        formatted = []
        for t in tokens:
            formatted.append({
                "line": t.get("line", ""),
                "col": t.get("col", ""),
                "type": "Error" if t.get("attribute") == -1 else t.get("type", "Token"),
                "value": t.get("token", ""),
                "error": t.get("attribute") == -1
            })
        
        self._current_tokens = tokens
        self._lex_tab.populate(formatted)
        self._tabs.setCurrentIndex(0)
        self._status.showMessage("Fase 1: Análisis Léxico Completado.")

    def _do_syntactic(self, source: str) -> bool:
        try:
            self._current_ast = parse(source)
            pre = get_preorder(self._current_ast)
            ino = get_inorder(self._current_ast)
            post = get_postorder(self._current_ast)
            
            self._syn_tab.set_tree(self._current_ast, pre, ino, post)
            self._tabs.setCurrentIndex(1)
            self._status.showMessage("Fase 2: Análisis Sintáctico Completado.")
            return True
        except Exception as e:
            self._status.showMessage(f"❌ Error de Sintaxis: {e}")
            self._tabs.setCurrentIndex(1)
            return False

    def _do_semantic(self):
        if not self._current_ast:
            return
            
        analyzer = SemanticAnalyzer()
        self._sem_errors = analyzer.analyze(self._current_ast)
        
        # Preparar data
        symbols_formatted = []
        for sym in analyzer.symbol_table.all_symbols():
            symbols_formatted.append({
                "name": sym.name,
                "type_": sym.type_,
                "line": sym.line,
                "is_used": len(sym.usages) > 0
            })
            
        self._sem_tab.populate(symbols_formatted, self._sem_errors)
        self._editor.highlight_errors(self._sem_errors)
        self._tabs.setCurrentIndex(2)
        
        err_msg = f"{len([e for e in self._sem_errors if getattr(e, 'severity', 1) == 1])} errores"
        self._status.showMessage(f"Fase 3: Semántica Completada ({err_msg}).")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    with open("ui/style.qss", "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
