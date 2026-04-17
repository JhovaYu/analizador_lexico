# Prompt Maestro — Jarvis: Analizador Léxico, Sintáctico y Semántico con AST

## Contexto del proyecto

Estás construyendo un analizador de código completo en Python para un subconjunto del lenguaje Python. La aplicación tiene cuatro fases de análisis: léxica, sintáctica, semántica, y visualización del AST. La interfaz es una aplicación de escritorio estilo IDE.

El repositorio base existe en: https://github.com/JhovaYu/analizador_lexico.git
Contiene un `lexer.py` con un DFA funcional y un `gui_app.py` con CustomTkinter. Ambos serán reemplazados o refactorizados en este nuevo proyecto.

---

## Stack técnico — no negociable

- **Lenguaje:** Python 3.11+
- **UI Framework:** PyQt6 (reemplaza CustomTkinter)
- **Parser:** lark-parser con `parser="earley"`, `propagate_positions=True`, `ambiguity="resolve"`
- **Grafo AST:** PyQt6 `QGraphicsView` + `QGraphicsScene` para render interactivo (zoom, pan, colapso de nodos)
- **Dependencias adicionales:** `networkx` para el layout del grafo (algoritmo Reingold-Tilford / dot layout)

---

## Arquitectura de archivos

```
analizador/
├── core/
│   ├── lexer.py          # DFA refactorizado del repo original
│   ├── grammar.py        # Gramática Lark EBNF (ver contrato abajo)
│   ├── parser.py         # Puente: árbol Lark → nodos ASTNode
│   ├── semantic.py       # Visitor semántico: tabla de símbolos + type checking
│   └── ast_nodes.py      # Definición de nodos AST (ver contrato abajo)
├── utils/
│   ├── error_handler.py  # Errores unificados con fase, línea y columna
│   └── symbol_table.py   # Tabla hash con soporte de scopes anidados
├── ui/
│   ├── app.py            # Ventana principal PyQt6
│   ├── editor_panel.py   # Panel editor de código con syntax highlighting
│   ├── token_table.py    # Widget tabla de tokens con columnas Token/Atributo/Tipo/Línea
│   ├── ast_graph.py      # Widget QGraphicsView para el grafo AST interactivo
│   └── style.qss         # Stylesheet QSS con el design system completo
├── tests/
│   ├── test_lexer.py
│   ├── test_parser.py
│   └── test_semantic.py
├── requirements.txt
└── main.py
```

---

## Contrato: ast_nodes.py

Implementar exactamente estos nodos, cada uno hereda de `ASTNode`:

**ASTNode (base):**
- Campos: `line: int`, `col: int`
- Métodos: `accept(visitor)` usando patrón Visitor con dispatch a `visit_<ClassName>`, `children() -> List[ASTNode]`, `label() -> str` (texto corto para el nodo del grafo)

**Statements:** `Program`, `FunctionDef`, `AssignStatement`, `IfStatement`, `WhileStatement`, `ForStatement`, `ReturnStatement`, `PrintStatement`, `ExprStatement`

**Expresiones:** `BinaryOp`, `UnaryOp`, `FunctionCall`, `Identifier`

**Literales:** `IntLiteral`, `FloatLiteral`, `StringLiteral`, `BoolLiteral`

**ASTVisitor (base):** método `generic_visit(node)` que recorre hijos sin hacer nada. Subclasificar para semántico.

Todos los nodos usan `@dataclass` de Python. Los campos hijos son `Optional[ASTNode]` o `List[ASTNode]` con `field(default_factory=list)`.

---

## Contrato: grammar.py

Gramática Lark EBNF. Reglas principales:

```
start → statement+
statement → funcdef | if_stmt | while_stmt | for_stmt | return_stmt | assign_stmt | print_stmt | expr_stmt
funcdef → "def" NAME "(" params? ")" ":" NEWLINE INDENT statement+ DEDENT
if_stmt → "if" expr ":" suite elif_clause* else_clause?
while_stmt → "while" expr ":" suite
for_stmt → "for" NAME "in" "range" "(" range_args ")" ":" suite
assign_stmt → NAME "=" expr
return_stmt → "return" expr?
print_stmt → "print" "(" arglist? ")"
```

Expresiones con precedencia ascendente: `or → and → not → comparison → arith → term → factor → power → atom`

Operadores aritméticos: `+ - * / // % **`
Operadores de comparación: `== != < > <= >=`
Literales: `INT`, `FLOAT`, `STRING` (comillas simples y dobles), `True`, `False`
Comentarios `#` ignorados. Whitespace ignorado. `propagate_positions=True`.

---

## Contrato: parser.py

Clase `ASTBuilder(Transformer)` que hereda de `lark.Transformer`.

Cada método del Transformer corresponde a una regla de la gramática y retorna el `ASTNode` correspondiente. Extraer `line` y `col` de `meta.line` y `meta.column` de Lark cuando `propagate_positions=True`.

Exponer función pública: `def parse(source: str) -> Program` que instancia el parser Lark, ejecuta `parse()`, aplica el Transformer y retorna el nodo raíz `Program`.

Manejo de errores: capturar `lark.exceptions.UnexpectedInput` y `lark.exceptions.UnexpectedEOF`, convertirlos a `SyntaxError` personalizado con mensaje en español, línea y columna.

---

## Contrato: semantic.py

Clase `SemanticAnalyzer(ASTVisitor)`.

**Tabla de símbolos:** implementar como stack de diccionarios para manejar scopes. `enter_scope()` / `exit_scope()`. Cada símbolo almacena: nombre, tipo inferido, línea de declaración, línea(s) de uso.

**Verificaciones requeridas:**
1. Variable usada antes de ser declarada → error semántico
2. Variable declarada pero nunca usada → warning
3. Función llamada con número incorrecto de argumentos → error semántico
4. Función llamada antes de ser definida → error semántico
5. Tipo incompatible en operación binaria (int + str) → error semántico cuando sea inferible

**Retornar:** lista de `SemanticError` y `SemanticWarning`, cada uno con `message`, `line`, `col`, `severity`.

---

## Contrato: error_handler.py

Clase `AnalysisError` con campos: `phase` (LEXER/PARSER/SEMANTIC), `message`, `line`, `col`, `severity` (ERROR/WARNING).

Clase `ErrorHandler` con método `collect(errors: List[AnalysisError])` y `report() -> str` que formatea todos los errores ordenados por línea.

---

## Contrato: symbol_table.py

Clase `SymbolTable` con:
- `define(name, type_, line)` — registra símbolo en scope actual
- `lookup(name) -> Symbol | None` — busca en scope actual y padres
- `enter_scope()` / `exit_scope()`
- `unused_symbols() -> List[Symbol]` — retorna símbolos definidos pero no usados

---

## Lenguaje soportado (subconjunto de Python)

El analizador debe procesar correctamente este código de ejemplo sin errores:

```python
def factorial(n):
    if n <= 1:
        return 1
    else:
        return n * factorial(n - 1)

def suma_rango(inicio, fin):
    total = 0
    for i in range(inicio, fin):
        total = total + i
    return total

x = 10
resultado = factorial(x)
print(resultado)

contador = 0
while contador < 5:
    contador = contador + 1

print(suma_rango(1, 100))
```

Este código debe generar:
- Tokens léxicos correctos para todas las palabras reservadas, identificadores, operadores y literales
- AST con nodos `Program > [FunctionDef(factorial), FunctionDef(suma_rango), AssignStatement, AssignStatement, PrintStatement, AssignStatement, WhileStatement, PrintStatement]`
- Sin errores semánticos
- Tabla de símbolos con: factorial, suma_rango, n, x, resultado, total, i, contador, inicio, fin

---

## Design system — UI (QSS)

Paleta "Paper and Ink" con Deep Teal. Implementar en `style.qss`:

```
Surface base:        #F5F5F0   (off-white, fondo principal)
Surface container:   #EEEEE8   (paneles secundarios)
Surface low:         #E8E8E2   (editor gutter, tabs inactivos)
Surface high:        #DDDDD6   (elementos deprimidos)
Primary (Deep Teal): #006565
Primary hover:       #004F4F
Primary text:        #FFFFFF
Text primary:        #1A1A1A
Text secondary:      #5A5A5A
Text muted:          #8A8A8A
Error:               #C0392B
Error surface:       #FDECEA
Warning:             #E67E22
Warning surface:     #FEF9E7
Success:             #27AE60
```

Fuentes: Inter para UI chrome (Fontshare o Google Fonts), Fira Code para editor y valores de tokens.

**Regla de bordes:** No usar `border: 1px solid` para separar paneles. Usar diferencia de `background-color` entre superficies. Bordes solo para inputs en estado focus (`border-bottom: 2px solid #006565`).

**Sombras:** Tint teal en sombras: `box-shadow: 0 12px 40px rgba(0, 101, 101, 0.06)` para elementos flotantes.

---

## Layout de la ventana principal

```
┌─────────────────────────────────────────────────────────────┐
│  [SVG Logo]  Analizador v2.0     [Run ▶]  [Clear]  [Export] │  48px topbar
├───────────────────────┬─────────────────────────────────────┤
│                       │  [Léxico] [Sintáctico] [Semántico]  │
│  Editor de código     │─────────────────────────────────────│
│  - Números de línea   │  Tabla scrollable con columnas:     │
│  - Fira Code 13px     │  Token | Atributo | Tipo | Línea    │
│  - Line highlight     │                                     │
│  - 60% del ancho      │  40% del ancho                      │
│                       │                                     │
├───────────────────────┴─────────────────────────────────────┤
│  [drag handle ══════════════════════════════════════════]   │
│  Panel AST — QGraphicsView                                  │
│  Nodos circulares con label(), aristas con curvas suaves    │
│  Controles: [+] [-] [Reset] en esquina inferior derecha     │
│  Default: 35% de la altura total. Resizable.                │
└─────────────────────────────────────────────────────────────┘
```

---

## Widget: ast_graph.py

Clase `ASTGraphWidget(QGraphicsView)`:

- Recibe un nodo raíz `ASTNode` y construye el grafo con `networkx` usando layout jerárquico (Graphviz `dot` o `networkx` spring con dirección top-down)
- Cada nodo del grafo es un `QGraphicsEllipseItem` con texto del `label()` del nodo
- Aristas son `QGraphicsPathItem` con curvas Bezier suaves
- **Colores por tipo de nodo:**
  - Statements: Deep Teal `#006565`, texto blanco
  - Expresiones: Teal claro `#E0F2F2`, texto oscuro
  - Literales: Surface `#EEEEE8`, borde teal, texto oscuro
  - Error nodes: `#FDECEA`, borde rojo
- **Interactividad:**
  - Zoom: `Ctrl+scroll` o botones `[+][-]`
  - Pan: click y arrastrar en espacio vacío
  - Selección de nodo: click → highlight con borde teal brillante `#00A0A0` + sombra
  - Hover: escala el nodo a 1.05x con transición suave
  - Doble click en nodo: colapsa/expande sus hijos

---

## Widget: token_table.py

Clase `TokenTableWidget(QTableWidget)`:

- 4 columnas: Token, Atributo, Tipo, Línea
- Columna Tipo con chips de color: Palabra Reservada (teal), Identificador (gris), Número (azul), Operador (naranja), Error (rojo)
- Filas con error (`attribute == -1`): background `#FDECEA`
- Row hover: background `#E0F2F2`
- Header fijo (sticky)
- Ordenable por cualquier columna
- Animación de entrada: las filas aparecen con fade-in secuencial al cargar (50ms de delay entre filas, máximo 20 filas animadas)

---

## Widget: editor_panel.py

Clase `CodeEditorWidget(QPlainTextEdit)`:

- Syntax highlighting con `QSyntaxHighlighter`:
  - Keywords (`def`, `if`, `elif`, `else`, `while`, `for`, `in`, `return`, `print`, `and`, `or`, `not`, `True`, `False`): color `#006565` bold
  - Strings: `#8B4823`
  - Números: `#1E6BB8`
  - Comentarios: `#8A8A8A` italic
  - Operadores: `#C0392B`
- Gutter (números de línea): background `#E8E8E2`, texto `#8A8A8A`
- Línea activa highlight: background `rgba(0, 101, 101, 0.06)`
- Fuente: Fira Code 13px
- Tab size: 4 espacios

---

## Tabs del panel derecho

Tres tabs: Léxico, Sintáctico, Semántico.

- Tab activo: texto `#006565`, borde inferior animado 2px teal (transición 200ms)
- Tab inactivo: texto `#5A5A5A`, background `#E8E8E2`
- Tab "Sintáctico": muestra árbol de derivación textual (representación indentada del AST como alternativa al grafo cuando este panel está activo)
- Tab "Semántico": muestra tabla de símbolos (Nombre | Tipo | Línea declaración | Usos) + lista de errores y warnings semánticos con sus líneas
- Si hay errores en una fase, mostrar badge contador rojo en el tab correspondiente

---

## Topbar

- Logo SVG inline: letra "A" con un nodo de grafo integrado, color `#006565`
- Botón "Analizar" (`[▶ Analizar]`): background `#006565`, texto blanco, corners `border-radius: 4px`, hover `#004F4F`, transición 180ms. Icono: triángulo de play (Lucide `Play`)
- Botón "Limpiar": ghost, texto `#5A5A5A`, hover background `#EEEEE8`
- Botón "Exportar": icono `Download` (Lucide), ghost, tooltip "Exportar tokens como CSV"
- Al hacer click en Analizar: el botón muestra estado de carga (icono spinner girando, texto "Analizando...") durante el procesamiento, luego vuelve al estado normal

---

## Flujo de análisis al presionar Analizar

```
1. Leer texto del CodeEditorWidget
2. lexer.tokenize(source) → Lista de tokens
3. Poblar TokenTableWidget con los tokens (tab Léxico)
4. parser.parse(source) → ASTNode raíz
5. Poblar representación textual en tab Sintáctico
6. SemanticAnalyzer().analyze(ast_root) → errores + tabla de símbolos
7. Poblar tab Semántico con tabla de símbolos y errores
8. ASTGraphWidget.render(ast_root) → grafo interactivo
9. Si hay errores en cualquier fase: mostrar badge en el tab correspondiente
10. Si hay errores críticos (léxicos/sintácticos): continuar hasta donde sea posible, no detener todo el flujo
```

---

## requirements.txt

```
PyQt6>=6.6.0
lark>=1.1.9
networkx>=3.2
```

---

## Orden de implementación (fases)

**Fase 1 — Core sin UI:**
Implementar y testear en este orden: `ast_nodes.py` → `grammar.py` → `parser.py` → `semantic.py` → `error_handler.py` → `symbol_table.py`. Verificar con el código de ejemplo del contrato antes de tocar la UI.

**Fase 2 — UI base:**
`style.qss` → `app.py` (ventana con layout) → `editor_panel.py` → `token_table.py` → conectar lexer existente a la UI.

**Fase 3 — Integración:**
Conectar parser y semántico a la UI. Implementar tabs Sintáctico y Semántico.

**Fase 4 — Grafo AST:**
`ast_graph.py` con QGraphicsView, nodos interactivos, zoom/pan/colapso.

**Fase 5 — Polish:**
Animaciones de tabs, fade-in de tabla, estado de carga del botón Analizar, export CSV.

---

## Restricciones absolutas

- No usar CustomTkinter en ningún archivo nuevo
- No usar matplotlib para el grafo AST
- No mezclar lógica de análisis en los widgets de UI — toda lógica va en `core/`
- Todo el texto de la UI en español
- Manejo de excepciones en cada fase del análisis — un error en el parser no debe crashear la aplicación
- Ningún widget muestra "None" o stack traces al usuario — los errores se muestran formateados en el panel Semántico o en un status bar

