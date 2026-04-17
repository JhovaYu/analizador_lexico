"""
semantic.py — Analizador semántico: tabla de símbolos + verificaciones de tipos.
"""
from __future__ import annotations
from typing import List, Optional

from core.ast_nodes import (
    ASTVisitor, ASTNode, Program, FunctionDef, AssignStatement, IfStatement,
    ElifClause, ElseClause, WhileStatement, ForStatement, ReturnStatement,
    PrintStatement, ExprStatement, BinaryOp, UnaryOp, FunctionCall,
    Identifier, IntLiteral, FloatLiteral, StringLiteral, BoolLiteral,
)
from utils.symbol_table import SymbolTable, Symbol
from utils.error_handler import AnalysisError, Phase, Severity


class SemanticAnalyzer(ASTVisitor):
    """Recorre el AST y aplica verificaciones semánticas."""

    def __init__(self) -> None:
        self.symbol_table = SymbolTable()
        self.errors: List[AnalysisError] = []
        # Map function name → expected arg count
        self._functions: dict = {}
        # Current return context
        self._in_function: Optional[str] = None

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def analyze(self, root: Program) -> List[AnalysisError]:
        """Analizar el árbol y retornar lista de errores y warnings."""
        self.errors.clear()
        self.symbol_table = SymbolTable()
        self._functions.clear()
        self.visit(root)
        # Reportar variables declaradas pero nunca usadas
        for sym in self.symbol_table.unused_symbols():
            if sym.name not in self._functions:
                self.errors.append(AnalysisError(
                    phase=Phase.SEMANTIC,
                    message=f"Variable '{sym.name}' declarada pero nunca utilizada.",
                    line=sym.line, col=0,
                    severity=Severity.WARNING,
                ))
        return self.errors

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _error(self, message: str, line: int, col: int = 0,
                severity: Severity = Severity.ERROR) -> None:
        self.errors.append(AnalysisError(
            phase=Phase.SEMANTIC, message=message,
            line=line, col=col, severity=severity,
        ))

    def _infer_type(self, node: ASTNode) -> str:
        """Intentar inferir el tipo de una expresión."""
        if isinstance(node, IntLiteral):
            return "int"
        if isinstance(node, FloatLiteral):
            return "float"
        if isinstance(node, StringLiteral):
            return "str"
        if isinstance(node, BoolLiteral):
            return "bool"
        if isinstance(node, Identifier):
            sym = self.symbol_table.lookup(node.name)
            return sym.type_ if sym else "unknown"
        if isinstance(node, BinaryOp):
            lt = self._infer_type(node.left) if node.left else "unknown"
            rt = self._infer_type(node.right) if node.right else "unknown"
            # Type coercion rules
            if lt == rt:
                return lt
            if {lt, rt} <= {"int", "float"}:
                return "float"
            return "unknown"
        if isinstance(node, FunctionCall):
            sym = self.symbol_table.lookup(node.name)
            return sym.type_ if sym else "unknown"
        return "unknown"

    # ------------------------------------------------------------------
    # Visitors
    # ------------------------------------------------------------------

    def visit_Program(self, node: Program) -> None:
        for stmt in node.body:
            self.visit(stmt)

    def visit_FunctionDef(self, node: FunctionDef) -> None:
        # Registrar la función antes de procesar su cuerpo (permite recursión)
        self._functions[node.name] = len(node.params)
        self.symbol_table.define(node.name, "function", node.line)
        self.symbol_table.mark_used(node.name, node.line)  # evitar warning de no uso

        self.symbol_table.enter_scope()
        old_fn = self._in_function
        self._in_function = node.name

        for param in node.params:
            self.symbol_table.define(param, "param", node.line)

        for stmt in node.body:
            self.visit(stmt)

        # Marcar parámetros como usados para evitar falsos positivos
        for sym in self.symbol_table.current_scope_symbols():
            if sym.type_ == "param" and not sym.is_used:
                pass  # params sin usar son warnings opcionales — omitir por ahora

        self._in_function = old_fn
        self.symbol_table.exit_scope()

    def visit_AssignStatement(self, node: AssignStatement) -> None:
        if node.value:
            self.visit(node.value)
        inferred = self._infer_type(node.value) if node.value else "unknown"
        self.symbol_table.define(node.name, inferred, node.line)

    def visit_IfStatement(self, node: IfStatement) -> None:
        if node.condition:
            self.visit(node.condition)
        for stmt in node.then_body:
            self.visit(stmt)
        for clause in node.elif_clauses:
            self.visit(clause)
        for stmt in node.else_body:
            self.visit(stmt)

    def visit_ElifClause(self, node: ElifClause) -> None:
        if node.condition:
            self.visit(node.condition)
        for stmt in node.body:
            self.visit(stmt)

    def visit_ElseClause(self, node: ElseClause) -> None:
        for stmt in node.body:
            self.visit(stmt)

    def visit_WhileStatement(self, node: WhileStatement) -> None:
        if node.condition:
            self.visit(node.condition)
        for stmt in node.body:
            self.visit(stmt)

    def visit_ForStatement(self, node: ForStatement) -> None:
        for arg in node.range_args:
            self.visit(arg)
        # Variable de iteración se define en este scope
        self.symbol_table.define(node.var, "int", node.line)
        self.symbol_table.mark_used(node.var, node.line)
        for stmt in node.body:
            self.visit(stmt)

    def visit_ReturnStatement(self, node: ReturnStatement) -> None:
        if node.value:
            self.visit(node.value)

    def visit_PrintStatement(self, node: PrintStatement) -> None:
        for arg in node.args:
            self.visit(arg)

    def visit_ExprStatement(self, node: ExprStatement) -> None:
        if node.expr:
            self.visit(node.expr)

    def visit_BinaryOp(self, node: BinaryOp) -> None:
        if node.left:
            self.visit(node.left)
        if node.right:
            self.visit(node.right)
        # Verificar incompatibilidad de tipos (int + str)
        if node.left and node.right:
            lt = self._infer_type(node.left)
            rt = self._infer_type(node.right)
            if lt != "unknown" and rt != "unknown":
                numeric = {"int", "float"}
                if node.op in ("+", "-", "*", "/", "//", "%", "**"):
                    if lt == "str" or rt == "str":
                        if not (lt == "str" and rt == "str" and node.op == "+"):
                            self._error(
                                f"Operación '{node.op}' entre tipos incompatibles: {lt} y {rt}.",
                                line=node.line, col=node.col,
                            )

    def visit_UnaryOp(self, node: UnaryOp) -> None:
        if node.operand:
            self.visit(node.operand)

    def visit_FunctionCall(self, node: FunctionCall) -> None:
        for arg in node.args:
            self.visit(arg)
        # Verificar si la función fue definida
        if node.name not in ("print", "range", "int", "float", "str", "len"):
            sym = self.symbol_table.lookup(node.name)
            if sym is None:
                self._error(
                    f"Función '{node.name}' utilizada antes de ser definida.",
                    line=node.line, col=node.col,
                )
            else:
                self.symbol_table.mark_used(node.name, node.line)
                expected = self._functions.get(node.name)
                if expected is not None and len(node.args) != expected:
                    self._error(
                        f"Función '{node.name}' llamada con {len(node.args)} argumento(s), "
                        f"pero espera {expected}.",
                        line=node.line, col=node.col,
                    )

    def visit_Identifier(self, node: Identifier) -> None:
        sym = self.symbol_table.lookup(node.name)
        if sym is None and node.name not in self._functions:
            self._error(
                f"Variable '{node.name}' utilizada antes de ser declarada.",
                line=node.line, col=node.col,
            )
        else:
            self.symbol_table.mark_used(node.name, node.line)

    def visit_IntLiteral(self, node: IntLiteral) -> None:
        pass

    def visit_FloatLiteral(self, node: FloatLiteral) -> None:
        pass

    def visit_StringLiteral(self, node: StringLiteral) -> None:
        pass

    def visit_BoolLiteral(self, node: BoolLiteral) -> None:
        pass
