# src/analizador_lexico/lexer_javascript.py
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
        self.lexema = lexema      # El texto actual del token (ej: "function", "miVariable")
        self.linea = linea        # Número de línea donde aparece el token
        self.columna = columna    # Número de columna donde comienza el token
        # El valor real (ej: 123 para "123", o el contenido de una cadena sin comillas).
        self.valor = valor if valor is not None else lexema 

    def __repr__(self):
        # Representación en cadena del token, útil para depuración.
        lexema_display = self.lexema.replace('\n', '\\n').replace('\r', '\\r')
        valor_repr = repr(self.valor) if self.valor != self.lexema and self.valor is not None else ""
        
        return (f"Token({self.tipo}, '{lexema_display}', "
                f"L{self.linea}:C{self.columna}" +
                (f", V:{valor_repr}" if valor_repr else "") + ")")

# Tipos de Token para JavaScript
TT_PALABRA_CLAVE = 'PALABRA_CLAVE_JS' # function, var, let, const, if, else, for, while, return, class, true, false, null, undefined, new, this, etc.
TT_IDENTIFICADOR = 'IDENTIFICADOR_JS'   # Nombres de variables, funciones, clases, etc.
TT_PUNTO_Y_COMA = 'PUNTO_Y_COMA_JS'  # ; (a menudo opcional)
TT_COMA = 'COMA_JS'                  # ,
TT_PUNTO = 'PUNTO_JS'                # . (acceso a propiedades)

TT_PARENTESIS_IZQ = 'PARENTESIS_IZQ_JS' # (
TT_PARENTESIS_DER = 'PARENTESIS_DER_JS' # )
TT_LLAVE_IZQ = 'LLAVE_IZQ_JS'         # {
TT_LLAVE_DER = 'LLAVE_DER_JS'         # }
TT_CORCHETE_IZQ = 'CORCHETE_IZQ_JS'   # [
TT_CORCHETE_DER = 'CORCHETE_DER_JS'   # ]

# Literales
TT_LITERAL_NUMERICO = 'LITERAL_NUMERICO_JS' # 123, 45.67, 0xFF, 1e5, NaN, Infinity
TT_LITERAL_CADENA = 'LITERAL_CADENA_JS'   # "cadena", 'cadena', `plantilla ${expr}` (plantillas son más complejas)
TT_LITERAL_BOOLEANO = 'LITERAL_BOOLEANO_JS' # true, false (son palabras clave)
TT_LITERAL_NULL = 'LITERAL_NULL_JS'       # null (palabra clave)
TT_LITERAL_UNDEFINED = 'LITERAL_UNDEFINED_JS' # undefined (identificador global, no palabra clave estricta pero se trata especial)
TT_LITERAL_REGEX = 'LITERAL_REGEX_JS'     # /patron/flags (complejo de distinguir de la división)

# Operadores
TT_OPERADOR_ASIGNACION = 'OPERADOR_ASIGNACION_JS' # =, +=, -=, *=, /=, %=, **=, <<=, >>=, >>>=, &=, ^=, |=
TT_OPERADOR_ARITMETICO = 'OPERADOR_ARITMETICO_JS' # +, -, *, /, %, ++, --, **
TT_OPERADOR_COMPARACION = 'OPERADOR_COMPARACION_JS'# ==, ===, !=, !==, >, <, >=, <=
TT_OPERADOR_LOGICO = 'OPERADOR_LOGICO_JS'      # &&, ||, !
TT_OPERADOR_BITWISE = 'OPERADOR_BITWISE_JS'    # &, |, ^, ~, <<, >>, >>>
TT_OPERADOR_TERNARIO = 'OPERADOR_TERNARIO_JS'  # ? (parte de ?: )
TT_DOS_PUNTOS_TERNARIO = 'DOS_PUNTOS_TERNARIO_JS' # : (parte de ?: )
TT_OPERADOR_SPREAD = 'OPERADOR_SPREAD_JS'    # ...
TT_FLECHA = 'FLECHA_JS'                  # => (para funciones flecha)

# Comentarios
TT_COMENTARIO_LINEA = 'COMENTARIO_LINEA_JS'  # // Esto es un comentario
TT_COMENTARIO_BLOQUE = 'COMENTARIO_BLOQUE_JS' # /* Esto es un comentario */

TT_EOF_JS = 'EOF_JS'                   # Fin de archivo/entrada
TT_ERROR_JS = 'ERROR_JS'               # Token para errores léxicos
TT_WHITESPACE_JS = 'WHITESPACE_JS'       # Espacios, tabs, nuevas líneas (generalmente se ignoran)

# Palabras clave de JavaScript (subconjunto inicial)
# JavaScript es sensible a mayúsculas/minúsculas.
PALABRAS_CLAVE_JS = {
    'await', 'break', 'case', 'catch', 'class', 'const', 'continue', 'debugger', 
    'default', 'delete', 'do', 'else', 'export', 'extends', 'false', 'finally', 
    'for', 'function', 'if', 'import', 'in', 'instanceof', 'let', 'new', 'null',
    'return', 'super', 'switch', 'this', 'throw', 'true', 'try', 'typeof', 'var',
    'void', 'while', 'with', 'yield',
    # 'undefined' no es una palabra clave reservada, es una propiedad global del objeto global.
    # Lo trataremos como un identificador especial o un literal si el lexer lo maneja.
    # 'async', 'get', 'set', 'static' son contextuales en algunos casos o parte de declaraciones.
}

# Identificadores especiales que a veces se comportan como palabras clave o tienen significado especial.
IDENTIFICADORES_ESPECIALES_JS = {
    'undefined', 'NaN', 'Infinity',
    'async', 'get', 'set', 'static', # Pueden ser contextuales
    'console', 'log', 'alert', 'document', 'window' # Objetos/métodos comunes
}

# Especificaciones de los tokens para JavaScript.
# El orden es importante.
ESPECIFICACIONES_TOKEN_JS = [
    # Comentarios (deben ir primero para que no interfieran con el operador de división)
    (r'//[^\n\r]*', TT_COMENTARIO_LINEA),      # Comentario de línea
    (r'/\*[\s\S]*?\*/', TT_COMENTARIO_BLOQUE), # Comentario de bloque (no anidado)

    # Plantillas literales (backticks). Captura todo el contenido, incluyendo ${...}.
    # El \` se maneja para escapar backticks dentro de la plantilla.
    # El [^`] captura cualquier carácter que no sea un backtick.
    # El [\s\S] dentro de ${} es para permitir cualquier carácter, incluyendo saltos de línea.
    (r'`(?:\\`|\\\$|\$\{[\s\S]*?\}|[^`])*`', TT_LITERAL_CADENA), # Plantilla literal

    # Cadenas con comillas dobles. Permite caracteres Unicode (incluyendo acentuados)
    # y secuencias de escape comunes.
    (r'"(?:\\(?:[bfnrtv"\'\\]|u[0-9a-fA-F]{4}|x[0-9a-fA-F]{2})|[^"\\])*"', TT_LITERAL_CADENA),

    # Cadenas con comillas simples. Similar a comillas dobles.
    (r"'(?:\\(?:[bfnrtv\"\'\\]|u[0-9a-fA-F]{4}|x[0-9a-fA-F]{2})|[^'\\])*'", TT_LITERAL_CADENA),

    # Literales de cadena (simples y dobles, con manejo básico de escapes)
    # Este regex es simplificado y no maneja todos los escapes de JS.
    (r'"(?:\\.|[^"\\])*"', TT_LITERAL_CADENA),  # Comillas dobles
    (r"' (?:\\.|[^'\\])*'", TT_LITERAL_CADENA),  # Comillas simples
    # Plantillas literales (``) son más complejas debido a las expresiones ${...}
    # (r'`(?:\\.|[^`\\])*`', TT_LITERAL_CADENA_PLANTILLA), # Simplificado, sin interpolación

    # Números: hexadecimales, binarios, octales (nuevos), decimales, y con exponente.
    (r'0[xX][0-9a-fA-F]+', TT_LITERAL_NUMERICO), # Hexadecimal
    (r'0[bB][01]+', TT_LITERAL_NUMERICO),       # Binario
    (r'0[oO][0-7]+', TT_LITERAL_NUMERICO),       # Octal (ES6+)
    # Números decimales y con exponente. Debe ir después de los anteriores.
    # Permite .123, 123., 123.456, 1e5, 1.2e-3, etc.
    (r'[+-]?(\d+\.\d*|\.\d+)([eE][+-]?\d+)?', TT_LITERAL_NUMERICO), # Decimales
    (r'[+-]?\d+([eE][+-]?\d+)?', TT_LITERAL_NUMERICO),             # Enteros

    # Operadores (el orden puede ser importante para los de múltiples caracteres)
    # Operadores de asignación compuestos
    (r'>>>=|>>=|<<=|\|\|=|\&\&=|\?\?=', TT_OPERADOR_ASIGNACION), # Asignación lógica nullish, OR, AND
    (r'\+=|-=|\*=|\/=|%=|\*\*=|&=|\^=|\|=', TT_OPERADOR_ASIGNACION),
    # Operadores lógicos y nullish coalescing
    (r'\|\||&&|\?\?', TT_OPERADOR_LOGICO),
    # Operadores bitwise
    (r'>>>|<<|>>', TT_OPERADOR_BITWISE),
    # Operadores de comparación (incluyendo estrictos)
    (r'===|!==|==|!=|<=|>=|<|>', TT_OPERADOR_COMPARACION),
    # Flecha para funciones
    (r'=>', TT_FLECHA),
    # Operador Spread/Rest
    (r'\.\.\.', TT_OPERADOR_SPREAD),
    # Operadores aritméticos (incluyendo incremento/decremento y exponenciación)
    (r'\+\+|--', TT_OPERADOR_ARITMETICO), # Incremento/Decremento
    (r'\*\*', TT_OPERADOR_ARITMETICO),   # Exponenciación
    (r'[\+\-\*\/%]', TT_OPERADOR_ARITMETICO), # +, -, *, /, %
    # Operadores bitwise simples
    (r'[&|\^~]', TT_OPERADOR_BITWISE),
    # Operador de asignación simple
    (r'=', TT_OPERADOR_ASIGNACION),
    # Operador lógico NOT
    (r'!', TT_OPERADOR_LOGICO), # También puede ser parte de !=, !==
    # Operador ternario
    (r'\?', TT_OPERADOR_TERNARIO),
    
    # Delimitadores
    (r'\(', TT_PARENTESIS_IZQ),
    (r'\)', TT_PARENTESIS_DER),
    (r'\{', TT_LLAVE_IZQ),
    (r'\}', TT_LLAVE_DER),
    (r'\[', TT_CORCHETE_IZQ),
    (r'\]', TT_CORCHETE_DER),
    (r';', TT_PUNTO_Y_COMA),
    (r',', TT_COMA),
    (r'\.', TT_PUNTO),
    (r':', TT_DOS_PUNTOS_TERNARIO), # También usado en objetos y etiquetas

    # Identificadores (deben ir después de palabras clave si no se reclasifican,
    # o antes si se reclasifican después). Aquí los ponemos y luego reclasificamos.
    # Un identificador JS puede empezar con letra, $, o _, seguido de esos o números.
    (r'\$', TT_ERROR_JS),  # Detectar $ solo como error léxico
    (r'[a-zA-Z_$][a-zA-Z0-9_$]*', TT_IDENTIFICADOR),

    # Espacios en blanco (se ignorarán pero deben ser consumidos)
    (r'\s+', TT_WHITESPACE_JS), 
]

class LexerJavaScript:
    """
    Analizador Léxico para un subconjunto de JavaScript.
    """
    def __init__(self, codigo_fuente):
        self.codigo = codigo_fuente
        self.posicion_actual = 0
        self.linea_actual = 1
        self.columna_actual = 1 # Columna de inicio del token actual en la línea

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

    def _procesar_valor_cadena(self, lexema):
        """
        Procesa el lexema de una cadena para obtener su valor real,
        manejando escapes básicos y quitando las comillas/acentos graves.
        """
        if lexema.startswith('`') and lexema.endswith('`'):
            # Para plantillas literales, por ahora devolvemos el contenido interno tal cual,
            # incluyendo las interpolaciones ${...} sin procesar.
            # Un manejo más avanzado podría parsear las interpolaciones.
            contenido = lexema[1:-1]
            # Simplificación de escapes comunes dentro de plantillas
            contenido = contenido.replace('\\`', '`')
            contenido = contenido.replace('\\\\', '\\')
            # No procesamos ${} aquí, se queda como parte de la cadena.
            return contenido
        elif (lexema.startswith('"') and lexema.endswith('"')) or \
             (lexema.startswith("'") and lexema.endswith("'")):
            contenido = lexema[1:-1]
            # Un decodificador de escapes más robusto sería mejor.
            # Esto es una aproximación simple.
            try:
                # Intenta usar 'unicode_escape' para manejar escapes comunes como \n, \t, \uXXXX
                # Cuidado: esto puede tener comportamientos inesperados con barras invertidas literales.
                # Una solución más robusta iteraría y reemplazaría escapes conocidos.
                # Ejemplo simple (no exhaustivo):
                processed_content = contenido.replace('\\n', '\n')
                processed_content = processed_content.replace('\\r', '\r')
                processed_content = processed_content.replace('\\t', '\t')
                processed_content = processed_content.replace("\\'", "'")
                processed_content = processed_content.replace('\\"', '"')
                processed_content = processed_content.replace('\\\\', '\\')
                # Faltarían \b, \f, \v, \xHH, \uHHHH, etc.
                return processed_content
            except Exception:
                return contenido # Devolver el contenido tal cual si hay error en el decode
        return lexema # Fallback

    def tokenizar(self):
        """
        Procesa el código fuente completo y devuelve una lista de tokens.
        """
        tokens = []
        while self.posicion_actual < len(self.codigo):
            match_encontrado_en_iteracion = False
            linea_inicio_token = self.linea_actual
            col_inicio_token = self.columna_actual

            for patron_regex, tipo_token_base in ESPECIFICACIONES_TOKEN_JS:
                match = re.match(patron_regex, self.codigo[self.posicion_actual:])
                
                if match:
                    lexema = match.group(0)
                    match_encontrado_en_iteracion = True
                    
                    if tipo_token_base == TT_WHITESPACE_JS or \
                       tipo_token_base == TT_COMENTARIO_LINEA or \
                       tipo_token_base == TT_COMENTARIO_BLOQUE:
                        self._avanzar(len(lexema))
                        break 

                    tipo_token_final = tipo_token_base
                    valor_final = lexema 

                    if tipo_token_base == TT_IDENTIFICADOR:
                        if lexema in PALABRAS_CLAVE_JS:
                            tipo_token_final = TT_PALABRA_CLAVE
                            if lexema == 'true': valor_final = True
                            elif lexema == 'false': valor_final = False
                            elif lexema == 'null': valor_final = None
                        elif lexema == 'undefined':
                            valor_final = None # Representando undefined como None
                        elif lexema == 'NaN':
                            valor_final = float('nan')
                        elif lexema == 'Infinity':
                            valor_final = float('inf')
                    
                    elif tipo_token_base == TT_LITERAL_CADENA:
                        valor_final = self._procesar_valor_cadena(lexema)
                    
                    elif tipo_token_base == TT_LITERAL_NUMERICO:
                        try:
                            if lexema.lower().startswith('0x'): valor_final = int(lexema, 16)
                            elif lexema.lower().startswith('0b'): valor_final = int(lexema, 2)
                            elif lexema.lower().startswith('0o'): valor_final = int(lexema, 8)
                            elif '.' in lexema or 'e' in lexema.lower(): valor_final = float(lexema)
                            else: valor_final = int(lexema)
                        except ValueError:
                            tipo_token_final = TT_ERROR_JS
                            valor_final = f"Literal numérico inválido: {lexema}"
                    
                    tokens.append(Token(tipo_token_final, lexema, linea_inicio_token, col_inicio_token, valor_final))
                    self._avanzar(len(lexema))
                    break 
            
            if not match_encontrado_en_iteracion and self.posicion_actual < len(self.codigo):
                caracter_erroneo = self.codigo[self.posicion_actual]
                tokens.append(Token(TT_ERROR_JS, caracter_erroneo, linea_inicio_token, col_inicio_token,
                                    valor=f"Carácter no reconocido: '{caracter_erroneo}'"))
                self._avanzar() 

        tokens.append(Token(TT_EOF_JS, "EOF", self.linea_actual, self.columna_actual))
        return tokens
