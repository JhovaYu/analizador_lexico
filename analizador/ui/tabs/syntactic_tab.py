"""
ui/tabs/syntactic_tab.py — Tab Sintáctico. Dumb Component contenedor del GraphView.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from ui.widgets.graph_view import ASTGraphWidget

class SyntacticTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # El grafo maneja sus propios estados visuales y barras de herramientas
        self.graph_view = ASTGraphWidget()
        layout.addWidget(self.graph_view)
        
        self.setLayout(layout)

    def set_tree(self, root_node, pre_order, in_order, post_order) -> None:
        """Pasa la data estructurada al widget gráfico interno."""
        self.graph_view.draw_tree(root_node, pre_order, in_order, post_order)
