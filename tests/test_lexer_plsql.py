import unittest
from src.analizador_lexico.lexer_plsql import LexerPLSQL, TT_LITERAL_NUMERICO_PLSQL, TT_OPERADOR_RANGO_PLSQL, TT_EOF_PLSQL

class TestLexerPLSQL(unittest.TestCase):
    def test_rango_for(self):
        codigo = "1..3"
        lexer = LexerPLSQL(codigo)
        tokens = lexer.tokenizar()
        tipos = [t.tipo for t in tokens]
        lexemas = [t.lexema for t in tokens]
        # Esperamos: 1 (numérico), .. (rango), 3 (numérico), EOF
        self.assertEqual(tipos[:4], [TT_LITERAL_NUMERICO_PLSQL, TT_OPERADOR_RANGO_PLSQL, TT_LITERAL_NUMERICO_PLSQL, TT_EOF_PLSQL])
        self.assertEqual(lexemas[:4], ["1", "..", "3", "EOF"])

if __name__ == "__main__":
    unittest.main()
