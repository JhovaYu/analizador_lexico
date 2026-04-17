"""
core/parse_tree_nodes.py — Estructura tipada del Árbol de Derivación (Parse Tree).
Mapea el árbol genérico de Lark a nuestro sistema fuertemente tipado utilizando el patrón Visitor.
"""
from dataclasses import dataclass, field
from typing import List, Any

class ParseTreeVisitor:
    """Clase base Visitor genérica para recorrer el Árbol de Derivación."""
    def visit(self, node: 'ParseTreeNode') -> Any:
        return node.accept(self)

@dataclass
class ParseTreeNode:
    """Nodo base del árbol."""
    line: int = 0
    col: int = 0

    def label(self) -> str:
        return self.__class__.__name__

    def get_children(self) -> List['ParseTreeNode']:
        return []

    def accept(self, visitor: ParseTreeVisitor) -> Any:
        pass

@dataclass
class TerminalNode(ParseTreeNode):
    """Representa una hoja pura (tokens: literales, palabras reservadas, símbolos)."""
    token_type: str = ""
    value: str = ""

    def label(self) -> str:
        return f"{self.value}"

    def accept(self, visitor: ParseTreeVisitor) -> Any:
        if hasattr(visitor, "visit_TerminalNode"):
            return visitor.visit_TerminalNode(self)
        return None

@dataclass
class NonTerminalNode(ParseTreeNode):
    """Representa reglas gramaticales internas con hijos."""
    rule_name: str = ""
    child_nodes: List[ParseTreeNode] = field(default_factory=list)

    def label(self) -> str:
        # Tal como solicitó el usuario: Mostrar la regla explícita de EBNF.
        return self.rule_name if self.rule_name else self.__class__.__name__

    def get_children(self) -> List[ParseTreeNode]:
        return self.child_nodes

    def accept(self, visitor: ParseTreeVisitor) -> Any:
        """Autodispatch basado en el nombre de la clase hija."""
        method_name = f"visit_{self.__class__.__name__}"
        if hasattr(visitor, method_name):
            return getattr(visitor, method_name)(self)
        else:
            return self.generic_visit(visitor)

    def generic_visit(self, visitor: ParseTreeVisitor) -> Any:
        for child in self.child_nodes:
            child.accept(visitor)


@dataclass
class ProgramNode(NonTerminalNode):
    pass

@dataclass
class StatementNode(NonTerminalNode):
    pass

# Funciones
@dataclass
class FuncDefNode(NonTerminalNode):
    pass

@dataclass
class ParamsNode(NonTerminalNode):
    pass

# Control de Flujo
@dataclass
class IfStmtNode(NonTerminalNode):
    pass

@dataclass
class ElifClauseNode(NonTerminalNode):
    pass

@dataclass
class ElseClauseNode(NonTerminalNode):
    pass

@dataclass
class WhileStmtNode(NonTerminalNode):
    pass

@dataclass
class ForStmtNode(NonTerminalNode):
    pass

@dataclass
class RangeArgsNode(NonTerminalNode):
    pass

# Statements Simples
@dataclass
class AssignStmtNode(NonTerminalNode):
    pass

@dataclass
class ReturnStmtNode(NonTerminalNode):
    pass

@dataclass
class PrintStmtNode(NonTerminalNode):
    pass

@dataclass
class ExprStmtNode(NonTerminalNode):
    pass

# Expresiones y Extras
@dataclass
class ArgListNode(NonTerminalNode):
    pass

@dataclass
class ExprNode(NonTerminalNode):
    pass
