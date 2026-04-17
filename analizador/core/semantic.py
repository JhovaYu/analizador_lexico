"""
core/semantic.py — Analizador semántico: tabla de símbolos + verificaciones de tipos basado en el Árbol de Derivación.
"""
from typing import List, Optional

from core.parse_tree_nodes import (
    ParseTreeVisitor, ParseTreeNode, TerminalNode, ProgramNode, FuncDefNode,
    AssignStmtNode, IfStmtNode, WhileStmtNode, ForStmtNode, ReturnStmtNode,
    PrintStmtNode, ArgListNode, ExprNode, ParamsNode
)
from core.traversals import get_preorder
from utils.symbol_table import SymbolTable, Symbol
from utils.error_handler import AnalysisError, Phase, Severity


def find_first_terminal(node: ParseTreeNode, token_type: str) -> Optional[TerminalNode]:
    """Busca recursivamente el primer terminal de un tipo específico."""
    for n in get_preorder(node):
        if isinstance(n, TerminalNode) and n.token_type == token_type:
            return n
    return None

def find_all_terminals(node: ParseTreeNode, token_type: str) -> List[TerminalNode]:
    return [n for n in get_preorder(node) if isinstance(n, TerminalNode) and n.token_type == token_type]


class SemanticAnalyzer(ParseTreeVisitor):
    """Recorre el Parse Tree estricto y aplica verificaciones semánticas."""

    def __init__(self) -> None:
        self.symbol_table = SymbolTable()
        self.errors: List[AnalysisError] = []
        # Map function name → expected arg count
        self._functions: dict = {}
        # Current return context
        self._in_function: Optional[str] = None

    def analyze(self, root: ProgramNode) -> List[AnalysisError]:
        self.errors.clear()
        self.symbol_table = SymbolTable()
        self._functions.clear()
        
        self.visit(root)
        
        # Reportar variables no usadas
        for sym in self.symbol_table.unused_symbols():
            if sym.name not in self._functions:
                self.errors.append(AnalysisError(
                    phase=Phase.SEMANTIC,
                    message=f"Variable '{sym.name}' declarada pero nunca utilizada.",
                    line=sym.line, col=0,
                    severity=Severity.WARNING,
                ))
        return self.errors

    def _error(self, message: str, line: int, col: int = 0, severity: Severity = Severity.ERROR) -> None:
        self.errors.append(AnalysisError(
            phase=Phase.SEMANTIC, message=message,
            line=line, col=col, severity=severity,
        ))

    # --- Visitadores para reglas EBNF principales ---

    def visit_ProgramNode(self, node: ProgramNode) -> None:
        node.generic_visit(self)

    def visit_FuncDefNode(self, node: FuncDefNode) -> None:
        # funcdef: "def" NAME "(" params? ")" ":" statement+
        # El NAME de la función es siempre el segundo elemento tras 'def' en un parser estructurado Earley.
        name_node = node.get_children()[1]
        if not isinstance(name_node, TerminalNode):
            name_node = find_first_terminal(node, "NAME")
            
        if not name_node:
            node.generic_visit(self)
            return

        func_name = name_node.value
        
        # Buscar parámetros
        params = []
        for child in node.get_children():
            if isinstance(child, ParamsNode):
                params = [t.value for t in find_all_terminals(child, "NAME")]

        self._functions[func_name] = len(params)
        self.symbol_table.define(func_name, "function", name_node.line)
        self.symbol_table.mark_used(func_name, name_node.line)

        self.symbol_table.enter_scope()
        old_fn = self._in_function
        self._in_function = func_name

        for p in params:
            self.symbol_table.define(p, "param", name_node.line)

        # Visitar cuerpo (escondido en generic_visit pasará por statements)
        node.generic_visit(self)

        self._in_function = old_fn
        self.symbol_table.exit_scope()

    def visit_AssignStmtNode(self, node: AssignStmtNode) -> None:
        # assign_stmt: NAME "=" expr ";"?
        name_node = node.get_children()[0]
        if isinstance(name_node, TerminalNode) and name_node.token_type == "NAME":
            var_name = name_node.value
            self.symbol_table.define(var_name, "unknown", name_node.line)
            
        node.generic_visit(self)

    def visit_TerminalNode(self, node: TerminalNode) -> None:
        # Cuando encontramos un IDENTIFICADOR libre de tipo NAME, debemos ver si existe en la tabla de símbolos.
        if node.token_type == "NAME":
            # Verificar si está en la tabla (o si es función builtin)
            if node.value not in ("print", "range", "int", "float", "str", "len"):
                sym = self.symbol_table.lookup(node.value)
                if sym is None and node.value not in self._functions:
                    self._error(
                        f"Variable o función '{node.value}' utilizada antes de ser declarada.",
                        line=node.line, col=node.col,
                    )
                else:
                    self.symbol_table.mark_used(node.value, node.line)

    def visit_ExprNode(self, node: ExprNode) -> None:
        # Verificaciones para llamadas a función
        if node.rule_name == "func_call":
            # Extraer el NAME invocado y checar argumentos
            name_node = node.get_children()[0]
            if isinstance(name_node, TerminalNode) and name_node.token_type == "NAME":
                func_name = name_node.value
                
                # Rescatar número de argumentos
                arglist = next((c for c in node.get_children() if isinstance(c, ArgListNode)), None)
                num_args = 0
                if arglist:
                    # En la gramática: arglist: expr ("," expr)* -> Contamos las expr separadas por comas.
                    # Simplificación: contamos los hijos de tipo ExprNode
                    num_args = sum(1 for c in arglist.get_children() if isinstance(c, ExprNode))
                
                if func_name not in ("print", "range", "int", "float", "str", "len"):
                    expected = self._functions.get(func_name)
                    if expected is not None and num_args != expected:
                        self._error(
                            f"Función '{func_name}' llamada con {num_args} argumento(s), "
                            f"pero espera {expected}.",
                            line=node.line, col=node.col,
                        )
        
        # Validaciones de operadores lógicos y aritméticos (Simplificadas para el Árbol de Derivación)
        node.generic_visit(self)

    def visit_ForStmtNode(self, node: ForStmtNode) -> None:
        # for_stmt: "for" NAME "in" "range" "(" range_args ")" ":" statement+
        name_node = find_first_terminal(node, "NAME")
        if name_node:
            self.symbol_table.define(name_node.value, "int", name_node.line)
            self.symbol_table.mark_used(name_node.value, name_node.line)
        node.generic_visit(self)
