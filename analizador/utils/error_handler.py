"""
error_handler.py — Errores unificados con fase, línea y columna.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List


class Phase(str, Enum):
    LEXER = "LÉXICO"
    PARSER = "SINTÁCTICO"
    SEMANTIC = "SEMÁNTICO"


class Severity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass
class AnalysisError:
    phase: Phase
    message: str
    line: int
    col: int
    severity: Severity = Severity.ERROR

    def __str__(self) -> str:
        return (
            f"[{self.severity.value}] {self.phase.value} "
            f"(línea {self.line}, col {self.col}): {self.message}"
        )


class ErrorHandler:
    def __init__(self) -> None:
        self._errors: List[AnalysisError] = []

    def collect(self, errors: List[AnalysisError]) -> None:
        self._errors.extend(errors)

    def add(self, error: AnalysisError) -> None:
        self._errors.append(error)

    def clear(self) -> None:
        self._errors.clear()

    @property
    def errors(self) -> List[AnalysisError]:
        return [e for e in self._errors if e.severity == Severity.ERROR]

    @property
    def warnings(self) -> List[AnalysisError]:
        return [e for e in self._errors if e.severity == Severity.WARNING]

    @property
    def all_errors(self) -> List[AnalysisError]:
        return list(self._errors)

    def has_errors(self) -> bool:
        return any(e.severity == Severity.ERROR for e in self._errors)

    def report(self) -> str:
        if not self._errors:
            return "✓ Sin errores."
        sorted_errors = sorted(self._errors, key=lambda e: (e.line, e.col))
        return "\n".join(str(e) for e in sorted_errors)
