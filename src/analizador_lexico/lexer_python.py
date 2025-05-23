# src/analizador_lexico/lexer_python.py
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

# Tipos de Token para Python
TT_IDENTIFICADOR = 'IDENTIFICADOR'
TT_PALABRA_CLAVE = 'PALABRA_CLAVE' # Anteriormente PALABRA_RESERVADA
TT_OPERADOR = 'OPERADOR'
TT_DELIMITADOR = 'DELIMITADOR'
TT_ENTERO = 'ENTERO'
TT_FLOTANTE = 'FLOTANTE'
TT_CADENA = 'CADENA'
TT_COMENTARIO = 'COMENTARIO'
TT_NUEVA_LINEA = 'NUEVA_LINEA'
TT_INDENT = 'INDENT'
TT_DEDENT = 'DEDENT'
TT_EOF = 'EOF' # Fin de archivo
TT_ERROR_LEXICO = 'ERROR_LEXICO' # Para errores

# Palabras clave de Python
PALABRAS_CLAVE_PYTHON = {
    'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await', 'break', 
    'class', 'continue', 'def', 'del', 'elif', 'else', 'except', 'finally', 
    'for', 'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'nonlocal', 
    'not', 'or', 'pass', 'raise', 'return', 'try', 'while', 'with', 'yield'
    # 'print' es una función en Python 3, no una palabra clave, 
    # pero el parser puede necesitar tratarla especialmente.
}
# Literales que son palabras clave
LITERALES_PALABRA_CLAVE_PYTHON = {
    'True': TT_PALABRA_CLAVE, # O un tipo TT_BOOLEANO si se prefiere
    'False': TT_PALABRA_CLAVE,
    'None': TT_PALABRA_CLAVE  # O un tipo TT_NONE si se prefiere
}


# Especificaciones de tokens para Python
# El orden es importante, especialmente para operadores de múltiples caracteres.
ESPECIFICACIONES_TOKEN_PYTHON = [
    # Comentarios (se deben ignorar o manejar por separado)
    (r'#[^\n\r]*', TT_COMENTARIO),

    # Nueva línea (muy importante para Python)
    (r'\n', TT_NUEVA_LINEA),

    # F-strings (antes de strings normales e identificadores)
    # Se capturan como TT_CADENA. La interpolación se manejaría en una fase posterior (intérprete).
    (r'f"(?:\\.|[^"\\])*?"', TT_CADENA),  # f"..."
    (r"f'(?:\\.|[^'\\])*?'", TT_CADENA),  # f'...'
    (r'rf"(?:\\.|[^"\\])*?"', TT_CADENA), # rf"..."
    (r"rf'(?:\\.|[^'\\])*?'", TT_CADENA), # rf'...'
    (r'fr"(?:\\.|[^"\\])*?"', TT_CADENA), # fr"..."
    (r"fr'(?:\\.|[^'\\])*?'", TT_CADENA), # fr'...'
    # Strings normales
    (r'r"(?:\\.|[^"\\])*?"', TT_CADENA),  # r"..."
    (r"r'(?:\\.|[^'\\])*?'", TT_CADENA),  # r'...'
    (r'"""(?:\\.|[^"\\])*?"""', TT_CADENA),  
    (r"'''(?:\\.|[^'\\])*?'''", TT_CADENA),  
    (r'"(?:\\.|[^"\\])*?"', TT_CADENA),    
    (r"'(?:\\.|[^'\\])*?'", TT_CADENA),
    # Palabras clave e Identificadores
    # (El manejo de si es palabra clave o identificador se hará después)
    (r'[a-zA-Z_][a-zA-Z0-9_]*', TT_IDENTIFICADOR),

    # Números (manejar flotantes antes que enteros si un entero puede ser prefijo de flotante)
    (r'\d+\.\d*(?:[eE][+-]?\d+)?', TT_FLOTANTE), # 3.14, 3. (con e/E para exponente)
    (r'\.\d+(?:[eE][+-]?\d+)?', TT_FLOTANTE),   # .5
    (r'\d+[eE][+-]?\d+', TT_FLOTANTE),        # 3e4
    (r'\d+', TT_ENTERO),                     # 123

    # Operadores
    (r'\+=|-=|\*=|/=|%=|&=|\|=|\^=|>>=|<<=|\*\*=|//=', TT_OPERADOR), # Asignación compuesta
    (r'\*\*|//', TT_OPERADOR), # Exponenciación, división entera
    (r'==|!=|<=|>=|<>', TT_OPERADOR), # Comparación
    (r'\+|-|\*|/|%|&|\||\^|~|<<|>>', TT_OPERADOR), # Aritméticos/Bitwise
    (r'<|>', TT_OPERADOR), # Comparación
    (r'=', TT_OPERADOR),  # Asignación simple

    # Delimitadores
    (r'\(|\)|\[|\]|\{|\}|:|@|\.|,', TT_DELIMITADOR), # Se quitó ;
    
    # Espacios en blanco (generalmente ignorados, excepto para indentación)
    # La indentación se maneja por separado. Esta regla es para espacios dentro de una línea.
    (r'[ \t]+', None), # Ignorar espacios y tabs que no sean indentación al inicio de línea
]


class LexerPython:
    def __init__(self, codigo_fuente):
        self.codigo = codigo_fuente.replace('\r\n', '\n').replace('\r', '\n') 
        self.tokens_generados = []
        # self.posicion_actual = 0 # No se usa directamente en el enfoque línea por línea
        self.linea_actual = 1      # Usado para el token EOF y potencialmente por _avanzar
        self.columna_actual = 1    # Usado para el token EOF y potencialmente por _avanzar
        self.pila_indentacion = [0] 
        self.regex_compilado = []
        for patron, tipo in ESPECIFICACIONES_TOKEN_PYTHON:
            self.regex_compilado.append((re.compile(patron), tipo))

    def _avanzar(self, cantidad=1): # Este método existe pero no es llamado por el tokenizador actual
        for _ in range(cantidad):
            if self.posicion_actual < len(self.codigo): # Necesitaría self.posicion_actual si se usara
                if self.codigo[self.posicion_actual] == '\n':
                    self.linea_actual += 1
                    self.columna_actual = 1
                else:
                    self.columna_actual += 1
                self.posicion_actual += 1
            else:
                break 

    def _procesar_identificador_o_palabra_clave(self, lexema, linea, col):
        if lexema in PALABRAS_CLAVE_PYTHON:
            if lexema in LITERALES_PALABRA_CLAVE_PYTHON:
                valor_real = None
                if lexema == 'True': valor_real = True
                elif lexema == 'False': valor_real = False
                return Token(TT_PALABRA_CLAVE, lexema, linea, col, valor_real) 
            return Token(TT_PALABRA_CLAVE, lexema, linea, col)
        return Token(TT_IDENTIFICADOR, lexema, linea, col)

    def _manejar_indentacion(self, linea_str, linea_num, columna_inicio_linea):
        espacios_inicio = 0
        linea_contenido_real = linea_str.lstrip() # Para ignorar espacios al inicio para la lógica de "vacía"
        
        # Solo procesar indentación para líneas que no están vacías y no son comentarios completos
        if not linea_contenido_real or linea_contenido_real.startswith('#'):
            return

        for char_idx, char in enumerate(linea_str):
            if char == ' ':
                espacios_inicio += 1
            elif char == '\t':
                # Un tab se expande a la siguiente columna múltiplo de 8.
                # Columna es 1-based.
                espacios_inicio = (espacios_inicio // 8 + 1) * 8 
            else:
                break # Fin del whitespace inicial
        
        nivel_actual_indentacion = espacios_inicio

        if nivel_actual_indentacion > self.pila_indentacion[-1]:
            self.pila_indentacion.append(nivel_actual_indentacion)
            self.tokens_generados.append(Token(TT_INDENT, "<INDENT>", linea_num, columna_inicio_linea))
        elif nivel_actual_indentacion < self.pila_indentacion[-1]:
            while nivel_actual_indentacion < self.pila_indentacion[-1]:
                self.pila_indentacion.pop()
                self.tokens_generados.append(Token(TT_DEDENT, "<DEDENT>", linea_num, columna_inicio_linea))
            if nivel_actual_indentacion != self.pila_indentacion[-1]:
                # Error de indentación: nivel no coincide con ninguno anterior
                # El lexema del error podría ser la línea entera o la parte indentada.
                # Usamos la línea desde la indentación para el lexema del error.
                lexema_error = linea_str[espacios_inicio:] if espacios_inicio < len(linea_str) else "<FIN_LINEA_INDENT_ERR>"
                self.tokens_generados.append(Token(TT_ERROR_LEXICO, lexema_error, linea_num, columna_inicio_linea + espacios_inicio, "Error de indentación inconsistente"))


    def tokenizar(self):
        lineas = self.codigo.split('\n')
        
        for num_linea_enum, linea_str_original in enumerate(lineas):
            linea_num_real = num_linea_enum + 1
            columna_actual_en_linea = 1 # Columna es 1-based
            
            # Manejar indentación al inicio de cada línea física
            self._manejar_indentacion(linea_str_original, linea_num_real, 1) # Columna 1 para INDENT/DEDENT

            pos_en_linea = 0
            # Saltar espacios iniciales que ya fueron contados por _manejar_indentacion
            while pos_en_linea < len(linea_str_original) and linea_str_original[pos_en_linea].isspace():
                pos_en_linea += 1
            
            linea_tuvo_tokens_significativos = False

            while pos_en_linea < len(linea_str_original):
                col_actual_real = pos_en_linea + 1
                match_encontrado_en_iteracion = False
                subcadena_linea = linea_str_original[pos_en_linea:]

                for regex, tipo_token_base in self.regex_compilado:
                    if tipo_token_base == TT_NUEVA_LINEA: continue # Los TT_NUEVA_LINEA se manejan al final de la línea

                    match = regex.match(subcadena_linea)
                    if match:
                        lexema = match.group(0)
                        match_encontrado_en_iteracion = True
                        
                        if tipo_token_base is None: # Ignorar (ej. espacios dentro de la línea)
                            pos_en_linea += len(lexema)
                            break 
                        
                        if tipo_token_base == TT_COMENTARIO:
                            pos_en_linea += len(lexema) 
                            # El comentario consume el resto de la línea, así que salimos del bucle interno
                            match_encontrado_en_iteracion = True # Asegura que no se marque error
                            break # Salir del bucle de regex, ir a la siguiente línea

                        token_final = None
                        if tipo_token_base == TT_IDENTIFICADOR:
                            token_final = self._procesar_identificador_o_palabra_clave(lexema, linea_num_real, col_actual_real)
                        elif tipo_token_base == TT_CADENA:
                            valor_cadena = lexema 
                            prefijo_f = ""
                            if lexema.lower().startswith(('f"', "f'", 'rf"', "rf'", 'fr"', "fr'")):
                                prefijo_f = lexema[0].lower()
                                if lexema.lower().startswith(('rf', 'fr')): valor_cadena = lexema[3:-1]
                                else: valor_cadena = lexema[2:-1] 
                            elif lexema.startswith(('"""', "'''")): valor_cadena = lexema[3:-3]
                            else: valor_cadena = lexema[1:-1]
                            valor_cadena = valor_cadena.replace('\\n', '\n').replace('\\t', '\t').replace("\\'", "'").replace('\\"', '"').replace('\\\\', '\\')
                            # Para f-strings, el valor es la cadena interna. La 'f' es parte del lexema.
                            token_final = Token(TT_CADENA, lexema, linea_num_real, col_actual_real, valor_cadena)
                        elif tipo_token_base == TT_ENTERO:
                            token_final = Token(TT_ENTERO, lexema, linea_num_real, col_actual_real, int(lexema))
                        elif tipo_token_base == TT_FLOTANTE:
                            token_final = Token(TT_FLOTANTE, lexema, linea_num_real, col_actual_real, float(lexema))
                        else: 
                            token_final = Token(tipo_token_base, lexema, linea_num_real, col_actual_real)
                        
                        if token_final:
                            self.tokens_generados.append(token_final)
                            linea_tuvo_tokens_significativos = True

                        pos_en_linea += len(lexema)
                        break 
                
                if not match_encontrado_en_iteracion:
                    if pos_en_linea < len(linea_str_original): 
                        caracter_erroneo = linea_str_original[pos_en_linea]
                        self.tokens_generados.append(Token(TT_ERROR_LEXICO, caracter_erroneo, linea_num_real, col_actual_real,
                                                    valor=f"Carácter no reconocido: '{caracter_erroneo}'"))
                        pos_en_linea += 1 
                        linea_tuvo_tokens_significativos = True # Un error también es significativo
            
            # Añadir TT_NUEVA_LINEA después de procesar cada línea física,
            # si la línea no estaba vacía (después de quitar espacios iniciales y comentarios)
            # o si la última cosa que se añadió no fue un DEDENT (porque DEDENT ya implica fin de bloque).
            if linea_str_original.strip() and not linea_str_original.lstrip().startswith('#'):
                 self.tokens_generados.append(Token(TT_NUEVA_LINEA, "\\n", linea_num_real, len(linea_str_original) + 1))
            elif not linea_str_original.strip() and self.tokens_generados and self.tokens_generados[-1].tipo == TT_DEDENT:
                 # Si la línea está vacía pero acabamos de hacer DEDENT, aún necesitamos un NUEVA_LINEA
                 # para separar el DEDENT de la siguiente línea de código.
                 self.tokens_generados.append(Token(TT_NUEVA_LINEA, "\\n", linea_num_real, 1))


        # Al final del archivo, generar los DEDENTs necesarios y un NUEVA_LINEA final si es necesario
        if self.tokens_generados and self.tokens_generados[-1].tipo != TT_NUEVA_LINEA:
             self.tokens_generados.append(Token(TT_NUEVA_LINEA, "\\n", self.linea_actual, self.columna_actual))

        while len(self.pila_indentacion) > 1:
            self.pila_indentacion.pop()
            self.tokens_generados.append(Token(TT_DEDENT, "<DEDENT>", self.linea_actual, 1)) # Columna podría ser la de la última línea

        self.tokens_generados.append(Token(TT_EOF, "EOF", self.linea_actual, self.columna_actual ))
        return self.tokens_generados

