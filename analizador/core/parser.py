"""
core/parser.py — Adaptador para parsear con Lark y construir el Árbol de Derivación fuertemente tipado.
"""
import lark
from typing import Optional, List, Union

from core.grammar import PYTHON_GRAMMAR
from core.parse_tree_nodes import *

_LARK_INSTANCE: Optional[lark.Lark] = None

# Mapeo de reglas EBNF a nuestras Dataclasses
_RULE_MAP = {
    "start": ProgramNode,
    "statement": StatementNode,
    "funcdef": FuncDefNode,
    "params": ParamsNode,
    "if_stmt": IfStmtNode,
    "elif_clause": ElifClauseNode,
    "else_clause": ElseClauseNode,
    "while_stmt": WhileStmtNode,
    "for_stmt": ForStmtNode,
    "range_args": RangeArgsNode,
    "assign_stmt": AssignStmtNode,
    "return_stmt": ReturnStmtNode,
    "print_stmt": PrintStmtNode,
    "expr_stmt": ExprStmtNode,
    "arglist": ArgListNode,
    
    # Expresiones anidadas
    "expr": ExprNode,
    "or_expr": ExprNode,
    "and_expr": ExprNode,
    "not_expr": ExprNode,
    "comparison": ExprNode,
    "arith": ExprNode,
    "term": ExprNode,
    "factor": ExprNode,
    "power": ExprNode,
    "atom": ExprNode,
    
    # Aliases de Expresiones Binarias/Unarias
    "binary_or": ExprNode,
    "binary_and": ExprNode,
    "unary_not": ExprNode,
    "binary_cmp": ExprNode,
    "binary_add": ExprNode,
    "binary_sub": ExprNode,
    "binary_mul": ExprNode,
    "binary_div": ExprNode,
    "binary_floordiv": ExprNode,
    "binary_mod": ExprNode,
    "binary_pow": ExprNode,
    "unary_plus": ExprNode,
    "unary_minus": ExprNode,
    
    # Literales (Atom) - Estos no son tokens terminales directamente, son ramas que acunan tokens
    "float_lit": ExprNode,
    "int_lit": ExprNode,
    "str_lit": ExprNode,
    "bool_true": ExprNode,
    "bool_false": ExprNode,
    "func_call": ExprNode,
    "name_ref": ExprNode,
}

def reset_parser() -> None:
    """Forzar reconstrucción del parser (útil al cambiar la gramática en runtime)."""
    global _LARK_INSTANCE
    _LARK_INSTANCE = None

def _get_lark() -> lark.Lark:
    global _LARK_INSTANCE
    if _LARK_INSTANCE is None:
        # Se requiere keep_all_tokens=True para no perder palabras reservadas en el parse tree
        _LARK_INSTANCE = lark.Lark(
            PYTHON_GRAMMAR, 
            parser='earley', 
            propagate_positions=True, 
            keep_all_tokens=True,
            ambiguity='resolve'
        )
    return _LARK_INSTANCE


def tree_to_derivation(node: Union[lark.Tree, lark.Token]) -> ParseTreeNode:
    """Convierte de forma recursiva el árbol crudo de Lark a nuestra capa de abstracción."""
    if isinstance(node, lark.Token):
        return TerminalNode(
            line=node.line or 0, 
            col=node.column or 0, 
            token_type=node.type, 
            value=node.value
        )
    
    # Es un lark.Tree
    children = [tree_to_derivation(c) for c in node.children]
    
    # Extraer posición del metaobjeto o heredar del primer hijo
    meta = getattr(node, "meta", None)
    if meta and getattr(meta, "line", None) is not None:
        line = meta.line
        col = meta.column
    elif children:
        line = children[0].line
        col = children[0].col
    else:
        line = col = 0
        
    node_cls = _RULE_MAP.get(node.data, NonTerminalNode)
    # Pasar el rule_name explícitamente para que la UI sepa qué regla era (sin importar qué NodeCls usemos)
    return node_cls(line=line, col=col, rule_name=node.data, child_nodes=children)


def parse(code: str) -> ProgramNode:
    """
    Parsea código Python en un Árbol de Derivación fuertemente tipado.
    Lanza excepciones de Lark en caso de error léxico o sintáctico.
    """
    lark_parser = _get_lark()
    raw_tree = lark_parser.parse(code)
    derivation_tree = tree_to_derivation(raw_tree)
    
    return derivation_tree
