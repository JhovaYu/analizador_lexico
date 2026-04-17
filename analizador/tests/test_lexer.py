"""
tests/test_lexer.py — Pruebas del DFA léxico refactorizado.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from core.lexer import DFALexer


@pytest.fixture
def lexer():
    return DFALexer()


def test_keyword_if(lexer):
    tokens = lexer.tokenize("if")
    assert tokens[0]["type"] == "Palabra Reservada"
    assert tokens[0]["attribute"] == 21


def test_identifier(lexer):
    tokens = lexer.tokenize("cuenta")
    assert tokens[0]["type"] == "Identificador"
    assert tokens[0]["attribute"] == 1


def test_integer(lexer):
    tokens = lexer.tokenize("42")
    assert tokens[0]["type"] == "Número Entero"
    assert tokens[0]["attribute"] == 2


def test_float(lexer):
    tokens = lexer.tokenize("3.14")
    assert tokens[0]["type"] == "Número Real"
    assert tokens[0]["attribute"] == 3


def test_operators(lexer):
    tokens = lexer.tokenize(":=")
    assert tokens[0]["token"] == ":="
    assert tokens[0]["attribute"] == 106


def test_comment_ignored(lexer):
    tokens = lexer.tokenize("x = 1 # comentario")
    assert all(t["type"] != "Comentario" for t in tokens)


def test_string(lexer):
    tokens = lexer.tokenize('"hola mundo"')
    assert tokens[0]["type"] == "Cadena"


def test_unknown(lexer):
    tokens = lexer.tokenize("@")
    assert tokens[0]["attribute"] == -1
    assert "Error" in tokens[0]["type"]


def test_full_expression(lexer):
    # Usar palabras reservadas del subconjunto Python (minúsculas)
    tokens = lexer.tokenize("if cuenta == sueldo:")
    types = [t["type"] for t in tokens]
    assert "Palabra Reservada" in types
    assert "Identificador" in types
    assert "Operador" in types


def test_whitespace_ignored(lexer):
    tokens = lexer.tokenize("   x   =   1   ")
    assert len(tokens) == 3  # x, =, 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
