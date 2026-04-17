---
description: Usar siempre que se modifiquen estilos, QSS o colores. Aplica el design system Paper and Ink. Prohibe estrictamente el modo oscuro, colores negros y dicta el uso exclusivo de la paleta Teal y Off-white.
---

# RULE: Restricciones de Diseño Visual (Paper & Ink)

Este proyecto simula una herramienta académica elegante, no un IDE hacker oscuro.

## Restricciones Absolutas de QSS:
- **NO MODO OSCURO:** Está prohibido usar `background-color: #000000`, `black`, o `darkgrey`.
- **Fondos (Surfaces):** Solo usa variaciones off-white: `#F5F5F0`, `#EEEEE8`, `#E8E8E2`.
- **Textos:** Principal `#1A1A1A`, Secundario `#5A5A5A`.
- **Acento (Primary):** Deep Teal `#006565`. Solo para botones de acción, tabs activos y borders de focus.
- **Errores:** Fondo rojo muy tenue `#FDECEA`, texto de error `#C0392B`.
- **Bordes:** No usar bordes sólidos para dividir paneles. Usa la diferencia de tonos `Surface` para crear jerarquía visual.