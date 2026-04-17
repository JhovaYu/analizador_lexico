import string

class DFALexer:
    def __init__(self):
        self.KEYWORDS = {
            'IF': 20, 'THEN': 21, 'ELSE': 22, 'WHILE': 23, 'DO': 24,
            'INT': 25, 'FLOAT': 26, 'PRINT': 27, 'RETURN': 28
        }
        self.OPERATORS = {
            '+': 30, '-': 31, '*': 32, '/': 33, '^': 34,
            '=': 35, '<': 36, '>': 37, ':=': 38,
            '<=': 39, '>=': 40
        }
        self.DELIMITERS = {
            ';': 50, ',': 51, '(': 52, ')': 53, '{': 54, '}': 55
        }
        
    def is_digit(self, char):
        return char.isdigit()
        
    def is_alpha(self, char):
        return char.isalpha() or char == '_'
        
    def is_space(self, char):
        return char.isspace()
    
    def tokenize(self, input_string):
        tokens = []
        i = 0
        n = len(input_string)
        line = 1
        
        while i < n:
            char = input_string[i]
            
            # Skip whitespace
            if self.is_space(char):
                if char == '\n':
                    line += 1
                i += 1
                continue
                
            # Comments (Skip until newline)
            if char == '#':
                while i < n and input_string[i] != '\n':
                    i += 1
                continue
                
            # String Literals (Double Quotes)
            if char == '"':
                lexeme = char
                i += 1
                while i < n and input_string[i] != '"':
                    lexeme += input_string[i]
                    i += 1
                
                if i < n and input_string[i] == '"':
                    lexeme += '"'
                    i += 1
                    tokens.append({'token': lexeme, 'attribute': 4, 'type': 'Cadena de Caracteres', 'line': line})
                else:
                    # Unterminated string
                    tokens.append({'token': lexeme, 'attribute': -1, 'type': 'Error (Cadena sin cerrar)', 'line': line})
                continue
                
            # Identifier or Keyword
            if self.is_alpha(char):
                lexeme = char
                i += 1
                while i < n and (self.is_alpha(input_string[i]) or self.is_digit(input_string[i])):
                    lexeme += input_string[i]
                    i += 1
                
                # Check if Keyword
                if lexeme.upper() in self.KEYWORDS:
                    tokens.append({'token': lexeme, 'attribute': self.KEYWORDS[lexeme.upper()], 'type': 'Palabra Reservada', 'line': line})
                else:
                    tokens.append({'token': lexeme, 'attribute': 1, 'type': 'Identificador', 'line': line})
                continue
                
            # Numbers (Integer or Float)
            if self.is_digit(char):
                lexeme = char
                i += 1
                
                # Integer part
                while i < n and self.is_digit(input_string[i]):
                    lexeme += input_string[i]
                    i += 1
                
                # Float part?
                if i < n and input_string[i] == '.':
                    lexeme += '.'
                    i += 1
                    # Require at least one digit after dot
                    if i < n and self.is_digit(input_string[i]):
                        while i < n and self.is_digit(input_string[i]):
                            lexeme += input_string[i]
                            i += 1
                        tokens.append({'token': lexeme, 'attribute': 2, 'type': 'Número Real', 'line': line})
                    else:
                        # Error: Trailing dot
                        tokens.append({'token': lexeme, 'attribute': -1, 'type': 'Error (Número inválido)', 'line': line})
                else:
                    tokens.append({'token': lexeme, 'attribute': 3, 'type': 'Número Entero', 'line': line})
                continue
                
            # Operators (Multi-char check first)
            if i + 1 < n and (char + input_string[i+1]) in self.OPERATORS:
                lexeme = char + input_string[i+1]
                tokens.append({'token': lexeme, 'attribute': self.OPERATORS[lexeme], 'type': 'Operador', 'line': line})
                i += 2
                continue
                
            if char in self.OPERATORS:
                tokens.append({'token': char, 'attribute': self.OPERATORS[char], 'type': 'Operador', 'line': line})
                i += 1
                continue
                
            # Delimiters
            if char in self.DELIMITERS:
                tokens.append({'token': char, 'attribute': self.DELIMITERS[char], 'type': 'Delimitador', 'line': line})
                i += 1
                continue
            
            # Unknown character
            tokens.append({'token': char, 'attribute': -1, 'type': 'Error (Desconocido)', 'line': line})
            i += 1
            
        return tokens
