# src/analizador_lexico/lexer_plsql.py
import re

# Reutilizamos la definición de la clase Token.
class Token:
    def __init__(self, tipo, lexema, linea, columna, valor=None):
        self.tipo = tipo
        self.lexema = lexema
        self.linea = linea
        self.columna = columna
        self.valor = valor if valor is not None else lexema 

    def __repr__(self):
        lexema_display = self.lexema.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        valor_repr = repr(self.valor) if self.valor != self.lexema and self.valor is not None else ""
        return (f"Token({self.tipo}, '{lexema_display}', "
                f"L{self.linea}:C{self.columna}" +
                (f", V:{valor_repr}" if valor_repr else "") + ")")

# Tipos de Token para PL/SQL
TT_PALABRA_CLAVE_PLSQL = 'PALABRA_CLAVE_PLSQL'
TT_IDENTIFICADOR_PLSQL = 'IDENTIFICADOR_PLSQL'
TT_IDENTIFICADOR_ENTRECOMILLADO_PLSQL = 'IDENTIFICADOR_ENTRECOMILLADO_PLSQL'
TT_LITERAL_NUMERICO_PLSQL = 'LITERAL_NUMERICO_PLSQL' 
TT_LITERAL_CADENA_PLSQL = 'LITERAL_CADENA_PLSQL'   
TT_LITERAL_FECHA_PLSQL = 'LITERAL_FECHA_PLSQL'    
TT_LITERAL_BOOLEANO_PLSQL = 'LITERAL_BOOLEANO_PLSQL' 
TT_LITERAL_NULL_PLSQL = 'LITERAL_NULL_PLSQL'     
TT_OPERADOR_ARITMETICO_PLSQL = 'OPERADOR_ARITMETICO_PLSQL' 
TT_OPERADOR_ASIGNACION_PLSQL = 'OPERADOR_ASIGNACION_PLSQL' 
TT_OPERADOR_COMPARACION_PLSQL = 'OPERADOR_COMPARACION_PLSQL'
TT_OPERADOR_LOGICO_PLSQL = 'OPERADOR_LOGICO_PLSQL'      
TT_OPERADOR_CONCATENACION_PLSQL = 'OPERADOR_CONCATENACION_PLSQL' 
TT_OPERADOR_MIEMBRO_PLSQL = 'OPERADOR_MIEMBRO_PLSQL' # Para .
TT_OPERADOR_RANGO_PLSQL = 'OPERADOR_RANGO_PLSQL'   # Para ..
TT_ETIQUETA_PLSQL = 'ETIQUETA_PLSQL'               
TT_PARENTESIS_IZQ_PLSQL = 'PARENTESIS_IZQ_PLSQL' 
TT_PARENTESIS_DER_PLSQL = 'PARENTESIS_DER_PLSQL' 
TT_PUNTO_Y_COMA_PLSQL = 'PUNTO_Y_COMA_PLSQL'  
TT_COMA_PLSQL = 'COMA_PLSQL'                  
TT_DOS_PUNTOS_PLSQL = 'DOS_PUNTOS_PLSQL'       
TT_PORCENTAJE_PLSQL = 'PORCENTAJE_PLSQL'       
TT_ASTERISCO = 'ASTERISCO_PLSQL' 
TT_COMENTARIO_LINEA_PLSQL = 'COMENTARIO_LINEA_PLSQL'  
TT_COMENTARIO_BLOQUE_PLSQL = 'COMENTARIO_BLOQUE_PLSQL' 
TT_EOF_PLSQL = 'EOF_PLSQL'                   
TT_ERROR_PLSQL = 'ERROR_PLSQL'               
TT_WHITESPACE_PLSQL = 'WHITESPACE_PLSQL'       

PALABRAS_CLAVE_PLSQL = {
    'all', 'alter', 'and', 'any', 'array', 'as', 'asc', 'at', 'begin', 'between', 
    'binary_integer', 'body', 'boolean', 'bulk', 'by', 'case', 'char', 'check', 
    'close', 'cluster', 'collect', 'comment', 'commit', 'constant', 'create', 
    'current', 'cursor', 'date', 'day', 'declare', 'default', 'delete', 'desc', 
    'distinct', 'do', 'else', 'elsif', 'end', 'exception', 'execute', 'exists', 
    'exit', 'extends', 'fetch', 'float', 'for', 'forall', 'from', 
    'function', 'goto', 'group', 'having', 'hour', 'if', 'immediate', 'in', 
    'index', 'indicator', 'insert', 'integer', 'interface', 'intersect', 
    'interval', 'into', 'is', 'level', 'like', 'limited', 'loop', 'max', 
    'minus', 'minute', 'mlslabel', 'mod', 'month', 'natural', 'new', 'not', 
    'nowait', 'null', 'number', 'of', 'on', 'open', 'option', 'or', 'order', 
    'others', 'out', 'package', 'partition', 'pls_integer', 'positive', 
    'pragma', 'prior', 'private', 'procedure', 'public', 'raise', 'range', 
    'real', 'record', 'ref', 'release', 'return', 'reverse', 'rollback', 
    'row', 'rowid', 'rowlabel', 'rownum', 'rowtype', 'savepoint', 'schema', 
    'second', 'select', 'separate', 'set', 'share', 'smallint', 'space', 
    'sql', 'sqlcode', 'sqlerrm', 'start', 'statement', 'subtype', 'successful', 
    'sum', 'synonym', 'sysdate', 'table', 'then', 'time', 'timestamp', 'to', 
    'trigger', 'true', 'type', 'uid', 'union', 'unique', 'update', 'user', 
    'validate', 'values', 'varchar', 'varchar2', 'varying', 'view', 'when', 
    'where', 'while', 'with', 'work', 'write', 'year', 'zone'
}
LITERALES_PALABRA_CLAVE_PLSQL = {
    'true': TT_LITERAL_BOOLEANO_PLSQL,
    'false': TT_LITERAL_BOOLEANO_PLSQL,
    'null': TT_LITERAL_NULL_PLSQL
}
IDENTIFIER_LIKE_KEYWORDS_PLSQL = {'sqlcode', 'sqlerrm', 'sysdate', 'user', 'uid', 'rownum'}

ESPECIFICACIONES_TOKEN_PLSQL = [
    (r'--[^\n\r]*', TT_COMENTARIO_LINEA_PLSQL),
    (r'/\*[\s\S]*?\*/', TT_COMENTARIO_BLOQUE_PLSQL),
    (r"q'\[(.*?)\]'", TT_LITERAL_CADENA_PLSQL),
    (r"'(?:''|[^'])*'", TT_LITERAL_CADENA_PLSQL),
    (r"DATE\s*'(\d{4}-\d{2}-\d{2})'", TT_LITERAL_FECHA_PLSQL),
    
    # Operadores (de más largo/específico a más corto/general)
    # Colocar '..' antes de '.' y antes de números que puedan empezar con '.'
    (r'\.\.', TT_OPERADOR_RANGO_PLSQL),      
    (r'\|\|', TT_OPERADOR_CONCATENACION_PLSQL),
    (r':=', TT_OPERADOR_ASIGNACION_PLSQL),
    (r'\*\*|=>', TT_OPERADOR_ARITMETICO_PLSQL), 
    (r'<=|>=|!=|<>|\^=', TT_OPERADOR_COMPARACION_PLSQL),
    (r'=', TT_OPERADOR_COMPARACION_PLSQL), 
    (r'<', TT_OPERADOR_COMPARACION_PLSQL),
    (r'>', TT_OPERADOR_COMPARACION_PLSQL),
    
    # El asterisco para SELECT * o multiplicación
    (r'\*', TT_ASTERISCO),  
    
    # Otros operadores aritméticos de un solo carácter
    (r'[\+\-\/%]', TT_OPERADOR_ARITMETICO_PLSQL), 
    
    # Literales numéricos:
    # Primero los que tienen punto decimal, luego los que empiezan con punto, luego enteros.
    (r'\d+\.(?!\.)(?:\d*)(?:[eE][+-]?\d+)?', TT_LITERAL_NUMERICO_PLSQL),   # Decimal, pero no seguido de otro punto
    (r'\.\d+(?:[eE][+-]?\d+)?', TT_LITERAL_NUMERICO_PLSQL),   # Para .5, .3 etc.
    (r'\d+(?:[eE][+-]?\d+)?', TT_LITERAL_NUMERICO_PLSQL),     
    
    # Delimitadores y Puntuación
    (r'<<', TT_ETIQUETA_PLSQL),
    (r'>>', TT_ETIQUETA_PLSQL),
    (r'\(', TT_PARENTESIS_IZQ_PLSQL),
    (r'\)', TT_PARENTESIS_DER_PLSQL),
    (r';', TT_PUNTO_Y_COMA_PLSQL),
    (r',', TT_COMA_PLSQL),
    (r'\.', TT_OPERADOR_MIEMBRO_PLSQL), # Punto simple para acceso a miembros (debe ir DESPUÉS de .. y números como .5)
    (r':', TT_DOS_PUNTOS_PLSQL),
    (r'%', TT_PORCENTAJE_PLSQL),

    # Identificadores (deben ir después de palabras clave y operadores)
    (r'"([a-zA-Z_][a-zA-Z0-9_$#\s]*)"', TT_IDENTIFICADOR_ENTRECOMILLADO_PLSQL),
    # Solo letras, dígitos, _ y $ (NO #) para identificadores normales
    (r'[a-zA-Z_][a-zA-Z0-9_$]*', TT_IDENTIFICADOR_PLSQL),
    
    (r'\s+', TT_WHITESPACE_PLSQL), # Espacios en blanco al final para que no interfieran con otros patrones
]

class LexerPLSQL:
    def __init__(self, codigo_fuente):
        self.codigo = codigo_fuente
        self.posicion_actual = 0
        self.linea_actual = 1
        self.columna_actual = 1
        self.regex_compilado = []
        for patron, tipo in ESPECIFICACIONES_TOKEN_PLSQL:
            self.regex_compilado.append((re.compile(patron, re.IGNORECASE), tipo))

    def _avanzar(self, cantidad=1):
        for _ in range(cantidad):
            if self.posicion_actual < len(self.codigo):
                if self.codigo[self.posicion_actual] == '\n':
                    self.linea_actual += 1
                    self.columna_actual = 1
                else:
                    self.columna_actual += 1
                self.posicion_actual += 1
            else:
                break 

    def _procesar_identificador(self, lexema, linea, columna):
        lexema_lower = lexema.lower()
        if lexema_lower in LITERALES_PALABRA_CLAVE_PLSQL:
            tipo_token = LITERALES_PALABRA_CLAVE_PLSQL[lexema_lower]
            valor = None
            if lexema_lower == 'true': valor = True
            elif lexema_lower == 'false': valor = False
            return Token(tipo_token, lexema, linea, columna, valor)
        elif lexema_lower in PALABRAS_CLAVE_PLSQL:
            if lexema_lower in ['and', 'or', 'not']:
                return Token(TT_OPERADOR_LOGICO_PLSQL, lexema, linea, columna)
            # 'in' y 'is' son palabras clave, el parser determinará su rol (operador o parte de sintaxis)
            elif lexema_lower in ['like', 'between']: 
                return Token(TT_OPERADOR_COMPARACION_PLSQL, lexema, linea, columna)
            return Token(TT_PALABRA_CLAVE_PLSQL, lexema, linea, columna)
        return Token(TT_IDENTIFICADOR_PLSQL, lexema, linea, columna)

    def tokenizar(self):
        tokens = []
        while self.posicion_actual < len(self.codigo):
            match_encontrado_en_iteracion = False
            linea_inicio_token = self.linea_actual
            col_inicio_token = self.columna_actual

            for regex, tipo_token_base in self.regex_compilado:
                match = regex.match(self.codigo, self.posicion_actual)
                if match:
                    lexema = match.group(0)
                    match_encontrado_en_iteracion = True
                    
                    if tipo_token_base == TT_WHITESPACE_PLSQL or \
                       tipo_token_base == TT_COMENTARIO_LINEA_PLSQL or \
                       tipo_token_base == TT_COMENTARIO_BLOQUE_PLSQL:
                        self._avanzar(len(lexema))
                        break 

                    token_final = None
                    if tipo_token_base == TT_IDENTIFICADOR_PLSQL:
                        token_final = self._procesar_identificador(lexema, linea_inicio_token, col_inicio_token)
                    elif tipo_token_base == TT_IDENTIFICADOR_ENTRECOMILLADO_PLSQL:
                        valor_real = lexema[1:-1] 
                        token_final = Token(TT_IDENTIFICADOR_ENTRECOMILLADO_PLSQL, valor_real, linea_inicio_token, col_inicio_token, valor_real)
                    elif tipo_token_base == TT_LITERAL_CADENA_PLSQL:
                        valor_real = lexema[1:-1].replace("''", "'") 
                        if lexema.lower().startswith("q'["): 
                             valor_real = match.group(1) 
                        token_final = Token(TT_LITERAL_CADENA_PLSQL, lexema, linea_inicio_token, col_inicio_token, valor_real)
                    elif tipo_token_base == TT_LITERAL_FECHA_PLSQL:
                        valor_fecha = match.group(1) 
                        token_final = Token(TT_LITERAL_FECHA_PLSQL, lexema, linea_inicio_token, col_inicio_token, valor_fecha)
                    elif tipo_token_base == TT_LITERAL_NUMERICO_PLSQL:
                        try:
                            if '.' in lexema or 'e' in lexema.lower(): valor_num = float(lexema)
                            else: valor_num = int(lexema)
                            token_final = Token(TT_LITERAL_NUMERICO_PLSQL, lexema, linea_inicio_token, col_inicio_token, valor_num)
                        except ValueError:
                            token_final = Token(TT_ERROR_PLSQL, lexema, linea_inicio_token, col_inicio_token, "Número inválido")
                    else: 
                        token_final = Token(tipo_token_base, lexema, linea_inicio_token, col_inicio_token)
                    
                    if token_final:
                        tokens.append(token_final)
                    self._avanzar(len(lexema))
                    break 
            
            if not match_encontrado_en_iteracion and self.posicion_actual < len(self.codigo):
                caracter_erroneo = self.codigo[self.posicion_actual]
                tokens.append(Token(TT_ERROR_PLSQL, caracter_erroneo, linea_inicio_token, col_inicio_token,
                                    valor=f"Carácter no reconocido: '{caracter_erroneo}'"))
                self._avanzar() 

        tokens.append(Token(TT_EOF_PLSQL, "EOF", self.linea_actual, self.columna_actual))
        return tokens

if __name__ == "__main__":
    codigo = "1..3"
    lexer = LexerPLSQL(codigo)
    tokens = lexer.tokenizar()
    for t in tokens:
        print(t)

