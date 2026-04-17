---
description: jecutar antes de confirmar cambios grandes o al buscar bugs. Realiza una auditoria estricta de type hints, manejo de excepciones especificas y prevencion de mutaciones de estado en la UI.
---

# WORKFLOW: Auto-Code Review para IA

Antes de entregar código Python, verifica lo siguiente:

1. **Type Hints Obligatorios:** Toda función/método debe tener definidos sus tipos de entrada y salida `def function(arg: str) -> bool:`.
2. **Uso de Optionals:** Si algo puede ser nulo, usa `Optional[Type]` o `Type | None`.
3. **Manejo de Excepciones Quirúrgico:** Prohibido usar `except Exception as e:`. Captura excepciones específicas (`KeyError`, `lark.exceptions.UnexpectedInput`). Un error en el parser NO debe cerrar la aplicación de escritorio.
4. **Evitar Mutaciones Peligrosas:** Pasa copias profundas (`copy.deepcopy()`) de listas/diccionarios si los widgets de la UI los van a retener, para evitar bugs de estado compartido entre múltiples análisis.