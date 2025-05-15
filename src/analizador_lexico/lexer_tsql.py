# src/analizador_lexico/lexer_tsql.py
import re

# Reutilizamos la definición de la clase Token.
# En un proyecto más grande, esta clase estaría en un módulo común.
class Token:
    """
    Representa un token léxico con su tipo, lexema (texto),
    número de línea y columna donde aparece, y un valor opcional (ej. para números).
    """
    def __init__(self, tipo, lexema, linea, columna, valor=None):
        self.tipo = tipo          # Tipo de token (ej: PALABRA_CLAVE, IDENTIFICADOR)
        self.lexema = lexema      # El texto actual del token (ej: "CREATE", "nombre_tabla")
        self.linea = linea        # Número de línea donde aparece el token
        self.columna = columna    # Número de columna donde comienza el token
        # El valor real (ej: 123 para "123", o el contenido de una cadena sin comillas).
        # Si no se provee un valor, se usa el lexema.
        self.valor = valor if valor is not None else lexema 

    def __repr__(self):
        # Representación en cadena del token, útil para depuración.
        # Escapa saltos de línea y retornos de carro para una mejor visualización.
        lexema_display = self.lexema.replace('\n', '\\n').replace('\r', '\\r')
        # Usar repr() para el valor asegura que las cadenas se muestren con sus comillas, etc.
        valor_repr = repr(self.valor) if self.valor != self.lexema and self.valor is not None else ""
        
        return (f"Token({self.tipo}, '{lexema_display}', "
                f"L{self.linea}:C{self.columna}" +
                (f", V:{valor_repr}" if valor_repr else "") + ")")

# Tipos de Token para T-SQL / SQL
TT_PALABRA_CLAVE = 'PALABRA_CLAVE'
TT_IDENTIFICADOR = 'IDENTIFICADOR'
# TT_TIPO_DATO = 'TIPO_DATO' # Se tratarán como PALABRA_CLAVE por ahora

TT_LITERAL_CADENA = 'LITERAL_CADENA'
TT_LITERAL_NUMERICO = 'LITERAL_NUMERICO'
# TT_LITERAL_FECHA = 'LITERAL_FECHA' # Podría ser un tipo de cadena especial

TT_OPERADOR_COMPARACION = 'OPERADOR_COMPARACION'
TT_OPERADOR_ARITMETICO = 'OPERADOR_ARITMETICO'
# TT_OPERADOR_LOGICO = 'OPERADOR_LOGICO' # AND, OR, NOT son palabras clave
# TT_OPERADOR_ASIGNACION = 'OPERADOR_ASIGNACION' # = en SET

TT_PARENTESIS_IZQ = 'PARENTESIS_IZQ'
TT_PARENTESIS_DER = 'PARENTESIS_DER'
TT_COMA = 'COMA'
TT_PUNTO_Y_COMA = 'PUNTO_Y_COMA'
TT_PUNTO = 'PUNTO'
TT_ASTERISCO = 'ASTERISCO'

TT_COMENTARIO_LINEA = 'COMENTARIO_LINEA'
TT_COMENTARIO_BLOQUE = 'COMENTARIO_BLOQUE'

TT_EOF_SQL = 'EOF_SQL'
TT_ERROR_SQL = 'ERROR_SQL'
TT_WHITESPACE_SQL = 'WHITESPACE_SQL'

PALABRAS_CLAVE_SQL = {
    'create', 'table', 'insert', 'into', 'values', 'select', 'from', 'where',
    'update', 'set', 'delete', 'and', 'or', 'not', 'null', 'primary', 'key',
    'varchar', 'int', 'integer', 'decimal', 'numeric', 'datetime', 'char', 'text',
    'nvarchar', 'float', 'real', 'bit', 'date', 'time', 'money', 'smallint', 'tinyint',
    'alter', 'drop', 'add', 'constraint', 'foreign', 'references', 'default', 'unique', 'check',
    'index', 'view', 'database', 'schema', 'identity', 'on', 'off',
    'order', 'by', 'asc', 'desc', 'group', 'having', 'distinct', 'top', 'percent',
    'begin', 'end', 'if', 'else', 'while', 'declare', 'as', 'exec', 'execute',
    'procedure', 'function', 'trigger', 'go', 'union', 'all', 'exists', 'case', 'when', 'then',
    'join', 'inner', 'left', 'right', 'outer', 'full', 'is', 'like', 'between', 'nulls', 'first', 'last',
    'current_timestamp', 'getdate', 'print' # Ejemplos de funciones comunes
}

# Los tipos de dato SQL se incluyen en PALABRAS_CLAVE_SQL para simplificar.
# El parser determinará su rol contextual.

ESPECIFICACIONES_TOKEN_SQL = [
    # Comentarios (deben ir primero)
    (r'--[^\n\r]*', TT_COMENTARIO_LINEA),
    (r'/\*[\s\S]*?\*/', TT_COMENTARIO_BLOQUE),

    # Literales
    (r"'[^']*'(?:''[^']*')*", TT_LITERAL_CADENA),
    (r'[+-]?\d+\.\d*([eE][+-]?\d+)?', TT_LITERAL_NUMERICO), 
    (r'[+-]?\d+([eE][+-]?\d+)?', TT_LITERAL_NUMERICO),

    # Identificadores Delimitados (antes de operadores para evitar conflictos)
    (r'\[[^\]]+\]', TT_IDENTIFICADOR), 
    (r'"[^"]+"', TT_IDENTIFICADOR),   

    # Variables y objetos especiales de T-SQL (más específicos, antes de identificadores generales)
    (r'@@[a-zA-Z_][a-zA-Z0-9_]*', TT_IDENTIFICADOR),
    (r'@[a-zA-Z_][a-zA-Z0-9_]*', TT_IDENTIFICADOR),   
    (r'##[a-zA-Z_][a-zA-Z0-9_]*', TT_IDENTIFICADOR), 
    (r'#[a-zA-Z_][a-zA-Z0-9_]*', TT_IDENTIFICADOR),

    # Operadores y Delimitadores (el orden entre ellos puede importar)
    # El asterisco específico para SELECT * debe ir ANTES del operador aritmético general.
    (r'\*', TT_ASTERISCO), # Para SELECT *
    (r'<>|!=|>=|<=|=|<|>', TT_OPERADOR_COMPARACION),
    (r'[\+\-\*\/%]', TT_OPERADOR_ARITMETICO), # Quitamos '*' de aquí, ya que se maneja arriba
    
    (r'\(', TT_PARENTESIS_IZQ),
    (r'\)', TT_PARENTESIS_DER),
    (r',', TT_COMA),
    (r';', TT_PUNTO_Y_COMA),
    (r'\.', TT_PUNTO),
    
    # Identificadores estándar (palabras clave se reclasificarán después)
    (r'[a-zA-Z_][a-zA-Z0-9_]*', TT_IDENTIFICADOR),
    
    # Espacios en blanco (se consumen y se marcan para ser ignorados por el parser)
    (r'\s+', TT_WHITESPACE_SQL), 
]

class LexerTSQL:
    """
    Analizador Léxico para un subconjunto de T-SQL.
    Convierte una cadena de código T-SQL en una lista de tokens.
    """
    def __init__(self, codigo_fuente):
        """
        Inicializa el lexer con el código fuente a analizar.
        Args:
            codigo_fuente (str): El código T-SQL como una cadena.
        """
        self.codigo = codigo_fuente
        self.posicion_actual = 0 # Posición actual en la cadena de código
        self.linea_actual = 1    # Número de línea actual
        self.columna_actual = 1  # Columna actual en la línea (inicio del token)

    def _avanzar(self, cantidad=1):
        """
        Avanza la posición actual en el código fuente y actualiza
        los contadores de línea y columna.
        Args:
            cantidad (int): Número de caracteres a avanzar.
        """
        for _ in range(cantidad):
            if self.posicion_actual < len(self.codigo):
                caracter = self.codigo[self.posicion_actual]
                if caracter == '\n':
                    self.linea_actual += 1
                    self.columna_actual = 1 # Reiniciar columna al inicio de nueva línea
                else:
                    self.columna_actual += 1
                self.posicion_actual += 1
            else:
                break # No se puede avanzar más allá del final del código

    def tokenizar(self):
        tokens = []
        while self.posicion_actual < len(self.codigo):
            match_encontrado_en_iteracion = False
            linea_inicio_token = self.linea_actual
            col_inicio_token = self.columna_actual

            for patron_regex, tipo_token_base in ESPECIFICACIONES_TOKEN_SQL:
                match = re.match(patron_regex, self.codigo[self.posicion_actual:])
                if match:
                    lexema = match.group(0)
                    match_encontrado_en_iteracion = True
                    
                    if tipo_token_base == TT_WHITESPACE_SQL or \
                       tipo_token_base == TT_COMENTARIO_LINEA or \
                       tipo_token_base == TT_COMENTARIO_BLOQUE:
                        self._avanzar(len(lexema))
                        break 

                    tipo_token_final = tipo_token_base
                    valor_final = lexema 

                    if tipo_token_base == TT_IDENTIFICADOR:
                        # Reclasificar si es una palabra clave
                        if lexema.lower() in PALABRAS_CLAVE_SQL:
                            tipo_token_final = TT_PALABRA_CLAVE
                        # Extraer valor para identificadores delimitados
                        elif lexema.startswith('[') and lexema.endswith(']'):
                            valor_final = lexema[1:-1]
                        elif lexema.startswith('"') and lexema.endswith('"'):
                            valor_final = lexema[1:-1]
                        # Para variables como @nombre, el lexema es el valor
                    
                    elif tipo_token_base == TT_LITERAL_CADENA:
                        valor_final = lexema[1:-1].replace("''", "'")
                    
                    elif tipo_token_base == TT_LITERAL_NUMERICO:
                        if '.' in lexema or 'e' in lexema.lower():
                            try: valor_final = float(lexema)
                            except ValueError: valor_final = lexema 
                        else:
                            try: valor_final = int(lexema)
                            except ValueError: valor_final = lexema 
                    
                    tokens.append(Token(tipo_token_final, lexema, linea_inicio_token, col_inicio_token, valor_final))
                    self._avanzar(len(lexema))
                    break 
            
            if not match_encontrado_en_iteracion and self.posicion_actual < len(self.codigo):
                caracter_erroneo = self.codigo[self.posicion_actual]
                tokens.append(Token(TT_ERROR_SQL, caracter_erroneo, linea_inicio_token, col_inicio_token,
                                    valor=f"Carácter no reconocido: '{caracter_erroneo}'"))
                self._avanzar() 
        tokens.append(Token(TT_EOF_SQL, "EOF", self.linea_actual, self.columna_actual))
        return tokens

# (Fin de la clase LexerTSQL)
