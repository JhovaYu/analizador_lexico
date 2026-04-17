"""
lexer.py — DFA refactorizado para subconjunto de Python.

Tokens devueltos: {'token': str, 'attribute': int, 'type': str, 'line': int, 'col': int}

Tabla de atributos:
  Palabras reservadas:  20-39
  Identificador:         1
  Número entero:         2
  Número real:           3
  String:                4
  Operadores:          100-120
  Delimitadores:       200-210
  Comentario:          300  (se ignora pero se registra)
  Desconocido/Error:    -1
"""
from __future__ import annotations
from typing import List, Dict, Any

Token = Dict[str, Any]

# ---------------------------------------------------------------------------
# Tablas de palabras reservadas y símbolos
# ---------------------------------------------------------------------------

KEYWORDS: Dict[str, int] = {
    "def":    20, "if":     21, "elif":   22, "else":   23,
    "while":  24, "for":    25, "in":     26, "range":  27,
    "return": 28, "print":  29, "and":    30, "or":     31,
    "not":    32, "True":   33, "False":  34, "int":    35,
    "float":  36, "str":    37, "pass":   38, "break":  39,
    "continue": 40, "import": 41, "from": 42, "class": 43,
    "lambda": 44, "None":   45,
}

# Operadores multicarácter — orden importa (más largo primero)
MULTI_CHAR_OPS: Dict[str, int] = {
    "**": 100, "//": 101, "==": 102, "!=": 103,
    "<=": 104, ">=": 105, ":=": 106,
}

SINGLE_CHAR_OPS: Dict[str, int] = {
    "+": 110, "-": 111, "*": 112, "/": 113,
    "%": 114, "=": 115, "<": 116, ">": 117,
    "^": 118,
}

DELIMITERS: Dict[str, int] = {
    "(": 200, ")": 201, "[": 202, "]": 203,
    "{": 204, "}": 205, ",": 206, ";": 207,
    ":": 208, ".": 209,
}


class DFALexer:
    """Analizador léxico basado en DFA (Autómata Finito Determinista)."""

    def tokenize(self, source: str) -> List[Token]:
        tokens: List[Token] = []
        i = 0
        n = len(source)
        line = 1
        line_start = 0

        while i < n:
            col = i - line_start + 1
            ch = source[i]

            # ---------------------------------------------------------- newline
            if ch == "\n":
                line += 1
                line_start = i + 1
                i += 1
                continue

            # ---------------------------------------------------------- whitespace
            if ch in (" ", "\t", "\r"):
                i += 1
                continue

            # ---------------------------------------------------------- comentarios #
            if ch == "#":
                j = i
                while j < n and source[j] != "\n":
                    j += 1
                # comentarios se ignoran (no se agregan a tokens)
                i = j
                continue

            # ---------------------------------------------------------- strings " y '
            if ch in ('"', "'"):
                quote = ch
                # Triple-quote support
                if source[i:i+3] in ('"""', "'''"):
                    quote = source[i:i+3]
                    j = i + 3
                    while j < n and source[j:j+3] != quote:
                        if source[j] == "\n":
                            line += 1
                            line_start = j + 1
                        j += 1
                    j += 3
                else:
                    j = i + 1
                    while j < n and source[j] != quote and source[j] != "\n":
                        if source[j] == "\\" and j + 1 < n:
                            j += 2
                        else:
                            j += 1
                    j += 1
                lexeme = source[i:j]
                tokens.append({"token": lexeme, "attribute": 4, "type": "Cadena", "line": line, "col": col})
                i = j
                continue

            # ---------------------------------------------------------- números
            if ch.isdigit() or (ch == "." and i + 1 < n and source[i+1].isdigit()):
                j = i
                is_float = False
                while j < n and source[j].isdigit():
                    j += 1
                if j < n and source[j] == "." and j + 1 < n and source[j+1].isdigit():
                    is_float = True
                    j += 1
                    while j < n and source[j].isdigit():
                        j += 1
                    # Exponent e.g. 1.5e10
                    if j < n and source[j] in ("e", "E"):
                        j += 1
                        if j < n and source[j] in ("+", "-"):
                            j += 1
                        while j < n and source[j].isdigit():
                            j += 1
                lexeme = source[i:j]
                if is_float:
                    tokens.append({"token": lexeme, "attribute": 3, "type": "Número Real", "line": line, "col": col})
                else:
                    tokens.append({"token": lexeme, "attribute": 2, "type": "Número Entero", "line": line, "col": col})
                i = j
                continue

            # ---------------------------------------------------------- identificadores / palabras reservadas
            if ch.isalpha() or ch == "_":
                j = i
                while j < n and (source[j].isalnum() or source[j] == "_"):
                    j += 1
                lexeme = source[i:j]
                if lexeme in KEYWORDS:
                    tokens.append({"token": lexeme, "attribute": KEYWORDS[lexeme], "type": "Palabra Reservada", "line": line, "col": col})
                else:
                    tokens.append({"token": lexeme, "attribute": 1, "type": "Identificador", "line": line, "col": col})
                i = j
                continue

            # ---------------------------------------------------------- operadores multicarácter
            two = source[i:i+2]
            if two in MULTI_CHAR_OPS:
                tokens.append({"token": two, "attribute": MULTI_CHAR_OPS[two], "type": "Operador", "line": line, "col": col})
                i += 2
                continue

            # ---------------------------------------------------------- operadores un carácter
            if ch in SINGLE_CHAR_OPS:
                tokens.append({"token": ch, "attribute": SINGLE_CHAR_OPS[ch], "type": "Operador", "line": line, "col": col})
                i += 1
                continue

            # ---------------------------------------------------------- delimitadores
            if ch in DELIMITERS:
                tokens.append({"token": ch, "attribute": DELIMITERS[ch], "type": "Delimitador", "line": line, "col": col})
                i += 1
                continue

            # ---------------------------------------------------------- desconocido
            tokens.append({"token": ch, "attribute": -1, "type": "Error (Desconocido)", "line": line, "col": col})
            i += 1

        return tokens
