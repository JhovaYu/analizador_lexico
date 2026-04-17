"""
parser.py — Puente entre el árbol Lark y los nodos ASTNode.

Actualizado para coincidir con grammar.py v2 (sin NEWLINE/INDENT/DEDENT).

Uso público:
    from core.parser import parse
    ast_root: Program = parse(source_code)
"""
from __future__ import annotations
from typing import List, Optional, Any

import lark
from lark import Transformer, v_args, Token

from core.grammar import PYTHON_GRAMMAR
from core.ast_nodes import (
    ASTNode, Program, FunctionDef, AssignStatement, IfStatement,
    ElifClause, ElseClause, WhileStatement, ForStatement, ReturnStatement,
    PrintStatement, ExprStatement, BinaryOp, UnaryOp, FunctionCall,
    Identifier, IntLiteral, FloatLiteral, StringLiteral, BoolLiteral,
)


def _pos(meta) -> dict:
    try:
        return {"line": meta.line, "col": meta.column}
    except AttributeError:
        return {"line": 0, "col": 0}


def _is_ast(node: Any) -> bool:
    return isinstance(node, ASTNode)


def _stmts(children: list) -> List[ASTNode]:
    """Filtrar sólo nodos ASTNode de una lista de children mixta."""
    result = []
    for c in children:
        if isinstance(c, ASTNode):
            result.append(c)
    return result


@v_args(meta=True)
class ASTBuilder(Transformer):

    # ------------------------------------------------------------------ pass-throughs
    @v_args(meta=True)
    def statement(self, meta, children):
        """Pass-through: retorna el primer (y único) hijo ASTNode."""
        ast_ch = [c for c in children if _is_ast(c)]
        return ast_ch[0] if ast_ch else None

    # ------------------------------------------------------------------ program
    def start(self, meta, children):
        return Program(body=_stmts(children), **_pos(meta))

    # ------------------------------------------------------------------ funcdef
    def funcdef(self, meta, children):
        # children: NAME, [params list?], statement...
        name = str(children[0])
        idx = 1
        params: List[str] = []
        if idx < len(children) and isinstance(children[idx], list):
            params = children[idx]
            idx += 1
        body = _stmts(children[idx:])
        return FunctionDef(name=name, params=params, body=body, **_pos(meta))

    def params(self, meta, children):
        return [str(c) for c in children if isinstance(c, Token)]

    # ------------------------------------------------------------------ if
    def if_stmt(self, meta, children):
        # children: condition, stmt..., elif_clause*, else_clause?
        condition = children[0]
        rest = children[1:]
        then_body: List[ASTNode] = []
        elifs: List[ElifClause] = []
        else_: List[ASTNode] = []

        for c in rest:
            if isinstance(c, ElifClause):
                elifs.append(c)
            elif isinstance(c, ElseClause):
                else_ = c.body
            elif _is_ast(c):
                then_body.append(c)

        return IfStatement(
            condition=condition,
            then_body=then_body,
            elif_clauses=elifs,
            else_body=else_,
            **_pos(meta)
        )

    def elif_clause(self, meta, children):
        condition = children[0]
        body = _stmts(children[1:])
        return ElifClause(condition=condition, body=body, **_pos(meta))

    def else_clause(self, meta, children):
        return ElseClause(body=_stmts(children), **_pos(meta))

    # ------------------------------------------------------------------ while
    def while_stmt(self, meta, children):
        condition = children[0]
        body = _stmts(children[1:])
        return WhileStatement(condition=condition, body=body, **_pos(meta))

    # ------------------------------------------------------------------ for
    def for_stmt(self, meta, children):
        var = str(children[0])
        ra: List[ASTNode] = []
        body: List[ASTNode] = []
        for c in children[1:]:
            if isinstance(c, list):
                ra = c
            elif _is_ast(c):
                body.append(c)
        return ForStatement(var=var, range_args=ra, body=body, **_pos(meta))

    def range_args(self, meta, children):
        return [c for c in children if _is_ast(c)]

    # ------------------------------------------------------------------ statements
    def assign_stmt(self, meta, children):
        name = str(children[0])
        ast_children = [c for c in children[1:] if _is_ast(c)]
        value = ast_children[0] if ast_children else None
        return AssignStatement(name=name, value=value, **_pos(meta))

    def return_stmt(self, meta, children):
        ast_ch = [c for c in children if _is_ast(c)]
        value = ast_ch[0] if ast_ch else None
        return ReturnStatement(value=value, **_pos(meta))

    def print_stmt(self, meta, children):
        args: List[ASTNode] = []
        for c in children:
            if isinstance(c, list):
                args = c
            elif _is_ast(c):
                args.append(c)
        return PrintStatement(args=args, **_pos(meta))

    def expr_stmt(self, meta, children):
        ast_ch = [c for c in children if _is_ast(c)]
        return ExprStatement(expr=ast_ch[0] if ast_ch else None, **_pos(meta))

    def arglist(self, meta, children):
        return [c for c in children if _is_ast(c)]

    # ------------------------------------------------------------------ binary ops (inline aliases)
    def binary_or(self, meta, children):
        return BinaryOp(op="or", left=children[0], right=children[1], **_pos(meta))

    def binary_and(self, meta, children):
        return BinaryOp(op="and", left=children[0], right=children[1], **_pos(meta))

    def binary_cmp(self, meta, children):
        op = str(children[1]) if len(children) > 2 else "?"
        # children: left, COMP_OP_token, right
        if len(children) == 3:
            return BinaryOp(op=str(children[1]), left=children[0], right=children[2], **_pos(meta))
        return BinaryOp(op="?", left=children[0], right=children[-1], **_pos(meta))

    def binary_add(self, meta, children):
        return BinaryOp(op="+", left=children[0], right=children[1], **_pos(meta))

    def binary_sub(self, meta, children):
        return BinaryOp(op="-", left=children[0], right=children[1], **_pos(meta))

    def binary_mul(self, meta, children):
        return BinaryOp(op="*", left=children[0], right=children[1], **_pos(meta))

    def binary_div(self, meta, children):
        return BinaryOp(op="/", left=children[0], right=children[1], **_pos(meta))

    def binary_floordiv(self, meta, children):
        return BinaryOp(op="//", left=children[0], right=children[1], **_pos(meta))

    def binary_mod(self, meta, children):
        return BinaryOp(op="%", left=children[0], right=children[1], **_pos(meta))

    def binary_pow(self, meta, children):
        return BinaryOp(op="**", left=children[0], right=children[1], **_pos(meta))

    def unary_not(self, meta, children):
        return UnaryOp(op="not", operand=children[0], **_pos(meta))

    def unary_plus(self, meta, children):
        return UnaryOp(op="+", operand=children[0], **_pos(meta))

    def unary_minus(self, meta, children):
        return UnaryOp(op="-", operand=children[0], **_pos(meta))

    # ------------------------------------------------------------------ atoms
    def int_lit(self, meta, children):
        try:
            val = int(str(children[0]))
        except Exception:
            val = 0
        return IntLiteral(value=val, **_pos(meta))

    def float_lit(self, meta, children):
        try:
            val = float(str(children[0]))
        except Exception:
            val = 0.0
        return FloatLiteral(value=val, **_pos(meta))

    def str_lit(self, meta, children):
        raw = str(children[0])
        # Strip outer quotes (single or double)
        if len(raw) >= 2 and raw[0] in ('"', "'"):
            value = raw[1:-1]
        else:
            value = raw
        return StringLiteral(value=value, **_pos(meta))

    def bool_true(self, meta, children):
        return BoolLiteral(value=True, **_pos(meta))

    def bool_false(self, meta, children):
        return BoolLiteral(value=False, **_pos(meta))

    def name_ref(self, meta, children):
        return Identifier(name=str(children[0]), **_pos(meta))

    def func_call(self, meta, children):
        name = str(children[0])
        args: List[ASTNode] = []
        for c in children[1:]:
            if isinstance(c, list):
                args = c
            elif _is_ast(c):
                args.append(c)
        return FunctionCall(name=name, args=args, **_pos(meta))


# ---------------------------------------------------------------------------
# Lark instance (singleton lazy — se recrea si hay cambios)
# ---------------------------------------------------------------------------

_LARK_INSTANCE: Optional[lark.Lark] = None


def reset_parser() -> None:
    """Forzar reconstrucción del parser (útil al cambiar la gramática en runtime)."""
    global _LARK_INSTANCE
    _LARK_INSTANCE = None


def _get_lark() -> lark.Lark:
    global _LARK_INSTANCE
    if _LARK_INSTANCE is None:
        _LARK_INSTANCE = lark.Lark(
            PYTHON_GRAMMAR,
            parser="earley",
            propagate_positions=True,
            ambiguity="resolve",
        )
    return _LARK_INSTANCE


# ---------------------------------------------------------------------------
# Función pública
# ---------------------------------------------------------------------------

class ParseError(Exception):
    def __init__(self, message: str, line: int = 0, col: int = 0):
        super().__init__(message)
        self.line = line
        self.col = col


def parse(source: str) -> Program:
    """
    Analizar código fuente y retornar nodo raíz Program.
    Raises ParseError si hay errores de sintaxis.
    """
    lark_inst = _get_lark()
    try:
        tree = lark_inst.parse(source)
        builder = ASTBuilder()
        result = builder.transform(tree)
        if isinstance(result, Program):
            return result
        if isinstance(result, ASTNode):
            return Program(body=[result])
        return Program(body=[])

    except lark.exceptions.UnexpectedToken as e:
        line = getattr(e, "line", 0)
        col  = getattr(e, "column", 0)
        tok  = getattr(e, "token", "?")
        expected = ""
        if hasattr(e, "expected"):
            expected = ", ".join(str(x) for x in list(e.expected)[:4])
        msg = f"Token inesperado '{tok}' en línea {line}, columna {col}."
        if expected:
            msg += f" Se esperaba: {expected}"
        raise ParseError(msg, line=line, col=col) from e

    except lark.exceptions.UnexpectedCharacters as e:
        line = getattr(e, "line", 0)
        col  = getattr(e, "column", 0)
        raise ParseError(
            f"Carácter inesperado en línea {line}, columna {col}.",
            line=line, col=col
        ) from e

    except lark.exceptions.UnexpectedEOF as e:
        raise ParseError(
            "Fin de archivo inesperado. ¿Falta cerrar un bloque 'if', 'def' o 'while'?",
            line=0, col=0
        ) from e

    except Exception as e:
        raise ParseError(f"Error de análisis sintáctico: {e}", line=0, col=0) from e
