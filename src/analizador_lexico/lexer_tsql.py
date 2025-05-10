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
        self.valor = valor if valor is not None else lexema # Valor real (ej: 123 para "123")

    def __repr__(self):
        # Representación en cadena del token, útil para depuración.
        # Escapa saltos de línea y retornos de carro para una mejor visualización.
        lexema_display = self.lexema.replace('\n', '\\n').replace('\r', '\\r')
        valor_display = str(self.valor).replace('\n', '\\n').replace('\r', '\\r')
        return (f"Token({self.tipo}, '{lexema_display}', "
                f"L{self.linea}:C{self.columna}" +
                (f", V:{repr(valor_display)}" if self.valor != self.lexema and self.valor is not None else "") + ")")

# Tipos de Token para T-SQL / SQL
TT_PALABRA_CLAVE = 'PALABRA_CLAVE'  # CREATE, TABLE, SELECT, INSERT, UPDATE, DELETE, FROM, WHERE, SET, VALUES, INTO, etc.
TT_IDENTIFICADOR = 'IDENTIFICADOR'  # Nombres de tablas, columnas, etc.
TT_TIPO_DATO = 'TIPO_DATO'          # VARCHAR, INT, DECIMAL, DATETIME, etc. (Podrían ser también PALABRA_CLAVE)

TT_LITERAL_CADENA = 'LITERAL_CADENA' # 'esto es una cadena'
TT_LITERAL_NUMERICO = 'LITERAL_NUMERICO' # 123, 45.67
TT_LITERAL_FECHA = 'LITERAL_FECHA'   # Podría ser un tipo de cadena especial, ej: '2025-05-10'

TT_OPERADOR_COMPARACION = 'OPERADOR_COMPARACION' # =, <, >, <=, >=, <>, !=
TT_OPERADOR_ARITMETICO = 'OPERADOR_ARITMETICO' # +, -, *, / (menos común en DDL/DML básico)
TT_OPERADOR_LOGICO = 'OPERADOR_LOGICO'     # AND, OR, NOT (a menudo como palabras clave)
TT_OPERADOR_ASIGNACION = 'OPERADOR_ASIGNACION' # = (en sentencias SET)

TT_PARENTESIS_IZQ = 'PARENTESIS_IZQ' # (
TT_PARENTESIS_DER = 'PARENTESIS_DER' # )
TT_COMA = 'COMA'                     # ,
TT_PUNTO_Y_COMA = 'PUNTO_Y_COMA'     # ; (Terminador de sentencia, a veces opcional)
TT_PUNTO = 'PUNTO'                   # . (Para nombres calificados, ej: tabla.columna)
TT_ASTERISCO = 'ASTERISCO'           # * (Para SELECT *)

TT_COMENTARIO_LINEA = 'COMENTARIO_LINEA' # -- Esto es un comentario
TT_COMENTARIO_BLOQUE = 'COMENTARIO_BLOQUE' # /* Esto es un comentario */

TT_EOF_SQL = 'EOF_SQL'               # Fin de archivo/entrada
TT_ERROR_SQL = 'ERROR_SQL'           # Token para errores léxicos
TT_WHITESPACE_SQL = 'WHITESPACE_SQL'   # Espacios, tabs, nuevas líneas (generalmente se ignoran)

# Palabras clave comunes de SQL (T-SQL)
# T-SQL es generalmente insensible a mayúsculas/minúsculas para palabras clave e identificadores.
# El lexer las identificará y el parser/intérprete las tratará de forma insensible si es necesario.
PALABRAS_CLAVE_SQL = {
    'create', 'table', 'insert', 'into', 'values', 'select', 'from', 'where',
    'update', 'set', 'delete', 'and', 'or', 'not', 'null', 'primary', 'key',
    'varchar', 'int', 'integer', 'decimal', 'numeric', 'datetime', 'char', 'text',
    'nvarchar', 'float', 'real', 'bit', 'date', 'time',
    'alter', 'drop', 'add', 'constraint', 'foreign', 'references', 'default',
    'order', 'by', 'asc', 'desc', 'group', 'having', 'distinct', 'top',
    'begin', 'end', 'if', 'else', 'while', 'declare', 'as', 'exec', 'execute',
    'procedure', 'function', 'trigger', 'go' # GO es específico de T-SQL para lotes
}

# Podríamos tener un conjunto separado para tipos de datos si queremos distinguirlos
# léxicamente, o tratarlos como PALABRA_CLAVE y que el parser determine su rol.
# Por simplicidad, muchos tipos de datos están en PALABRAS_CLAVE_SQL.
# Si quisiéramos TT_TIPO_DATO explícito del lexer:
TIPOS_DATO_SQL = {
    'varchar', 'int', 'integer', 'decimal', 'numeric', 'datetime', 'char', 'text',
    'nvarchar', 'float', 'real', 'bit', 'date', 'time'
}

# Especificaciones de los tokens para T-SQL/SQL.
# El orden es importante: las palabras clave deben buscarse después de los identificadores
# o manejar la insensibilidad a mayúsculas/minúsculas al verificar si un identificador es palabra clave.
# Aquí, definiremos patrones para componentes y luego una lógica para clasificar.
ESPECIFICACIONES_TOKEN_SQL = [
    # Comentarios
    (r'--[^\n]*', TT_COMENTARIO_LINEA),    # Comentario de línea SQL: -- hasta el final de la línea
    (r'/\*[\s\S]*?\*/', TT_COMENTARIO_BLOQUE), # Comentario de bloque SQL: /* ... */ (no anidado)

    # Literales
    (r"'[^']*'(?:''[^']*')*", TT_LITERAL_CADENA), # Cadenas: 'texto', 'texto con '' comilla simple'
    # (r'"[^"]*"(?:""[^"]*")*', TT_LITERAL_CADENA_DOBLE_COMILLA), # Si se soportan comillas dobles para cadenas
    
    # Números: decimales y enteros.
    # Un número puede tener un punto decimal, y opcionalmente un exponente.
    # También puede tener un signo + o - al inicio.
    (r'[+-]?\d+\.\d*([eE][+-]?\d+)?', TT_LITERAL_NUMERICO), # Decimales: 1.0, .5, 1.2E-5
    (r'[+-]?\d+([eE][+-]?\d+)?', TT_LITERAL_NUMERICO),      # Enteros (con posible exponente): 123, 1e5

    # Operadores y Delimitadores
    (r'<>|!=|>=|<=|=|<|>', TT_OPERADOR_COMPARACION),
    (r'[\+\-\*\/%]', TT_OPERADOR_ARITMETICO), # % para módulo en T-SQL
    
    (r'\(', TT_PARENTESIS_IZQ),
    (r'\)', TT_PARENTESIS_DER),
    (r',', TT_COMA),
    (r';', TT_PUNTO_Y_COMA),
    (r'\.', TT_PUNTO),      # Para nombres calificados: database.schema.table.column
    (r'\*', TT_ASTERISCO), # Para SELECT *

    # Identificadores:
    # Pueden empezar con letra o _, seguido de letras, números o _.
    # También pueden estar entre corchetes [Identificador con espacios o palabras clave] o comillas dobles "..."
    # Por simplicidad inicial, manejaremos identificadores simples.
    # Un identificador también puede ser una palabra clave, se reclasificará después.
    (r'[a-zA-Z_][a-zA-Z0-9_]*', TT_IDENTIFICADOR), 
    # (r'\[[^\]]+\]', TT_IDENTIFICADOR_DELIMITADO), # Para [Column Name]
    # (r'"[^"]+"', TT_IDENTIFICADOR_DELIMITADO),   # Para "Table Name" (si no son cadenas)

    # Espacios en blanco (se ignorarán pero deben ser consumidos)
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
        """
        Procesa el código fuente completo y devuelve una lista de tokens.
        Returns:
            list: Una lista de objetos Token.
        """
        tokens = []
        while self.posicion_actual < len(self.codigo):
            match_encontrado_en_iteracion = False
            
            # Guardar la posición de inicio del token actual antes de buscar coincidencias.
            linea_inicio_token = self.linea_actual
            col_inicio_token = self.columna_actual

            for patron_regex, tipo_token_base in ESPECIFICACIONES_TOKEN_SQL:
                # Compilar el regex. Para SQL, la mayoría de las palabras clave e identificadores
                # son insensibles a mayúsculas/minúsculas, pero los literales de cadena no.
                # La insensibilidad para palabras clave se maneja después de identificar un IDENTIFICADOR.
                # Los patrones de regex para operadores y delimitadores son sensibles a mayúsculas/minúsculas por naturaleza.
                # Para identificadores, el patrón [a-zA-Z_] ya captura ambas cajas.
                
                # re.match solo busca al principio de la cadena (o subcadena desde self.posicion_actual).
                match = re.match(patron_regex, self.codigo[self.posicion_actual:])
                
                if match:
                    lexema = match.group(0) # El texto completo que coincidió.
                    match_encontrado_en_iteracion = True
                    
                    # Omitir WHITESPACE y COMENTARIOS (no se añaden a la lista final de tokens).
                    if tipo_token_base == TT_WHITESPACE_SQL or \
                       tipo_token_base == TT_COMENTARIO_LINEA or \
                       tipo_token_base == TT_COMENTARIO_BLOQUE:
                        self._avanzar(len(lexema)) # Avanzar la posición.
                        break # Salir del bucle for de especificaciones, volver al while.

                    tipo_token_final = tipo_token_base
                    valor_final = lexema # Valor por defecto es el lexema.

                    if tipo_token_base == TT_IDENTIFICADOR:
                        # Verificar si el identificador es una palabra clave.
                        # SQL es generalmente insensible a mayúsculas/minúsculas para palabras clave.
                        if lexema.lower() in PALABRAS_CLAVE_SQL:
                            tipo_token_final = TT_PALABRA_CLAVE
                        # Para identificadores delimitados, el valor es el contenido sin los delimitadores.
                        elif lexema.startswith('[') and lexema.endswith(']'):
                            valor_final = lexema[1:-1]
                        elif lexema.startswith('"') and lexema.endswith('"'):
                            valor_final = lexema[1:-1]
                        # El lexema se guarda tal como aparece en el código.
                    
                    elif tipo_token_base == TT_LITERAL_CADENA:
                        # Quitar comillas simples de inicio/fin y reemplazar '' por '.
                        valor_final = lexema[1:-1].replace("''", "'")
                    
                    elif tipo_token_base == TT_LITERAL_NUMERICO:
                        # Convertir el lexema a int o float.
                        if '.' in lexema or 'e' in lexema.lower():
                            try:
                                valor_final = float(lexema)
                            except ValueError:
                                # Si falla la conversión a float (ej. formato de exponente inválido)
                                # se podría marcar como error o dejar como string.
                                # Por ahora, se mantiene como lexema si falla float().
                                print(f"Advertencia LexerSQL: No se pudo convertir '{lexema}' a float.")
                                valor_final = lexema # Mantener como string si la conversión falla
                        else:
                            try:
                                valor_final = int(lexema)
                            except ValueError:
                                print(f"Advertencia LexerSQL: No se pudo convertir '{lexema}' a int.")
                                valor_final = lexema # Mantener como string si la conversión falla
                    
                    tokens.append(Token(tipo_token_final, lexema, linea_inicio_token, col_inicio_token, valor_final))
                    self._avanzar(len(lexema)) # Avanzar la posición.
                    break # Salir del bucle for, volver al while para el siguiente token.
            
            if not match_encontrado_en_iteracion and self.posicion_actual < len(self.codigo):
                # Si ninguna especificación coincidió y no hemos llegado al final del código,
                # es un carácter o secuencia no reconocida.
                caracter_erroneo = self.codigo[self.posicion_actual]
                tokens.append(Token(TT_ERROR_SQL, caracter_erroneo, linea_inicio_token, col_inicio_token,
                                    valor=f"Carácter no reconocido: '{caracter_erroneo}'"))
                self._avanzar() # Avanzar un carácter para evitar un bucle infinito.

        # Añadir el token de Fin de Archivo (EOF) al final de la lista.
        tokens.append(Token(TT_EOF_SQL, "EOF", self.linea_actual, self.columna_actual))
        return tokens

# (Fin de la clase LexerTSQL)
