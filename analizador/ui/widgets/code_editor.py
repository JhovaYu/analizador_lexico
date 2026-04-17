"""
ui/widgets/code_editor.py — Componente atomizado del Editor de Código.
Responsabilidades:
- Renderizado del código con Syntax Highlighting.
- Gutter con números de línea.
- Resaltado visual de errores semánticos/léxicos/sintácticos (ExtraSelection).
"""
from __future__ import annotations
import re
from typing import List, Any
from PyQt6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit
from PyQt6.QtCore import Qt, QRect, QSize
from PyQt6.QtGui import (
    QColor, QTextCharFormat, QFont, QSyntaxHighlighter,
    QTextDocument, QPainter, QFontMetrics, QTextCursor,
)

# Se asume que AnalysisError viene del core, lo tipamos levemente aquí
# para mantener desacoplamiento estricto
class PythonHighlighter(QSyntaxHighlighter):
    """Resaltado de sintaxis (Paleta Paper & Ink / Deep Teal)."""

    def __init__(self, document: QTextDocument) -> None:
        super().__init__(document)
        self._rules: list = []
        self._build_rules()

    def _fmt(self, color: str, bold: bool = False, italic: bool = False) -> QTextCharFormat:
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Weight.Bold)
        if italic:
            fmt.setFontItalic(True)
        return fmt

    def _build_rules(self) -> None:
        # Keywords — Deep Teal bold
        kw_fmt = self._fmt("#006565", bold=True)
        keywords = [
            "def", "if", "elif", "else", "while", "for", "in",
            "return", "print", "and", "or", "not", "True", "False",
            "class", "import", "from", "lambda", "pass", "break",
            "continue", "None", "range",
        ]
        for kw in keywords:
            self._rules.append((re.compile(rf"\b{kw}\b"), kw_fmt))

        # Strings — Marrón terroso (#8B4823)
        str_fmt = self._fmt("#8B4823")
        self._rules.append((re.compile(r'"""[\s\S]*?"""'), str_fmt))
        self._rules.append((re.compile(r"'''[\s\S]*?'''"), str_fmt))
        self._rules.append((re.compile(r'"[^"\n]*"'), str_fmt))
        self._rules.append((re.compile(r"'[^'\n]*'"), str_fmt))

        # Numbers — Azul sobrio (#1E6BB8)
        num_fmt = self._fmt("#1E6BB8")
        self._rules.append((re.compile(r"\b\d+\.?\d*([eE][+-]?\d+)?\b"), num_fmt))

        # Operators — Rojo acento (#C0392B)
        op_fmt = self._fmt("#C0392B")
        self._rules.append((re.compile(r"[+\-*/%=<>!&|^~]+"), op_fmt))

        # Comments — Gris (#8A8A8A) italic
        comment_fmt = self._fmt("#8A8A8A", italic=True)
        self._rules.append((re.compile(r"#[^\n]*"), comment_fmt))

    def highlightBlock(self, text: str) -> None:
        for pattern, fmt in self._rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)


class _LineNumberArea(QWidget):
    """Gutter lateral para mostrar las líneas numeradas."""
    def __init__(self, editor: "CodeEditorWidget") -> None:
        super().__init__(editor)
        self._editor = editor
        self.setObjectName("line_number_area")

    def sizeHint(self) -> QSize:
        return QSize(self._editor._line_number_area_width(), 0)

    def paintEvent(self, event) -> None:
        self._editor._paint_line_numbers(event)


class CodeEditorWidget(QPlainTextEdit):
    """Editor Atomizado con Highlight de Errores integrados."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("code_editor")
        self._error_selections: List[QTextEdit.ExtraSelection] = []

        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        # Font setup (Fira Code preferido)
        font = QFont("Fira Code")
        if not font.exactMatch():
            font = QFont("Cascadia Code")
            if not font.exactMatch():
                font = QFont("Consolas")
        font.setPointSize(13)
        self.setFont(font)
        self.setTabStopDistance(QFontMetrics(font).horizontalAdvance(" ") * 4)

        # Line number area
        self._line_number_area = _LineNumberArea(self)
        self._update_line_number_area_width(0)

        # Syntax highlighting
        self._highlighter = PythonHighlighter(self.document())

        self.setPlaceholderText("# Escribe tu código apoyado por el Árbol de Derivación...")

    def _connect_signals(self) -> None:
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_lines)

    # ------------------------------------------------------------------
    # Error Highlighting
    # ------------------------------------------------------------------
    def highlight_errors(self, errors: List[Any]) -> None:
        """
        Recibe una lista de errores y resalta el fondo de sus líneas correspondientes.
        errors: Lista de objetos (e.g. AnalysisError) que posean atributo `line`.
        """
        self._error_selections.clear()
        doc = self.document()

        for err in errors:
            line_idx = getattr(err, "line", 1) - 1
            if 0 <= line_idx < doc.blockCount():
                block = doc.findBlockByNumber(line_idx)
                
                selection = QTextEdit.ExtraSelection()
                # Rojo muy tenue especificado en la directriz de diseño (#FDECEA)
                selection.format.setBackground(QColor("#FDECEA"))
                selection.format.setProperty(QTextCharFormat.Property.FullWidthSelection, True)
                
                # Opcional: Subrayar ondulado (squiggly) rojo si se necesita más énfasis
                selection.format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SpellCheckUnderline)
                selection.format.setUnderlineColor(QColor("#C0392B"))
                
                cursor = QTextCursor(block)
                selection.cursor = cursor
                selection.cursor.clearSelection()
                
                self._error_selections.append(selection)

        self._highlight_lines()

    # ------------------------------------------------------------------
    # Rendering Internals
    # ------------------------------------------------------------------
    def _highlight_lines(self) -> None:
        """Combina los errores persistentes con la línea actual enfocada."""
        extra = list(self._error_selections)
        
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            # Selection focus Teal (#006565) transparente
            color = QColor(0, 101, 101, 15)
            selection.format.setBackground(color)
            selection.format.setProperty(QTextCharFormat.Property.FullWidthSelection, True)
            
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra.append(selection)
            
        self.setExtraSelections(extra)

    # ------------------------------------------------------------------
    # Line number gutter
    # ------------------------------------------------------------------
    def _line_number_area_width(self) -> int:
        digits = max(len(str(self.blockCount())), 3)
        return 12 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_line_number_area_width(self, _: int) -> None:
        self.setViewportMargins(self._line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect: QRect, dy: int) -> None:
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(0, rect.y(), self._line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self._line_number_area_width(), cr.height())
        )

    def _paint_line_numbers(self, event) -> None:
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), QColor("#E8E8E2"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        
        font = QFont(self.font())
        font.setPointSize(11)
        painter.setFont(font)

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#8A8A8A"))
                painter.drawText(
                    0, top,
                    self._line_number_area.width() - 6,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight, number,
                )
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1
