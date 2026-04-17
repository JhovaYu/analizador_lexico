"""
ast_graph.py — ASTGraphWidget: QGraphicsView interactivo para visualizar el AST.

Características:
- Nodos con colores por tipo (Statement, Expresión, Literal)
- Aristas con curvas Bezier
- Zoom: Ctrl+scroll y botones [+][-][Reset]
- Pan: click + arrastrar
- Selección de nodo con highlight
- Hover: escala 1.05x
- Doble click: colapsar/expandir hijos
"""
from __future__ import annotations
from typing import Optional, List, Dict, Tuple

from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsEllipseItem,
    QGraphicsPathItem, QGraphicsTextItem, QGraphicsItem,
    QWidget, QHBoxLayout, QPushButton, QVBoxLayout,
)
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import (
    QColor, QPen, QBrush, QPainterPath, QFont, QWheelEvent, QMouseEvent,
    QTransform,
)

from core.ast_nodes import (
    ASTNode, Program, FunctionDef, AssignStatement, IfStatement,
    WhileStatement, ForStatement, ReturnStatement, PrintStatement,
    BinaryOp, UnaryOp, FunctionCall,
    Identifier, IntLiteral, FloatLiteral, StringLiteral, BoolLiteral,
    ExprStatement, ElifClause, ElseClause,
)

# ---------------------------------------------------------------------------
# Color scheme por categoría de nodo
# ---------------------------------------------------------------------------

STATEMENT_NODES = (
    Program, FunctionDef, AssignStatement, IfStatement, ElifClause, ElseClause,
    WhileStatement, ForStatement, ReturnStatement, PrintStatement, ExprStatement,
)
EXPRESSION_NODES = (BinaryOp, UnaryOp, FunctionCall)
LITERAL_NODES = (Identifier, IntLiteral, FloatLiteral, StringLiteral, BoolLiteral)


def _node_colors(node: ASTNode) -> Tuple[str, str, str]:
    """Retorna (fondo, borde, texto) según el tipo de nodo."""
    if isinstance(node, STATEMENT_NODES):
        return "#006565", "#004F4F", "#FFFFFF"
    if isinstance(node, EXPRESSION_NODES):
        return "#E0F2F2", "#006565", "#1A1A1A"
    if isinstance(node, LITERAL_NODES):
        return "#EEEEE8", "#AAAAAA", "#1A1A1A"
    return "#EEEEE8", "#8A8A8A", "#1A1A1A"


# ---------------------------------------------------------------------------
# Graphics items
# ---------------------------------------------------------------------------

NODE_W = 110
NODE_H = 40
H_GAP = 30   # horizontal gap between siblings
V_GAP = 60   # vertical gap between levels


class NodeItem(QGraphicsEllipseItem):
    """Nodo circular del grafo AST."""

    def __init__(self, node: ASTNode, scene: "ASTScene") -> None:
        super().__init__(-NODE_W / 2, -NODE_H / 2, NODE_W, NODE_H)
        self._ast_node = node
        self._scene = scene
        self._collapsed = False
        self._children_items: List["NodeItem"] = []
        self._edge_items: List[QGraphicsPathItem] = []

        bg, border, text_color = _node_colors(node)
        self.setBrush(QBrush(QColor(bg)))
        self._default_pen = QPen(QColor(border), 1.5)
        self._hover_pen = QPen(QColor("#00A0A0"), 2.5)
        self._select_pen = QPen(QColor("#00A0A0"), 3)
        self.setPen(self._default_pen)

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)

        # Label text
        self._label = QGraphicsTextItem(node.label(), self)
        font = QFont("Inter", 9, QFont.Weight.Medium)
        self._label.setFont(font)
        self._label.setDefaultTextColor(QColor(text_color))
        lw = self._label.boundingRect().width()
        lh = self._label.boundingRect().height()
        self._label.setPos(-lw / 2, -lh / 2)

    def hoverEnterEvent(self, event) -> None:
        self.setScale(1.05)
        self.setPen(self._hover_pen)
        self.setZValue(10)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        self.setScale(1.0)
        self.setPen(self._select_pen if self.isSelected() else self._default_pen)
        self.setZValue(1)
        super().hoverLeaveEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        self._collapsed = not self._collapsed
        for child in self._children_items:
            child.setVisible(not self._collapsed)
        for edge in self._edge_items:
            edge.setVisible(not self._collapsed)
        super().mouseDoubleClickEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            self.setPen(self._select_pen if value else self._default_pen)
        return super().itemChange(change, value)


# ---------------------------------------------------------------------------
# Layout engine — Reingold-Tilford (simplified recursive)
# ---------------------------------------------------------------------------

class _LayoutEngine:
    """Calcula posiciones (x, y) para cada nodo en un árbol jerárquico."""

    def __init__(self) -> None:
        self._x_counters: Dict[int, float] = {}

    def layout(self, node: ASTNode, depth: int = 0) -> Dict[int, Tuple[float, float]]:
        positions: Dict[int, Tuple[float, float]] = {}
        self._assign_positions(node, depth, positions)
        return positions

    def _assign_positions(
        self,
        node: ASTNode,
        depth: int,
        positions: Dict[int, Tuple[float, float]],
    ) -> float:
        """Asignar posición usando counter por nivel. Retorna x central del subárbol."""
        children = node.children()
        if not children:
            x = self._x_counters.get(depth, 0.0)
            self._x_counters[depth] = x + NODE_W + H_GAP
            positions[id(node)] = (x, depth * (NODE_H + V_GAP))
            return x

        child_xs: List[float] = []
        for child in children:
            cx = self._assign_positions(child, depth + 1, positions)
            child_xs.append(cx)

        x = (child_xs[0] + child_xs[-1]) / 2.0
        positions[id(node)] = (x, depth * (NODE_H + V_GAP))
        return x


# ---------------------------------------------------------------------------
# Scene
# ---------------------------------------------------------------------------

class ASTScene(QGraphicsScene):
    def __init__(self) -> None:
        super().__init__()
        self.setBackgroundBrush(QBrush(QColor("#F5F5F0")))

    def build(self, root: ASTNode) -> None:
        self.clear()
        engine = _LayoutEngine()
        positions = engine.layout(root)
        node_items: Dict[int, NodeItem] = {}
        # First pass: create node items
        self._create_items(root, positions, node_items)
        # Second pass: draw edges
        self._draw_edges(root, node_items)

    def _create_items(
        self,
        node: ASTNode,
        positions: Dict[int, Tuple[float, float]],
        node_items: Dict[int, NodeItem],
    ) -> None:
        pos = positions.get(id(node))
        if pos is None:
            return
        item = NodeItem(node, self)
        item.setPos(QPointF(pos[0], pos[1]))
        item.setZValue(1)
        self.addItem(item)
        node_items[id(node)] = item

        for child in node.children():
            self._create_items(child, positions, node_items)

    def _draw_edges(
        self, node: ASTNode, node_items: Dict[int, NodeItem]
    ) -> None:
        parent_item = node_items.get(id(node))
        if parent_item is None:
            return

        for child in node.children():
            child_item = node_items.get(id(child))
            if child_item is None:
                continue

            # Bezier edge
            p1 = parent_item.pos()
            p2 = child_item.pos()

            path = QPainterPath(p1)
            ctrl1 = QPointF(p1.x(), (p1.y() + p2.y()) / 2)
            ctrl2 = QPointF(p2.x(), (p1.y() + p2.y()) / 2)
            path.cubicTo(ctrl1, ctrl2, p2)

            edge = QGraphicsPathItem(path)
            edge.setPen(QPen(QColor("#AAAAAA"), 1.2, Qt.PenStyle.SolidLine))
            edge.setZValue(0)
            self.addItem(edge)

            parent_item._edge_items.append(edge)
            parent_item._children_items.append(child_item)

            self._draw_edges(child, node_items)


# ---------------------------------------------------------------------------
# View
# ---------------------------------------------------------------------------

class ASTGraphWidget(QGraphicsView):
    """QGraphicsView interactivo para el grafo AST."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("ast_graph_view")
        self._scene = ASTScene()
        self.setScene(self._scene)

        self.setRenderHint(self.renderHints() | self.renderHints().Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self._scale_factor = 1.0

        # Mostrar mensaje vacío
        self._show_empty()

    def _show_empty(self) -> None:
        self._scene.clear()
        msg = QGraphicsTextItem("El grafo AST aparecerá aquí después del análisis.")
        msg.setDefaultTextColor(QColor("#8A8A8A"))
        msg.setFont(QFont("Inter", 11))
        self._scene.addItem(msg)

    def render_ast(self, root: Optional[ASTNode]) -> None:
        """Construir y mostrar el grafo del AST."""
        if root is None:
            self._show_empty()
            return
        self._scene.build(root)
        self.fitInView(self._scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def clear_graph(self) -> None:
        self._show_empty()

    # ------------------------------------------------------------------
    # Zoom
    # ------------------------------------------------------------------

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 0.87
            self._zoom(factor)
        else:
            super().wheelEvent(event)

    def zoom_in(self) -> None:
        self._zoom(1.2)

    def zoom_out(self) -> None:
        self._zoom(1 / 1.2)

    def zoom_reset(self) -> None:
        self.resetTransform()
        self._scale_factor = 1.0
        if self._scene.items():
            self.fitInView(
                self._scene.itemsBoundingRect(),
                Qt.AspectRatioMode.KeepAspectRatio,
            )

    def _zoom(self, factor: float) -> None:
        self._scale_factor *= factor
        self._scale_factor = max(0.1, min(self._scale_factor, 5.0))
        self.scale(factor, factor)
