"""
editor_panel.py — CodeEditorWidget con números de línea y syntax highlighting.
"""
from __future__ import annotations
import re
from PyQt6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit
from PyQt6.QtCore import Qt, QRect, QSize
from PyQt6.QtGui import (
    QColor, QTextCharFormat, QFont, QSyntaxHighlighter,
    QTextDocument, QPainter, QFontMetrics, QTextCursor,
)


# ---------------------------------------------------------------------------
# Syntax Highlighter
# ---------------------------------------------------------------------------

class PythonHighlighter(QSyntaxHighlighter):
    """Resaltado de sintaxis para el subconjunto de Python soportado."""

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

        # Strings — brown
        str_fmt = self._fmt("#8B4823")
        self._rules.append((re.compile(r'"""[\s\S]*?"""'), str_fmt))
        self._rules.append((re.compile(r"'''[\s\S]*?'''"), str_fmt))
        self._rules.append((re.compile(r'"[^"\n]*"'), str_fmt))
        self._rules.append((re.compile(r"'[^'\n]*'"), str_fmt))

        # Numbers — blue
        num_fmt = self._fmt("#1E6BB8")
        self._rules.append((re.compile(r"\b\d+\.?\d*([eE][+-]?\d+)?\b"), num_fmt))

        # Operators — red
        op_fmt = self._fmt("#C0392B")
        self._rules.append((re.compile(r"[+\-*/%=<>!&|^~]+"), op_fmt))

        # Comments — muted italic — must be last
        comment_fmt = self._fmt("#8A8A8A", italic=True)
        self._rules.append((re.compile(r"#[^\n]*"), comment_fmt))

    def highlightBlock(self, text: str) -> None:
        for pattern, fmt in self._rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)


# ---------------------------------------------------------------------------
# Line number gutter
# ---------------------------------------------------------------------------

class _LineNumberArea(QWidget):
    def __init__(self, editor: "CodeEditorWidget") -> None:
        super().__init__(editor)
        self._editor = editor
        self.setObjectName("line_number_area")

    def sizeHint(self) -> QSize:
        return QSize(self._editor._line_number_area_width(), 0)

    def paintEvent(self, event) -> None:
        self._editor._paint_line_numbers(event)


# ---------------------------------------------------------------------------
# Code editor
# ---------------------------------------------------------------------------

class CodeEditorWidget(QPlainTextEdit):
    """Editor de código con gutter de números de línea y syntax highlighting."""

    PLACEHOLDER = (
        "# Escribe o pega tu código Python aquí...\n\n"
        "def factorial(n):\n"
        "    if n <= 1:\n"
        "        return 1\n"
        "    else:\n"
        "        return n * factorial(n - 1)\n"
    )

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("code_editor")

        # Font
        font = QFont("Fira Code")
        if not QFont("Fira Code").exactMatch():
            font = QFont("Cascadia Code")
            if not font.exactMatch():
                font = QFont("Consolas")
        font.setPointSize(13)
        self.setFont(font)
        self.setTabStopDistance(QFontMetrics(font).horizontalAdvance(" ") * 4)

        # Line number area
        self._line_number_area = _LineNumberArea(self)

        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)

        self._update_line_number_area_width(0)
        self._highlight_current_line()

        # Syntax highlighting
        self._highlighter = PythonHighlighter(self.document())

        # Placeholder
        self.setPlaceholderText("# Escribe o pega tu código Python aquí...")

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
            self._line_number_area.update(
                0, rect.y(), self._line_number_area.width(), rect.height()
            )
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
        top = round(
            self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        )
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

    # ------------------------------------------------------------------
    # Current line highlight
    # ------------------------------------------------------------------

    def _highlight_current_line(self) -> None:
        extra: list = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            color = QColor(0, 101, 101, 15)  # rgba(0,101,101,0.06) approx
            selection.format.setBackground(color)
            selection.format.setProperty(
                QTextCharFormat.Property.FullWidthSelection, True
            )
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra.append(selection)
        self.setExtraSelections(extra)
