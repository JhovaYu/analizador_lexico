---
description: Usar para crear o refactorizar la interfaz grafica en PyQt6. Impone limites de 300 lineas por archivo, separacion estricta de la logica de analisis y estructuracion modular mediante widgets y tabs
---

# WORKFLOW: Diseño y Modificación de UI en PyQt6

## Filosofía Anti-Monolito
Las aplicaciones Qt tienden al "Spaghetti de UI". Para evitarlo:

1. **Límites de Archivo:** Ningún archivo dentro de `ui/` debe superar las 300 líneas. Si lo hace, extráelo a un sub-widget.
2. **Separación de Responsabilidades:**
   - **NO** mezcles lógica de análisis (parsing/semántica) en los archivos `.py` de la UI.
   - La UI solo recibe estados (Dataclasses, listas de tokens) y emite señales (`pyqtSignal`).
3. **Estructura Interna de Clase:**
   Toda clase de UI debe seguir este orden de inicialización:
   - `def __init__(self):`
   - `self._init_ui()` -> Construye widgets hijos.
   - `self._setup_layout()` -> Organiza el QGridLayout / QVBoxLayout.
   - `self._apply_styles()` -> Aplica clases objectName para el QSS.
   - `self._connect_signals()` -> Conecta botones a funciones.