# src/analizador_lexico/lexer_html.py
import re

# Definición de la clase Token (reutilizada)
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

# Tipos de Token para HTML
TT_DOCTYPE = 'DOCTYPE'                 # <!DOCTYPE ...>
TT_ETIQUETA_APERTURA = 'ETIQUETA_APERTURA' # <nombre_etiqueta
TT_ETIQUETA_CIERRE = 'ETIQUETA_CIERRE'   # </nombre_etiqueta>
TT_SLASH_MAYOR_QUE = 'SLASH_MAYOR_QUE' # /> (para etiquetas de autocierre)
TT_MAYOR_QUE = 'MAYOR_QUE'             # >
TT_MENOR_QUE = 'MENOR_QUE'             # < (usado internamente si no es parte de una etiqueta completa)
TT_SLASH = 'SLASH'                   # / (usado internamente)
TT_IDENTIFICADOR = 'IDENTIFICADOR'       # nombre_etiqueta, nombre_atributo
TT_ATRIBUTO_NOMBRE = 'ATRIBUTO_NOMBRE'   # Nombre de un atributo (se podría usar IDENTIFICADOR)
TT_ATRIBUTO_VALOR = 'ATRIBUTO_VALOR'    # Valor de un atributo (generalmente entre comillas)
TT_IGUAL = 'IGUAL'                   # =
TT_TEXTO = 'TEXTO'                     # Contenido de texto entre etiquetas
TT_COMENTARIO_HTML = 'COMENTARIO_HTML'   
TT_WHITESPACE = 'WHITESPACE'           # Espacios, tabs, nuevas líneas (significativos en algunos contextos)
TT_EOF_HTML = 'EOF_HTML'                 # Fin de archivo
TT_ERROR_HTML = 'ERROR_HTML'             # Token para errores léxicos

# Especificaciones de tokens para HTML
# El orden es importante.
ESPECIFICACIONES_TOKEN_HTML = [
    (r'<!DOCTYPE[^>]*>', TT_DOCTYPE),          # DOCTYPE
    (r'<!--[\s\S]*?-->', TT_COMENTARIO_HTML),   # Comentarios HTML
    (r'</[a-zA-Z][a-zA-Z0-9_:-]*\s*>', TT_ETIQUETA_CIERRE), # Etiqueta de cierre, ej: </p>
    (r'<[a-zA-Z][a-zA-Z0-9_:-]*', TT_ETIQUETA_APERTURA), # Inicio de etiqueta de apertura, ej: <div
    (r'/>', TT_SLASH_MAYOR_QUE),             # Para etiquetas de autocierre, ej: <img />
    (r'>', TT_MAYOR_QUE),                    # Cierre de etiqueta de apertura
    (r'<', TT_MENOR_QUE),                    # Menor que (si no es parte de una etiqueta)
    (r'/', TT_SLASH),                        # Slash (si no es parte de /> o </tag>)
    (r'=', TT_IGUAL),                        # Signo igual para atributos
    (r'[a-zA-Z_][a-zA-Z0-9_:-]*(?=\s*=)', TT_ATRIBUTO_NOMBRE), 
    (r'"[^"]*"', TT_ATRIBUTO_VALOR),
    (r"'[^']*'", TT_ATRIBUTO_VALOR),
    (r'\s+', TT_WHITESPACE), # Espacios en blanco
    (r'[^<]+', TT_TEXTO), # Texto: cualquier cosa que no sea '<'
    (r'[a-zA-Z_][a-zA-Z0-9_:-]+', TT_IDENTIFICADOR),
]


class LexerHTML:
    def __init__(self, codigo_fuente):
        self.codigo = codigo_fuente
        self.posicion_actual = 0
        self.linea_actual = 1
        self.columna_actual = 1
        self.regex_compilado = []
        for patron, tipo in ESPECIFICACIONES_TOKEN_HTML:
            flags = re.IGNORECASE if tipo == TT_DOCTYPE else 0
            self.regex_compilado.append((re.compile(patron, flags), tipo))

    def _avanzar_posicion(self, texto_consumido):
        for char in texto_consumido:
            if char == '\n':
                self.linea_actual += 1
                self.columna_actual = 1
            else:
                self.columna_actual += 1
        self.posicion_actual += len(texto_consumido)

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
                    
                    valor_token = lexema 
                    if tipo_token_base == TT_ATRIBUTO_VALOR:
                        valor_token = lexema[1:-1]
                    
                    if tipo_token_base == TT_WHITESPACE: # No añadir tokens de WHITESPACE
                         self._avanzar_posicion(lexema)
                         break 

                    token = Token(tipo_token_base, lexema, linea_inicio_token, col_inicio_token, valor_token)
                    tokens.append(token)
                    
                    self._avanzar_posicion(lexema)
                    break 
            
            if not match_encontrado_en_iteracion:
                if self.posicion_actual < len(self.codigo):
                    caracter_erroneo = self.codigo[self.posicion_actual]
                    tokens.append(Token(TT_ERROR_HTML, caracter_erroneo, linea_inicio_token, col_inicio_token,
                                        valor=f"Carácter no reconocido: '{caracter_erroneo}'"))
                    self._avanzar_posicion(caracter_erroneo) 
        
        tokens.append(Token(TT_EOF_HTML, "EOF", self.linea_actual, self.columna_actual))
        return tokens

