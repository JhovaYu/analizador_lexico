"""
grammar.py — Gramática Lark EBNF para un subconjunto de Python.

FIX v3:
- Reemplazados %import common.NAME / NUMBER / ESCAPED_STRING por terminales
  regex propios, compatibles con Earley en lark 1.x.
- Eliminados NEWLINE / INDENT / DEDENT (consumidos por %ignore WS).
- Gramática whitespace-agnostic para máxima compatibilidad con el parser educativo.
"""

PYTHON_GRAMMAR = r"""
    start: statement+

    statement: funcdef
             | if_stmt
             | while_stmt
             | for_stmt
             | return_stmt
             | print_stmt
             | assign_stmt
             | expr_stmt

    // ---------------------------------------------------------- funcdef
    funcdef: "def" NAME "(" params? ")" ":" statement+

    params: NAME ("," NAME)*

    // ---------------------------------------------------------- if / elif / else
    if_stmt: "if" expr ":" statement+ elif_clause* else_clause?

    elif_clause: "elif" expr ":" statement+

    else_clause: "else" ":" statement+

    // ---------------------------------------------------------- while
    while_stmt: "while" expr ":" statement+

    // ---------------------------------------------------------- for
    for_stmt: "for" NAME "in" "range" "(" range_args ")" ":" statement+

    range_args: expr ("," expr)*

    // ---------------------------------------------------------- simple statements
    assign_stmt: NAME "=" expr ";"?

    return_stmt: "return" expr? ";"?

    print_stmt: "print" "(" arglist? ")" ";"?

    expr_stmt: expr ";"?

    arglist: expr ("," expr)*

    // ---------------------------------------------------------- expressions (precedencia ascendente con alias)
    ?expr: or_expr

    ?or_expr: and_expr
            | or_expr "or" and_expr -> binary_or

    ?and_expr: not_expr
             | and_expr "and" not_expr -> binary_and

    ?not_expr: comparison
             | "not" not_expr -> unary_not

    ?comparison: arith
               | comparison COMP_OP arith -> binary_cmp

    ?arith: term
          | arith "+" term -> binary_add
          | arith "-" term -> binary_sub

    ?term: factor
         | term "*"  factor -> binary_mul
         | term "/"  factor -> binary_div
         | term "//" factor -> binary_floordiv
         | term "%"  factor -> binary_mod

    ?factor: "+" factor -> unary_plus
           | "-" factor -> unary_minus
           | power

    ?power: atom
          | atom "**" factor -> binary_pow

    ?atom: FLOAT_NUM       -> float_lit
         | INT_NUM         -> int_lit
         | STRING_DQ       -> str_lit
         | STRING_SQ       -> str_lit
         | "True"          -> bool_true
         | "False"         -> bool_false
         | NAME "(" arglist? ")" -> func_call
         | NAME            -> name_ref
         | "(" expr ")"

    // ---------------------------------------------------------- terminals (definidos manualmente para Earley)
    COMP_OP: "==" | "!=" | "<=" | ">=" | "<" | ">"

    FLOAT_NUM: /\d+\.\d+([eE][+-]?\d+)?/
    INT_NUM:   /\d+/
    NAME:      /[a-zA-Z_][a-zA-Z0-9_]*/
    STRING_DQ: /\"[^\"\\n]*\"/
    STRING_SQ: /\'[^\'\\n]*\'/

    COMMENT: /#[^\n]*/
    WS:      /\s+/

    %ignore WS
    %ignore COMMENT
"""
