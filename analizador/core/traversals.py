"""
core/traversals.py — Algoritmos de recorrido para el Árbol de Derivación.
"""
from typing import List
from core.parse_tree_nodes import ParseTreeNode

def get_preorder(node: ParseTreeNode) -> List[ParseTreeNode]:
    """Recorrido Preorden: Raíz, luego Hijos (izq a der)."""
    result = [node]
    for child in node.get_children():
        result.extend(get_preorder(child))
    return result

def get_postorder(node: ParseTreeNode) -> List[ParseTreeNode]:
    """Recorrido Postorden: Hijos (izq a der), luego Raíz."""
    result = []
    for child in node.get_children():
        result.extend(get_postorder(child))
    result.append(node)
    return result

def get_inorder(node: ParseTreeNode) -> List[ParseTreeNode]:
    """
    Recorrido Inorden Generalizado (para árboles n-arios).
    Visita el primer hijo (izquierdo), luego la raíz, luego el resto de hijos.
    Esto permite a las expresiones binarias comportarse naturalmente (izquierdo -> operador -> derecho).
    """
    result = []
    children = node.get_children()
    
    if not children:
        return [node]
    
    # 1. Visitar primer hijo
    result.extend(get_inorder(children[0]))
    
    # 2. Visitar raíz
    result.append(node)
    
    # 3. Visitar el resto de los hijos
    for child in children[1:]:
        result.extend(get_inorder(child))
        
    return result
