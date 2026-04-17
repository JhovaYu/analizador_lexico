---
description: Usar cuando se solicite desarrollar una nueva caracteristica completa. Fuerza el orden de implementacion core, gramatica, parser, semantica y finalmente UI. Evita empezar por la interfaz grafica
---

# WORKFLOW: Desarrollo de Feature Completa (Python/PyQt6)

## Regla de Oro: Core Primero, UI Después
Cuando se solicite una nueva característica (ej. "Añadir soporte para ciclo DO-WHILE"), NUNCA comiences modificando la interfaz gráfica.

## Secuencia de Ejecución Estricta:
1. **Definición de Tipos (`core/parse_tree_nodes.py`):** - Define las dataclasses necesarias para la nueva característica.
2. **Gramática (`core/grammar.py`):**
   - Actualiza la gramática EBNF.
3. **Adaptador/Parser (`core/parser.py`):**
   - Asegura la correcta traducción de `lark.Tree` a las dataclasses tipadas.
4. **Semántica (`core/semantic.py`):**
   - Añade el método en el patrón Visitor (ej. `visit_DoWhileNode`).
   - Implementa reglas de tabla de símbolos y chequeo de tipos.
5. **Pruebas Unitarias (Opcional pero recomendado):**
   - Verifica el pipeline sin UI.
6. **Integración UI (`ui/`):**
   - Conecta la lógica. Solo ahora puedes tocar PyQt6.