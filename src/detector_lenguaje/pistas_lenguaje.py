# src/detector_lenguaje/pistas_lenguaje.py
import re

LENGUAJES_SOPORTADOS = [
    "C++",
    "HTML",
    "JavaScript",
    "Pascal",
    "PL/SQL",
    "Python",
    "T-SQL"
]

# Pistas y sus pesos. Este diccionario es crucial y probablemente
# necesitará muchos ajustes y adiciones a medida que probemos.
# Formato de PISTA:
#   'expresion_regular_o_cadena': {
#       'NOMBRE_LENGUAJE_1': puntaje_si_coincide,
#       'NOMBRE_LENGUAJE_2': puntaje_si_coincide,
#       ...
#   }
# Los puntajes pueden ser positivos (aumentan la probabilidad) o negativos (la disminuyen).

PISTAS_LENGUAJE = {
    # HTML
    r'<!DOCTYPE\s+html>': {'HTML': 200},  # Pista muy fuerte
    r'<html\b': {'HTML': 70},
    r'<\w+\s*[^>]*>': {'HTML': 10},    # Cualquier etiqueta de apertura <tag ...>
    r'</\w+>': {'HTML': 10},           # Cualquier etiqueta de cierre </tag>
    r'<head\b': {'HTML': 50},
    r'<body\b': {'HTML': 50},
    r'<title\b': {'HTML': 40},
    r'<script\s*.*src\s*=\s*".*\.js"': {'HTML': 20, 'JavaScript': 10}, # Script JS externo en HTML
    r'<script\b[^>]*>': {'HTML': 15, 'JavaScript': 5}, # Etiqueta script (puede ser JS inline)

    # C++
    r'#include\s*<iostream>': {'C++': 90},
    r'#include\s*<vector>': {'C++': 70},
    r'#include\s*<string>': {'C++': 70},
    r'#include\s*<[a-zA-Z0-9_]+(\.h)?>': {'C++': 50}, # Include genérico
    r'using\s+namespace\s+std;': {'C++': 60},
    r'\b(int|void|char|double|float)\s+main\s*\(\s*(void)?\s*\)\s*\{': {'C++': 50}, # main()
    r'\bstd::cout': {'C++': 70},
    r'\bcout\s*<<': {'C++': 40},
    r'\bstd::cin': {'C++': 70},
    r'\bcin\s*>>': {'C++': 40},
    r'\bclass\s+\w+(\s*:\s*public\s+\w+)?\s*\{': {'C++': 40, 'JavaScript': 10}, # class MiClase {

    # JavaScript
    r'\bfunction\s+[a-zA-Z_]\w*\s*\([^)]*\)\s*\{': {'JavaScript': 70, 'Pascal': -20}, # function miFunc() {
    r'\bvar\s+[a-zA-Z_]\w*\s*=': {'JavaScript': 60, 'Pascal': -30}, # var x =
    r'\blet\s+[a-zA-Z_]\w*\s*=': {'JavaScript': 70},
    r'\bconst\s+[a-zA-Z_]\w*\s*=': {'JavaScript': 70},
    r'console\.log\s*\(': {'JavaScript': 80},
    r'document\.getElementById\s*\(': {'JavaScript': 70, 'HTML': 10},
    r'alert\s*\(': {'JavaScript': 60, 'HTML': 5},
    r'(async\s+function|=>\s*\{)': {'JavaScript': 50}, # Funciones async o arrow functions

    # Pascal
    r'\bprogram\s+[a-zA-Z_]\w*;': {'Pascal': 100}, # Pista muy fuerte
    r'\buses\s+[\w\s,]+;': {'Pascal': 70},
    r'\bbegin\b': {'Pascal': 40, 'PL/SQL': 20, 'T-SQL': 10}, # 'begin' es ambiguo, pero común en Pascal
    r'\bend;': {'Pascal': 30, 'PL/SQL': 50}, # 'end;'
    r'\bend\.': {'Pascal': 90},              # 'end.' es muy distintivo de Pascal
    r':=': {'Pascal': 60, 'PL/SQL': 60},     # Operador de asignación
    r'\bwriteln\s*\(': {'Pascal': 70},
    r'\breadln\s*\(': {'Pascal': 60},
    r'\brepeat\b': {'Pascal': 40},
    r'\buntil\b': {'Pascal': 40},
    r'\{[^}]*?\}': {'Pascal': 20},          # Comentarios estilo Pascal { }
    r'\(\*[\s\S]*?\*\)': {'Pascal': 20},    # Comentarios estilo Pascal (* *) ([\s\S] para multilínea)

    # PL/SQL
    r'\bDECLARE': {'PL/SQL': 70, 'T-SQL': 50},
    r'\bBEGIN': {'PL/SQL': 50, 'Pascal': 10, 'T-SQL': 20}, # BEGIN en mayúsculas, más común en SQL
    r'\bEXCEPTION': {'PL/SQL': 60},
    r'\bEND;': {'PL/SQL': 60, 'Pascal': 10}, # END; (con punto y coma)
    r'DBMS_OUTPUT\.PUT_LINE\s*\(': {'PL/SQL': 100}, # Pista muy fuerte
    r'SELECT\s+.*\s+INTO\s+.*FROM': {'PL/SQL': 70},
    r'CREATE\s+(OR\s+REPLACE\s+)?PROCEDURE': {'PL/SQL': 60, 'T-SQL': 40},
    r'CREATE\s+(OR\s+REPLACE\s+)?FUNCTION': {'PL/SQL': 60, 'T-SQL': 40},
    r'CREATE\s+(OR\s+REPLACE\s+)?PACKAGE': {'PL/SQL': 70},
    r'CREATE\s+(OR\s+REPLACE\s+)?TRIGGER': {'PL/SQL': 60, 'T-SQL': 30},
    r'V_(\w+)\s+(VARCHAR2|NUMBER|DATE|BOOLEAN)': {'PL/SQL': 50}, # Variables estilo v_nombre TIPO

    # T-SQL
    # DECLARE ya cubierto arriba, pero T-SQL usa @variables
    r'DECLARE\s+@\w+\s+(VARCHAR|NVARCHAR|INT|BIGINT|DATETIME|BIT|DECIMAL|NUMERIC)': {'T-SQL': 80},
    r'SET\s+@\w+\s*=': {'T-SQL': 70},
    r'PRINT\s+(\'|\"|@)': {'T-SQL': 80},
    r'\bGO\b': {'T-SQL': 70}, # Separador de lotes T-SQL
    r'CREATE\s+PROCEDURE\s+(AS\s+)?(BEGIN)?': {'T-SQL': 50, 'PL/SQL': 20}, # Menos OR REPLACE que PL/SQL
    r'CREATE\s+TABLE\s+\w+\s*\(': {'T-SQL': 40, 'PL/SQL': 30, 'SQL_GENERICO': 20},
    r'INSERT\s+INTO\s+\w+': {'T-SQL': 30, 'PL/SQL': 30, 'SQL_GENERICO': 20},
    r'UPDATE\s+\w+\s+SET': {'T-SQL': 30, 'PL/SQL': 30, 'SQL_GENERICO': 20},
    r'DELETE\s+FROM\s+\w+': {'T-SQL': 30, 'PL/SQL': 30, 'SQL_GENERICO': 20},
    r'SELECT\s+.*\s+FROM': {'T-SQL': 20, 'PL/SQL': 20, 'SQL_GENERICO': 10}, # SELECT es muy genérico
    r'IF\s+EXISTS\s*\(': {'T-SQL': 50},
    r'BEGIN\s+TRAN(SACTION)?': {'T-SQL': 40, 'PL/SQL': 10},
    r'--.*': {'T-SQL': 15, 'PL/SQL': 15, 'SQL_GENERICO': 10, 'Python': -5}, # Comentario SQL

    # Python
    r'\bdef\s+[a-zA-Z_]\w*\s*\(.*\)\s*:': {'Python': 100}, # def mi_funcion(): (Pista fuerte)
    r'\bprint\s*\([\s\S]*?\)': {'Python': 70, 'JavaScript': -10}, # print("algo") o print(f"algo")
    r'\bimport\s+[\w\.]+': {'Python': 60},
    r'\bfrom\s+[\w\.]+\s+import\s+[\w\*]+': {'Python': 60},
    r'\bclass\s+\w+\(.*\)\s*:': {'Python': 50},           # class MiClase(object):
    r'#.*': {'Python': 20, 'C++': -10, 'JavaScript': -10, 'Pascal': -20, 'PL/SQL': -20, 'T-SQL': -20, 'HTML': -20}, # Comentario Python es muy común
    r'^\s{4}\w+': {'Python': 10},                          # Indentación de 4 espacios al inicio de línea con contenido (pista débil pero suma)
    r'"""[\s\S]*?"""': {'Python': 30},                     # Docstrings multilínea con comillas dobles
    r"'''[\s\S]*?'''": {'Python': 30},                     # Docstrings multilínea con comillas simples
    r'\bif\s+__name__\s*==\s*("__main__"|\'__main__\'):': {'Python': 80}, # Bloque if __name__ == "__main__":

    # Pistas más generales o que pueden aplicar a varios (con menor peso o para desambiguar)
    # Punto y coma al final de la línea (no comentario)
    r';\s*(//.*|/\*.*\*/|#.*|--.*)?\s*$': {
        'C++': 10, 'JavaScript': 10, 'Pascal': 5, 'PL/SQL': 5, 'T-SQL': 5,
        'Python': -50, 'HTML': -30 # Muy improbable en Python o HTML
    },
    # Llaves para bloques
    r'\{[\s\S]*?\}': { # Bloque con contenido
        'C++': 10, 'JavaScript': 10,
        'Python': -40, 'Pascal': -30, 'HTML': -10
    },
    # Comentarios tipo C
    r'//.*': {'C++': 20, 'JavaScript': 20, 'Python': -20},
    r'/\*[\s\S]*?\*/': {'C++': 15, 'JavaScript': 15, 'PL/SQL': 10, 'T-SQL': 10, 'Pascal': -10, 'Python': -30}
}