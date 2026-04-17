"""
ast_nodes.py — Definición de nodos del Árbol de Sintaxis Abstracta (AST).
Todos los nodos usan @dataclass y heredan de ASTNode.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Any


# ---------------------------------------------------------------------------
# Visitor base
# ---------------------------------------------------------------------------

class ASTVisitor:
    """Visitante base. Subclasificar para implementar análisis semántico."""

    def visit(self, node: "ASTNode") -> Any:
        """Despachar al método visit_<ClassName> si existe, si no generic_visit."""
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, self.generic_visit)
        return method(node)

    def generic_visit(self, node: "ASTNode") -> Any:
        """Visitar todos los hijos sin hacer nada por defecto."""
        for child in node.children():
            if child is not None:
                self.visit(child)
        return None


# ---------------------------------------------------------------------------
# Nodo base
# ---------------------------------------------------------------------------

@dataclass
class ASTNode:
    line: int = 0
    col: int = 0

    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit(self)

    def children(self) -> List["ASTNode"]:
        """Retorna la lista de hijos directos del nodo. Sobreescribir en cada subclase."""
        return []

    def label(self) -> str:
        """Texto corto para mostrar en el grafo del AST."""
        return type(self).__name__


# ---------------------------------------------------------------------------
# Nodos Statement
# ---------------------------------------------------------------------------

@dataclass
class Program(ASTNode):
    body: List[ASTNode] = field(default_factory=list)

    def children(self) -> List[ASTNode]:
        return self.body

    def label(self) -> str:
        return "Prog"


@dataclass
class FunctionDef(ASTNode):
    name: str = ""
    params: List[str] = field(default_factory=list)
    body: List[ASTNode] = field(default_factory=list)

    def children(self) -> List[ASTNode]:
        return self.body

    def label(self) -> str:
        return f"def {self.name}()"


@dataclass
class AssignStatement(ASTNode):
    name: str = ""
    value: Optional[ASTNode] = None

    def children(self) -> List[ASTNode]:
        return [self.value] if self.value else []

    def label(self) -> str:
        return f"{self.name} ="


@dataclass
class IfStatement(ASTNode):
    condition: Optional[ASTNode] = None
    then_body: List[ASTNode] = field(default_factory=list)
    elif_clauses: List[ASTNode] = field(default_factory=list)
    else_body: List[ASTNode] = field(default_factory=list)

    def children(self) -> List[ASTNode]:
        kids: List[ASTNode] = []
        if self.condition:
            kids.append(self.condition)
        kids.extend(self.then_body)
        kids.extend(self.elif_clauses)
        kids.extend(self.else_body)
        return kids

    def label(self) -> str:
        return "if"


@dataclass
class ElifClause(ASTNode):
    condition: Optional[ASTNode] = None
    body: List[ASTNode] = field(default_factory=list)

    def children(self) -> List[ASTNode]:
        kids: List[ASTNode] = []
        if self.condition:
            kids.append(self.condition)
        kids.extend(self.body)
        return kids

    def label(self) -> str:
        return "elif"


@dataclass
class ElseClause(ASTNode):
    body: List[ASTNode] = field(default_factory=list)

    def children(self) -> List[ASTNode]:
        return self.body

    def label(self) -> str:
        return "else"


@dataclass
class WhileStatement(ASTNode):
    condition: Optional[ASTNode] = None
    body: List[ASTNode] = field(default_factory=list)

    def children(self) -> List[ASTNode]:
        kids: List[ASTNode] = []
        if self.condition:
            kids.append(self.condition)
        kids.extend(self.body)
        return kids

    def label(self) -> str:
        return "while"


@dataclass
class ForStatement(ASTNode):
    var: str = ""
    range_args: List[ASTNode] = field(default_factory=list)
    body: List[ASTNode] = field(default_factory=list)

    def children(self) -> List[ASTNode]:
        return self.range_args + self.body

    def label(self) -> str:
        return f"for {self.var}"


@dataclass
class ReturnStatement(ASTNode):
    value: Optional[ASTNode] = None

    def children(self) -> List[ASTNode]:
        return [self.value] if self.value else []

    def label(self) -> str:
        return "return"


@dataclass
class PrintStatement(ASTNode):
    args: List[ASTNode] = field(default_factory=list)

    def children(self) -> List[ASTNode]:
        return self.args

    def label(self) -> str:
        return "print()"


@dataclass
class ExprStatement(ASTNode):
    expr: Optional[ASTNode] = None

    def children(self) -> List[ASTNode]:
        return [self.expr] if self.expr else []

    def label(self) -> str:
        return "expr"


# ---------------------------------------------------------------------------
# Nodos Expresión
# ---------------------------------------------------------------------------

@dataclass
class BinaryOp(ASTNode):
    op: str = ""
    left: Optional[ASTNode] = None
    right: Optional[ASTNode] = None

    def children(self) -> List[ASTNode]:
        kids: List[ASTNode] = []
        if self.left:
            kids.append(self.left)
        if self.right:
            kids.append(self.right)
        return kids

    def label(self) -> str:
        return self.op


@dataclass
class UnaryOp(ASTNode):
    op: str = ""
    operand: Optional[ASTNode] = None

    def children(self) -> List[ASTNode]:
        return [self.operand] if self.operand else []

    def label(self) -> str:
        return f"unary {self.op}"


@dataclass
class FunctionCall(ASTNode):
    name: str = ""
    args: List[ASTNode] = field(default_factory=list)

    def children(self) -> List[ASTNode]:
        return self.args

    def label(self) -> str:
        return f"{self.name}()"


@dataclass
class Identifier(ASTNode):
    name: str = ""

    def children(self) -> List[ASTNode]:
        return []

    def label(self) -> str:
        return self.name


# ---------------------------------------------------------------------------
# Nodos Literal
# ---------------------------------------------------------------------------

@dataclass
class IntLiteral(ASTNode):
    value: int = 0

    def children(self) -> List[ASTNode]:
        return []

    def label(self) -> str:
        return str(self.value)


@dataclass
class FloatLiteral(ASTNode):
    value: float = 0.0

    def children(self) -> List[ASTNode]:
        return []

    def label(self) -> str:
        return str(self.value)


@dataclass
class StringLiteral(ASTNode):
    value: str = ""

    def children(self) -> List[ASTNode]:
        return []

    def label(self) -> str:
        return f'"{self.value[:12]}{"..." if len(self.value) > 12 else ""}"'


@dataclass
class BoolLiteral(ASTNode):
    value: bool = False

    def children(self) -> List[ASTNode]:
        return []

    def label(self) -> str:
        return "True" if self.value else "False"
