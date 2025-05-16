# src/analizador_lexico/lexer_cpp.py
import re

# Reutilizamos la definición de la clase Token.
class Token:
    """
    Representa un token léxico con su tipo, lexema (texto),
    número de línea y columna donde aparece, y un valor opcional.
    """
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

# Tipos de Token para C++
TT_PALABRA_CLAVE = 'PALABRA_CLAVE_CPP'  # ej: int, class, if, for, while, return, using, namespace
TT_IDENTIFICADOR = 'IDENTIFICADOR_CPP'   # ej: miVariable, MiClase, std
TT_DIRECTIVA_PREPROCESADOR = 'DIRECTIVA_PREPROCESADOR_CPP' # ej: #include, #define
TT_CABECERA_ESTANDAR = 'CABECERA_ESTANDAR_CPP' # ej: <iostream>, <vector> (dentro de #include)
TT_CABECERA_USUARIO = 'CABECERA_USUARIO_CPP'   # ej: "mi_cabecera.h" (dentro de #include)

# Literales
TT_LITERAL_ENTERO = 'LITERAL_ENTERO_CPP'     # ej: 123, 0xFF (hex), 077 (octal)
TT_LITERAL_FLOTANTE = 'LITERAL_FLOTANTE_CPP' # ej: 3.14, 1.0e-5, .5f
TT_LITERAL_CARACTER = 'LITERAL_CARACTER_CPP' # ej: 'a', '\n'
TT_LITERAL_CADENA = 'LITERAL_CADENA_CPP'   # ej: "hola mundo", R"(raw string)"
TT_LITERAL_BOOLEANO = 'LITERAL_BOOLEANO_CPP' # true, false (son palabras clave)
TT_PUNTERO_NULL = 'PUNTERO_NULL_CPP'     # nullptr (palabra clave en C++11)

# Operadores
TT_OPERADOR_ARITMETICO = 'OPERADOR_ARITMETICO_CPP' # +, -, *, /, %, ++, --
TT_OPERADOR_ASIGNACION = 'OPERADOR_ASIGNACION_CPP' # =, +=, -=, *=, /=, %=, &=, |=, ^=, <<=, >>=
TT_OPERADOR_COMPARACION = 'OPERADOR_COMPARACION_CPP'# ==, !=, <, >, <=, >=
TT_OPERADOR_LOGICO = 'OPERADOR_LOGICO_CPP'      # &&, ||, !
TT_OPERADOR_BITWISE = 'OPERADOR_BITWISE_CPP'    # &, |, ^, ~, <<, >>
TT_OPERADOR_MIEMBRO = 'OPERADOR_MIEMBRO_CPP'    # . (punto), -> (flecha), :: (resolución de alcance)
TT_OPERADOR_TERNARIO = 'OPERADOR_TERNARIO_CPP'  # ?
TT_OPERADOR_SIZEOF = 'OPERADOR_SIZEOF_CPP'    # sizeof (palabra clave que actúa como operador)
# (Más operadores como typeid, new, delete, etc., que también son palabras clave)

# Delimitadores y Puntuación
TT_LLAVE_IZQ = 'LLAVE_IZQ_CPP'         # {
TT_LLAVE_DER = 'LLAVE_DER_CPP'         # }
TT_PARENTESIS_IZQ = 'PARENTESIS_IZQ_CPP' # (
TT_PARENTESIS_DER = 'PARENTESIS_DER_CPP' # )
TT_CORCHETE_IZQ = 'CORCHETE_IZQ_CPP'   # [
TT_CORCHETE_DER = 'CORCHETE_DER_CPP'   # ]
TT_PUNTO_Y_COMA = 'PUNTO_Y_COMA_CPP'  # ;
TT_COMA = 'COMA_CPP'                  # ,
TT_DOS_PUNTOS = 'DOS_PUNTOS_CPP'
TT_PUNTO = 'PUNTO_CPP'       # : (para etiquetas, herencia, ternario)

# Comentarios
TT_COMENTARIO_LINEA = 'COMENTARIO_LINEA_CPP'  # // Esto es un comentario
TT_COMENTARIO_BLOQUE = 'COMENTARIO_BLOQUE_CPP' # /* Esto es un comentario */

TT_EOF_CPP = 'EOF_CPP'                   # Fin de archivo/entrada
TT_ERROR_CPP = 'ERROR_CPP'               # Token para errores léxicos
TT_WHITESPACE_CPP = 'WHITESPACE_CPP'       # Espacios, tabs, nuevas líneas

# Palabras clave de C++ (subconjunto inicial, sensible a mayúsculas/minúsculas)
PALABRAS_CLAVE_CPP = {
    'alignas', 'alignof', 'and', 'and_eq', 'asm', 'atomic_cancel', 'atomic_commit', 
    'atomic_noexcept', 'auto', 'bitand', 'bitor', 'bool', 'break', 'case', 'catch', 
    'char', 'char8_t', 'char16_t', 'char32_t', 'class', 'compl', 'concept', 'const',
    'consteval', 'constexpr', 'constinit', 'const_cast', 'continue', 'co_await', 
    'co_return', 'co_yield', 'decltype', 'default', 'delete', 'do', 'double', 
    'dynamic_cast', 'else', 'enum', 'explicit', 'export', 'extern', 'false', 'float',
    'for', 'friend', 'goto', 'if', 'inline', 'int', 'long', 'mutable', 'namespace',
    'new', 'noexcept', 'not', 'not_eq', 'nullptr', 'operator', 'or', 'or_eq', 
    'private', 'protected', 'public', 'reflexpr', 'register', 'reinterpret_cast', 
    'requires', 'return', 'short', 'signed', 'sizeof', 'static', 'static_assert',
    'static_cast', 'struct', 'switch', 'synchronized', 'template', 'this', 
    'thread_local', 'throw', 'true', 'try', 'typedef', 'typeid', 'typename', 
    'union', 'unsigned', 'using', 'virtual', 'void', 'volatile', 'wchar_t', 
    'while', 'xor', 'xor_eq',
    # Palabras clave comunes para el simulador
    'cout', 'cin', 'endl', 'std', 'main', 'include', 'define', 'iostream', 'vector', 'string'
    # 'iostream', 'vector', 'string' no son keywords per se, pero se usan en #include
    # y 'std', 'cout', 'cin', 'endl', 'main' son identificadores muy comunes.
    # Es mejor que el lexer los marque como IDENTIFICADOR y el parser/semántico les dé significado.
    # Sin embargo, 'include' y 'define' sí son parte de directivas.
}
# Separaremos las directivas de preprocesador
DIRECTIVAS_PREPROCESADOR_CPP = {
    'include', 'define', 'undef', 'if', 'ifdef', 'ifndef', 'else', 'elif', 'endif',
    'line', 'error', 'pragma', 'warning' 
    # 'if', 'else', 'elif' también son palabras clave del lenguaje,
    # el contexto (si están después de #) determinará si son directivas.
}

# Especificaciones de los tokens para C++. El orden es crucial.
ESPECIFICACIONES_TOKEN_CPP = [
    # 1. Directivas de preprocesador (líneas que comienzan con #)
    # Esta es una simplificación. Un preprocesador real es más complejo.
    # Captura toda la línea después de # hasta el salto de línea.
    (r'#\s*([a-zA-Z_][a-zA-Z0-9_]*)(.*)', TT_DIRECTIVA_PREPROCESADOR), # Captura la directiva y el resto

    # 2. Comentarios (deben ir antes de operadores como / o *)
    (r'//[^\n\r]*', TT_COMENTARIO_LINEA),      # Comentario de línea
    (r'/\*[\s\S]*?\*/', TT_COMENTARIO_BLOQUE), # Comentario de bloque (no anidado simple)

    # 3. Literales
    # Cadenas Raw C++11: R"delim(...)delim"
    (r'R"([^\s()\\\t\n\r]*)\([\s\S]*?\)\1"', TT_LITERAL_CADENA), 
    # Cadenas (con escapes simples). Prefijos L, u, U, u8 se pueden añadir.
    (r'(L|u8|u|U)?"(?:\\.|[^"\\])*"', TT_LITERAL_CADENA),
    (r"(L|u8|u|U)?'(?:\\.|[^'\\])*'", TT_LITERAL_CARACTER), # Caracteres (con escapes simples)
    
    # Números:
    # Hexadecimales (0x...), Binarios (0b...), Octales (0...)
    (r'0[xX][0-9a-fA-F]+[ulUL]{0,2}', TT_LITERAL_ENTERO), 
    (r'0[bB][01]+[ulUL]{0,2}', TT_LITERAL_ENTERO),    
    (r'0[0-7]*[ulUL]{0,2}', TT_LITERAL_ENTERO), # Octales (0, 01, 077) o solo 0
    # Flotantes: 1.0, .5, 1e5, 1.2E-5, 3.14f, 0.5L (con sufijos f, F, l, L)
    (r'[+-]?(\d+\.\d*|\.\d+)([eE][+-]?\d+)?[fFLl]?', TT_LITERAL_FLOTANTE),
    # Enteros decimales (con sufijos u, U, l, L, ll, LL, ul, Ul, uL, UL, ull, Ull, uLL, ULL)
    (r'[+-]?\d+([eE][+-]?\d+)?[ulUL]{0,3}', TT_LITERAL_ENTERO), 
    
    # 4. Operadores (de más largo a más corto para evitar ambigüedades)
    (r'->\*|->|\+\+|--|<<=|>>=|::', TT_OPERADOR_MIEMBRO), # :: también es operador de alcance
    (r'\.\*', TT_OPERADOR_MIEMBRO), # .* (puntero a miembro)
    (r'<=|>=|==|!=|&&|\|\|', TT_OPERADOR_COMPARACION), # &&, || son lógicos pero se agrupan aquí
    (r'\+=|-=|\*=|/=|%=|&=|\^=|\|=|<<|>>', TT_OPERADOR_ASIGNACION), # << y >> también son bitwise
    (r'[+\-*/%&|^!~<>=?:]', TT_OPERADOR_ARITMETICO), # Incluye bitwise y lógicos de un caracter, y ternario. El tipo se refinará.
                                                 # <, > también son relacionales.
                                                 # : también es delimitador.

    # 5. Delimitadores y Puntuación
    (r'\{', TT_LLAVE_IZQ), (r'\}', TT_LLAVE_DER),
    (r'\(', TT_PARENTESIS_IZQ), (r'\)', TT_PARENTESIS_DER),
    (r'\[', TT_CORCHETE_IZQ), (r'\]', TT_CORCHETE_DER),
    (r';', TT_PUNTO_Y_COMA),
    (r',', TT_COMA),
    (r'\.', TT_PUNTO), # Acceso a miembro, también parte de flotantes.

    # 6. Identificadores y Palabras Clave
    # Un identificador C++ puede empezar con letra o _, seguido de letras, números o _.
    (r'[a-zA-Z_][a-zA-Z0-9_]*', TT_IDENTIFICADOR),

    # 7. Espacios en blanco (se ignorarán pero deben ser consumidos por el lexer)
    (r'\s+', TT_WHITESPACE_CPP),
]


class LexerCPP:
    """
    Analizador Léxico para un subconjunto de C++.
    """
    def __init__(self, codigo_fuente):
        self.codigo = codigo_fuente
        self.posicion_actual = 0
        self.linea_actual = 1
        self.columna_actual = 1 

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

    def _procesar_directiva_preprocesador(self, match_directiva):
        """Procesa una directiva de preprocesador."""
        lexema_completo = match_directiva.group(0)
        nombre_directiva = match_directiva.group(1).lower() # ej. 'include', 'define'
        resto_linea = match_directiva.group(2).strip()
        
        # print(f"DEBUG Preproc: '{nombre_directiva}', Resto: '{resto_linea}'")

        if nombre_directiva in DIRECTIVAS_PREPROCESADOR_CPP:
            # Para #include, intentar extraer el nombre del archivo cabecera
            if nombre_directiva == 'include':
                match_cabecera_std = re.match(r'<\s*([^>]+)\s*>', resto_linea)
                match_cabecera_usr = re.match(r'"\s*([^"]+)\s*"', resto_linea)
                if match_cabecera_std:
                    nombre_archivo = match_cabecera_std.group(1).strip()
                    return Token(TT_DIRECTIVA_PREPROCESADOR, lexema_completo, self.linea_actual, self.columna_actual, 
                                 valor={'directiva': nombre_directiva, 'archivo': nombre_archivo, 'tipo_cabecera': TT_CABECERA_ESTANDAR})
                elif match_cabecera_usr:
                    nombre_archivo = match_cabecera_usr.group(1).strip()
                    return Token(TT_DIRECTIVA_PREPROCESADOR, lexema_completo, self.linea_actual, self.columna_actual,
                                 valor={'directiva': nombre_directiva, 'archivo': nombre_archivo, 'tipo_cabecera': TT_CABECERA_USUARIO})
                else: # No se pudo parsear el archivo de cabecera correctamente
                    return Token(TT_DIRECTIVA_PREPROCESADOR, lexema_completo, self.linea_actual, self.columna_actual,
                                 valor={'directiva': nombre_directiva, 'argumentos': resto_linea, 'error_cabecera': True})
            else: # Otras directivas
                return Token(TT_DIRECTIVA_PREPROCESADOR, lexema_completo, self.linea_actual, self.columna_actual,
                             valor={'directiva': nombre_directiva, 'argumentos': resto_linea})
        else: # No es una directiva conocida, pero empieza con #
            return Token(TT_ERROR_CPP, lexema_completo, self.linea_actual, self.columna_actual,
                         valor=f"Directiva de preprocesador desconocida: '{nombre_directiva}'")


    def tokenizar(self):
        tokens = []
        while self.posicion_actual < len(self.codigo):
            match_encontrado_en_iteracion = False
            linea_inicio_token = self.linea_actual
            col_inicio_token = self.columna_actual

            # Manejo especial para directivas de preprocesador al inicio de una línea (después de espacios opcionales)
            # Esto es una simplificación; un preprocesador real es más complejo.
            subcadena_actual = self.codigo[self.posicion_actual:]
            match_espacios_inicio_linea = re.match(r'^[ \t]*', subcadena_actual)
            pos_despues_espacios = self.posicion_actual + len(match_espacios_inicio_linea.group(0))

            if pos_despues_espacios < len(self.codigo) and self.codigo[pos_despues_espacios] == '#':
                # Potencial directiva de preprocesador
                # Usar la especificación de TT_DIRECTIVA_PREPROCESADOR
                patron_directiva_regex, tipo_directiva = ESPECIFICACIONES_TOKEN_CPP[0] # Asumiendo que es la primera
                if tipo_directiva == TT_DIRECTIVA_PREPROCESADOR:
                    # Aplicar el regex desde la posición después de los espacios iniciales
                    match_dir = re.match(patron_directiva_regex, self.codigo[pos_despues_espacios:])
                    if match_dir:
                        # Consumir los espacios iniciales
                        self._avanzar(len(match_espacios_inicio_linea.group(0))) 
                        # El token de directiva se crea y consume dentro de _procesar_directiva
                        token_directiva = self._procesar_directiva_preprocesador(match_dir)
                        tokens.append(token_directiva)
                        self._avanzar(len(match_dir.group(0))) # Avanzar por el resto de la directiva
                        match_encontrado_en_iteracion = True
                        continue # Volver al inicio del bucle while

            # Si no es una directiva, proceder con las especificaciones normales
            for patron_regex, tipo_token_base in ESPECIFICACIONES_TOKEN_CPP:
                if tipo_token_base == TT_DIRECTIVA_PREPROCESADOR: # Ya manejado arriba
                    continue

                match = re.match(patron_regex, self.codigo[self.posicion_actual:])
                
                if match:
                    lexema = match.group(0)
                    match_encontrado_en_iteracion = True
                    
                    if tipo_token_base == TT_WHITESPACE_CPP or \
                       tipo_token_base == TT_COMENTARIO_LINEA or \
                       tipo_token_base == TT_COMENTARIO_BLOQUE:
                        self._avanzar(len(lexema))
                        break 

                    tipo_token_final = tipo_token_base
                    valor_final = lexema 

                    if tipo_token_base == TT_IDENTIFICADOR:
                        if lexema in PALABRAS_CLAVE_CPP: # C++ es sensible a mayúsculas/minúsculas
                            tipo_token_final = TT_PALABRA_CLAVE
                            if lexema == 'true': valor_final = True
                            elif lexema == 'false': valor_final = False
                            elif lexema == 'nullptr': valor_final = None # O un objeto especial
                        elif lexema.startswith('[') and lexema.endswith(']'): # Identificador delimitado
                            valor_final = lexema[1:-1]
                        elif lexema.startswith('"') and lexema.endswith('"'): # Identificador delimitado
                             valor_final = lexema[1:-1]
                    
                    elif tipo_token_base == TT_LITERAL_CADENA:
                        # Quitar comillas y procesar escapes. Esto es una simplificación.
                        # También manejar prefijos L, u8, u, U y R"()"
                        if lexema.startswith('R"'): # Raw string
                            # Extraer el delimitador y el contenido
                            match_raw = re.match(r'R"([^\s()\\\t\n\r]*)\(([\s\S]*?)\)\1"', lexema)
                            if match_raw:
                                valor_final = match_raw.group(2)
                        else: # Cadena normal o con prefijo L, u8, u, U
                            prefijo_match = re.match(r'^(L|u8|u|U)?(".*")', lexema)
                            cadena_real = prefijo_match.group(2) if prefijo_match else lexema
                            valor_final = cadena_real[1:-1] 
                            # Aquí iría un manejo de secuencias de escape más robusto
                            valor_final = valor_final.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace("\\'", "'").replace('\\\\', '\\')
                    
                    elif tipo_token_base == TT_LITERAL_CARACTER:
                        valor_final = lexema[1:-1] # Quitar comillas simples
                        # Manejar escapes: '\n', '\\', '\'', '\"', '\xHH', '\OOO'
                        if valor_final.startswith('\\'):
                            if valor_final == '\\n': valor_final = '\n'
                            elif valor_final == '\\t': valor_final = '\t'
                            # Añadir más escapes
                    
                    elif tipo_token_base == TT_LITERAL_ENTERO:
                        try:
                            if lexema.lower().startswith('0x'): valor_final = int(lexema, 16)
                            elif lexema.lower().startswith('0b'): valor_final = int(lexema, 2)
                            elif lexema.startswith('0') and len(lexema) > 1 and lexema[1] in '01234567': valor_final = int(lexema, 8)
                            else: valor_final = int(lexema)
                        except ValueError:
                            tipo_token_final = TT_ERROR_CPP
                            valor_final = f"Literal entero inválido: {lexema}"
                    
                    elif tipo_token_base == TT_LITERAL_FLOTANTE:
                        try:
                            valor_final = float(lexema.rstrip('fFlL')) # Quitar sufijos f/F/l/L antes de convertir
                        except ValueError:
                            tipo_token_final = TT_ERROR_CPP
                            valor_final = f"Literal flotante inválido: {lexema}"
                    
                    # Refinar tipos de operadores (esto es opcional, el parser puede hacerlo)
                    elif tipo_token_base == TT_OPERADOR_ARITMETICO:
                        if lexema in ['&&', '||', '!']: tipo_token_final = TT_OPERADOR_LOGICO
                        elif lexema in ['&', '|', '^', '~']: tipo_token_final = TT_OPERADOR_BITWISE
                        elif lexema in ['<', '>', '<=', '>=', '==', '!=']: tipo_token_final = TT_OPERADOR_COMPARACION
                        elif lexema == '=' or lexema.endswith('='): # =, +=, -= etc.
                             if lexema != '=' and not lexema in ['==', '!=', '<=', '>=']: # Evitar reclasificar ==, !=, <=, >=
                                tipo_token_final = TT_OPERADOR_ASIGNACION
                        elif lexema == '?': tipo_token_final = TT_OPERADOR_TERNARIO
                        elif lexema == ':': tipo_token_final = TT_DOS_PUNTOS # Podría ser ternario o etiqueta/alcance

                    elif tipo_token_base == TT_OPERADOR_MIEMBRO:
                        if lexema == '::': tipo_token_final = TT_OPERADOR_MIEMBRO # Específicamente resolución de alcance
                        # . y -> ya son TT_OPERADOR_MIEMBRO
                    
                    tokens.append(Token(tipo_token_final, lexema, linea_inicio_token, col_inicio_token, valor_final))
                    self._avanzar(len(lexema))
                    break 
            
            if not match_encontrado_en_iteracion and self.posicion_actual < len(self.codigo):
                caracter_erroneo = self.codigo[self.posicion_actual]
                tokens.append(Token(TT_ERROR_CPP, caracter_erroneo, linea_inicio_token, col_inicio_token,
                                    valor=f"Carácter no reconocido: '{caracter_erroneo}'"))
                self._avanzar() 

        tokens.append(Token(TT_EOF_CPP, "EOF", self.linea_actual, self.columna_actual))
        return tokens

# (Fin de la clase LexerCPP)
