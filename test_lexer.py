from lexer import DFALexer

def test_lexer():
    lexer = DFALexer()
    
    test_cases = [
        ("IF cuenta = sueldo THEN", "Simple Assignment"),
        ("val := (5 * 4) + 10.5;", "Arithmetic & Float"),
        ("x = 10 # This is a comment", "Comment Handling"),
        ('msg = "Hola Mundo"', "String Literal"),
        ("error_test @", "Error Handling")
    ]
    
    for code, name in test_cases:
        print(f"\n--- Testing: {name} ---")
        print(f"Input: {code}")
        tokens = lexer.tokenize(code)
        for t in tokens:
            print(f"Token: {t['token']:<10} | Type: {t['type']:<20} | Attr: {t['attribute']}")

if __name__ == "__main__":
    test_lexer()
