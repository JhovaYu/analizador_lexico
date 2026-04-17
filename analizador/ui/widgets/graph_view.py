"""
ui/widgets/graph_view.py — AST Graph Viewer.
- Renderiza en Top-Down jerárquico.
- Permite animar los recorridos Pre, In y Postorden con QTimer.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, 
    QHBoxLayout, QComboBox, QPushButton
)
from PyQt6.QtCore import Qt, QTimer, QRectF, pyqtSignal
from PyQt6.QtGui import QColor, QPen, QBrush, QFont, QPainter

class _NodeItem:
    """Clase local pequeña para guardar coordenadas y datos graficos de un nodo."""
    def __init__(self, node_obj, x: float, y: float, depth: int, is_terminal: bool):
        self.node_obj = node_obj
        self.x = x
        self.y = y
        self.depth = depth
        self.is_terminal = is_terminal
        self.label = str(getattr(node_obj, "value", getattr(node_obj, "rule_name", "Node")))
        # Default styling
        self.bg_color = QColor("#E8E8E2") if not is_terminal else QColor("#DDDDD6")
        self.border_color = QColor("#8A8A8A")
        self.text_color = QColor("#1A1A1A")

        self.W = 80
        self.H = 30

class ASTGraphWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        
        # Guardar estado para animación
        self._items = {} # id(node) -> _NodeItem
        self._edges = []
        self._animation_steps = []
        self._current_anim_idx = 0
        self._timer = QTimer()
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._anim_step)
        
        # Diccionarios de recorridos generados por core/traversals
        self._traversals = {"Preorden": [], "Inorden": [], "Postorden": []}
        
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        self.toolbar = QWidget()
        self.toolbar.setObjectName("ast_toolbar")
        t_layout = QHBoxLayout(self.toolbar)
        t_layout.setContentsMargins(10, 5, 10, 5)
        
        self.cb_traversal = QComboBox()
        self.cb_traversal.addItems(["Preorden", "Inorden", "Postorden"])
        t_layout.addWidget(self.cb_traversal)
        
        self.btn_play = QPushButton("▶ Reproducir")
        self.btn_play.setObjectName("btn_analyze")
        self.btn_play.clicked.connect(self._start_animation)
        t_layout.addWidget(self.btn_play)
        t_layout.addStretch()
        
        layout.addWidget(self.toolbar)
        
        # View
        self.view.setObjectName("ast_graph_view")
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        layout.addWidget(self.view)
        
        self.setLayout(layout)

    def draw_tree(self, root_node, pre, inorder, post) -> None:
        self._timer.stop()
        self.scene.clear()
        self._items.clear()
        self._edges.clear()
        
        if not root_node:
            return
            
        self._traversals["Preorden"] = pre
        self._traversals["Inorden"] = inorder
        self._traversals["Postorden"] = post
        
        # LAYOUT: Jerárquico recursivo Top-Down Custom
        # 1. Asignamos anchura y posX a toda la capa inferior.
        X_SEP = 100
        Y_SEP = 80
        
        # Computar X recursivamente:
        # El X de un nodo interno es el promedio de los X de sus hijos.
        # Si es una hoja, es el max_x_actual + X_SEP
        max_x = [0]
        
        def calculate_positions(node, depth):
            children = node.get_children()
            child_coords = []
            
            for c in children:
                cx, cy = calculate_positions(c, depth + 1)
                child_coords.append((id(c), cx, cy))
                
            if not children:
                # Es hoja
                my_x = max_x[0]
                max_x[0] += X_SEP
            else:
                # Es interno
                my_x = sum(cx for _, cx, _ in child_coords) / len(children)
                
            my_y = depth * Y_SEP
            self._items[id(node)] = _NodeItem(node, my_x, my_y, depth, not bool(children))
            
            # Guardar edges de este padre a sus hijos
            for cid, cx, cy in child_coords:
                self._edges.append((my_x, my_y, cx, cy))
                
            return my_x, my_y

        calculate_positions(root_node, 0)
        self._render_scene()

    def _render_scene(self) -> None:
        self.scene.clear()
        
        pen_line = QPen(QColor("#DDDDD6"))
        pen_line.setWidth(2)
        
        # Draw edges
        for x1, y1, x2, y2 in self._edges:
            # Los y son el centro de las cajas. Para quedar mejor:
            # y1 + H para el top, y2 para el bottom
            # simplificado conectando centro a centro
            self.scene.addLine(x1, y1, x2, y2, pen_line)
            
        # Draw nodes
        font = QFont("Inter", 10, QFont.Weight.Bold)
        for _, itm in self._items.items():
            # Background
            rect = self.scene.addRect(
                itm.x - itm.W/2, itm.y - itm.H/2, 
                itm.W, itm.H,
                QPen(itm.border_color), QBrush(itm.bg_color)
            )
            # Text
            text = self.scene.addText(itm.label, font)
            text.setDefaultTextColor(itm.text_color)
            br = text.boundingRect()
            text.setPos(itm.x - br.width()/2, itm.y - br.height()/2)

    def _start_animation(self) -> None:
        sel = self.cb_traversal.currentText()
        self._animation_steps = self._traversals.get(sel, [])
        if not self._animation_steps: return
        
        self.btn_play.setEnabled(False)
        self._current_anim_idx = 0
        # Reset defaults
        for itm in self._items.values():
            itm.bg_color = QColor("#E8E8E2") if not itm.is_terminal else QColor("#DDDDD6")
            itm.border_color = QColor("#8A8A8A")
            itm.text_color = QColor("#1A1A1A")
            
        self._render_scene()
        self._timer.start()

    def _anim_step(self) -> None:
        if self._current_anim_idx > 0:
            # Restaurar el anterior a un gris pasivo sutil
            prev_node = self._animation_steps[self._current_anim_idx - 1]
            itm = self._items.get(id(prev_node))
            if itm:
                itm.bg_color = QColor("#F5F5F0")
                itm.border_color = QColor("#DDDDD6")
                
        if self._current_anim_idx >= len(self._animation_steps):
            self._timer.stop()
            self.btn_play.setEnabled(True)
            self._render_scene()
            return
            
        # Iluminar activo #00A0A0
        curr_node = self._animation_steps[self._current_anim_idx]
        curr_itm = self._items.get(id(curr_node))
        if curr_itm:
            curr_itm.bg_color = QColor("#00A0A0")
            curr_itm.border_color = QColor("#006565")
            curr_itm.text_color = QColor("#FFFFFF")
            # Hacer scroll hacia el nodo
            self.view.centerOn(curr_itm.x, curr_itm.y)
            
        self._render_scene()
        self._current_anim_idx += 1
