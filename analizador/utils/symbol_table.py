"""
symbol_table.py — Tabla de símbolos con soporte de scopes anidados.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Symbol:
    name: str
    type_: str
    line: int
    usages: List[int] = field(default_factory=list)

    @property
    def is_used(self) -> bool:
        return len(self.usages) > 0


class SymbolTable:
    def __init__(self) -> None:
        # Stack of scopes: cada scope es un dict name -> Symbol
        self._scopes: List[Dict[str, Symbol]] = [{}]

    # ------------------------------------------------------------------
    # Scope management
    # ------------------------------------------------------------------

    def enter_scope(self) -> None:
        self._scopes.append({})

    def exit_scope(self) -> None:
        if len(self._scopes) > 1:
            self._scopes.pop()

    # ------------------------------------------------------------------
    # Symbol operations
    # ------------------------------------------------------------------

    def define(self, name: str, type_: str, line: int) -> Symbol:
        """Registrar símbolo en el scope actual. Sobreescribe si ya existe."""
        sym = Symbol(name=name, type_=type_, line=line)
        self._scopes[-1][name] = sym
        return sym

    def lookup(self, name: str) -> Optional[Symbol]:
        """Buscar símbolo desde el scope más interno hacia el más externo."""
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        return None

    def mark_used(self, name: str, line: int) -> bool:
        """Marcar un símbolo como usado. Retorna True si fue encontrado."""
        sym = self.lookup(name)
        if sym:
            sym.usages.append(line)
            return True
        return False

    def unused_symbols(self) -> List[Symbol]:
        """Retorna todos los símbolos definidos pero nunca usados."""
        result: List[Symbol] = []
        for scope in self._scopes:
            for sym in scope.values():
                if not sym.is_used:
                    result.append(sym)
        return result

    def all_symbols(self) -> List[Symbol]:
        """Retorna todos los símbolos de todos los scopes."""
        result: List[Symbol] = []
        for scope in self._scopes:
            result.extend(scope.values())
        return result

    def current_scope_symbols(self) -> List[Symbol]:
        return list(self._scopes[-1].values())
