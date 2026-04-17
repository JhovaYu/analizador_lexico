"""
ui/main_window.py — Orquestador Principal.
Responsabilidad:
- Integrar CodeEditor, Tabs y GraphView en el layout general.
- Ejecutar el flujo de compilación (Paso a Paso o Analizar Todo en Vivo).
"""
import sys
import csv
from typing import Optional, List

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QLabel, QPushButton,
    QStatusBar, QApplication, QRadioButton, QButtonGroup,
    QFileDialog
)
from PyQt6.QtCore import Qt

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
        
        self.pipe_state = 0
        self._current_tokens = []
        self._current_ast = None
        self._sem_errors = []
        
        self._build_ui()
        
        # Conectar eventos en vivo
        self._editor.textChanged.connect(self._on_text_changed)

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        
        layout.addWidget(self._build_topbar())
        
        self._editor = CodeEditorWidget()
        self._tabs = QTabWidget()
        self._tabs.tabBar().setExpanding(True)
        
        self._lex_tab = LexicalTab()
        self._syn_tab = SyntacticTab()
        self._sem_tab = SemanticTab()
        
        self._syn_tab.graph_view.request_maximize.connect(self._on_graph_maximize)
        
        self._tabs.addTab(self._lex_tab, "1. Léxico")
        self._tabs.addTab(self._syn_tab, "2. Sintáctico")
        self._tabs.addTab(self._sem_tab, "3. Semántico")
        
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
        
        # Modo de Ejecución
        mode_layout = QHBoxLayout()
        mode_layout.setContentsMargins(20, 0, 20, 0)
        self.rb_live = QRadioButton("Modo en Vivo")
        self.rb_live.setChecked(True)
        self.rb_step = QRadioButton("Paso a Paso")
        
        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.rb_live)
        self.mode_group.addButton(self.rb_step)
        
        mode_layout.addWidget(self.rb_live)
        mode_layout.addWidget(self.rb_step)
        hl.addLayout(mode_layout)
        
        hl.addStretch()
        
        self.btn_step = QPushButton("Próximo Paso")
        self.btn_step.setObjectName("btn_step")
        self.btn_step.clicked.connect(self._on_step)
        hl.addWidget(self.btn_step)
        
        self.btn_all = QPushButton("▶ Analizar Todo")
        self.btn_all.setObjectName("btn_analyze")
        self.btn_all.clicked.connect(self._on_analyze_all)
        hl.addWidget(self.btn_all)
        
        btn_clear = QPushButton("Limpiar")
        btn_clear.setObjectName("btn_clear")
        btn_clear.clicked.connect(self._on_clear)
        hl.addWidget(btn_clear)
        
        btn_export = QPushButton("⬇ Exportar CSV")
        btn_export.setObjectName("btn_export")
        btn_export.clicked.connect(self._on_export)
        hl.addWidget(btn_export)
        
        return bar

    # ----------------------------------------------------------------------
    # Eventos y Máquina de Estados
    # ----------------------------------------------------------------------
    def _on_text_changed(self):
        if self.rb_live.isChecked():
            # Si escribimos lento en tiempo real, ejecutamos TODO automáticametne.
            self._on_analyze_all()
        else:
            # En paso a paso, al editar se pierde la garantía, reiniciamos.
            if self.pipe_state != 0:
                self._reset_state()
                self._status.showMessage("⚠ Código modificado. Estado reseteado a Inicio.")

    def _on_clear(self):
        self._editor.blockSignals(True)
        self._editor.clear()
        self._editor.blockSignals(False)
        self._reset_state()
        self._lex_tab.populate([])
        # Resetear grafo enviando nada
        self._syn_tab.set_tree(None, [], [], [])
        self._sem_tab.populate([], [])
        self._status.showMessage("Editor y estados limpiados.")

    def _on_export(self):
        if not self._current_tokens:
            self._status.showMessage("⚠ No hay tokens para exportar.")
            return
        
        path, _ = QFileDialog.getSaveFileName(self, "Exportar tokens", "tokens.csv", "CSV (*.csv)")
        if not path:
            return
            
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self._current_tokens[0].keys())
                writer.writeheader()
                writer.writerows(self._current_tokens)
            self._status.showMessage(f"✓ Exportado exitosamente en: {path}")
        except Exception as e:
            self._status.showMessage(f"❌ Error guardando: {e}")

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
            self._reset_state()
            self._status.showMessage("⚠ Editor vacío.")
            return

        self._reset_state()
        self._do_lexical(source)
        if self._do_syntactic(source):
            self._do_semantic()
            
        # Update metrics status final en ambos casos de éxito completo
        self._update_status_metrics()

    def _on_graph_maximize(self, maximized: bool):
        self._editor.setVisible(not maximized)
        if maximized:
            self.btn_all.setVisible(False)
            self.btn_step.setVisible(False)
            self.rb_live.setVisible(False)
            self.rb_step.setVisible(False)
        else:
            self.btn_all.setVisible(True)
            self.btn_step.setVisible(True)
            self.rb_live.setVisible(True)
            self.rb_step.setVisible(True)

    def _reset_state(self):
        self.pipe_state = 0
        self.btn_step.setText("Paso a Paso")
        self._editor.highlight_errors([])
        self._current_ast = None
        self._current_tokens = []
        self._sem_errors = []
        
    def _update_status_metrics(self):
        tok_count = len(self._current_tokens)
        err_count = len([e for e in self._sem_errors if getattr(e, 'severity', 1) == 1])
        # Buscamos tokens lexicos malos (attribute = -1)
        lex_errs = sum(1 for t in self._current_tokens if t.get("attribute") == -1)
        
        self._status.showMessage(f"✓ Análisis finalizado: {tok_count} Tokens | {lex_errs} Err. Léxicos | {err_count} Err. Semánticos")

    # ----------------------------------------------------------------------
    # PIPELINE ACTIONS
    # ----------------------------------------------------------------------
    def _do_lexical(self, source: str):
        lexer = DFALexer()
        tokens = lexer.tokenize(source)
        
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
        
        if not self.rb_live.isChecked():
            # Evita spoilers de las fases futuras limpiándolas
            self._syn_tab.set_tree(None, [], [], [])
            self._sem_tab.populate([], [])
            self._editor.highlight_errors([])
            
            self._tabs.setCurrentIndex(0)
            self._status.showMessage("Fase 1: Análisis Léxico Completado.")

    def _do_syntactic(self, source: str) -> bool:
        try:
            self._current_ast = parse(source)
            pre = get_preorder(self._current_ast)
            ino = get_inorder(self._current_ast)
            post = get_postorder(self._current_ast)
            
            self._syn_tab.set_tree(self._current_ast, pre, ino, post)
            
            if not self.rb_live.isChecked():
                self._sem_tab.populate([], [])
                self._editor.highlight_errors([])
                self._tabs.setCurrentIndex(1)
                self._status.showMessage("Fase 2: Análisis Sintáctico Completado.")
            return True
        except Exception as e:
            self._status.showMessage(f"❌ Error de Sintaxis: {e}")
            if not self.rb_live.isChecked():
                self._tabs.setCurrentIndex(1)
            return False

    def _do_semantic(self):
        if not self._current_ast:
            return
            
        analyzer = SemanticAnalyzer()
        self._sem_errors = analyzer.analyze(self._current_ast)
        
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
        
        if not self.rb_live.isChecked():
            self._tabs.setCurrentIndex(2)
            self._update_status_metrics()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    with open("ui/style.qss", "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
