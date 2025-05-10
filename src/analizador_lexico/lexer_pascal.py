# src/analizador_lexico/lexer_pascal.py
import re

class Token: # Definición local de Token para este lexer
    def __init__(self, tipo, lexema, linea, columna, valor=None):
        self.tipo = tipo
        self.lexema = lexema
        self.linea = linea
        self.columna = columna
        self.valor = valor if valor is not None else lexema

    def __repr__(self):
        lexema_display = self.lexema.replace('\n', '\\n').replace('\r', '\\r')
        valor_display = str(self.valor).replace('\n', '\\n').replace('\r', '\\r')
        return f"Token({self.tipo}, '{lexema_display}', L{self.linea}:C{self.columna}" + \
               (f", V:'{valor_display}'" if self.valor != self.lexema else "") + ")"

# Tipos de Token para Pascal
TT_PALABRA_RESERVADA = 'PALABRA_RESERVADA'
TT_IDENTIFICADOR = 'IDENTIFICADOR'
TT_NUMERO_ENTERO = 'NUMERO_ENTERO'
TT_NUMERO_REAL = 'NUMERO_REAL'
TT_CADENA_LITERAL = 'CADENA_LITERAL' # Ej: 'Hola mundo'

TT_OPERADOR_ASIGNACION = 'OPERADOR_ASIGNACION' # :=
TT_OPERADOR_RELACIONAL = 'OPERADOR_RELACIONAL' # =, <>, <, >, <=, >=
TT_OPERADOR_ARITMETICO = 'OPERADOR_ARITMETICO' # +, -, *, /
TT_OPERADOR_LOGICO = 'OPERADOR_LOGICO'     # AND, OR, NOT (a veces como palabras reservadas)

TT_DELIMITADOR = 'DELIMITADOR'     # ( ) [ ] , ; . .. :
TT_PUNTO = 'PUNTO'                 # . (puede ser parte de '..' o fin de programa)
TT_DOS_PUNTOS = 'DOS_PUNTOS'       # : (para declaración de tipo)
TT_PUNTO_Y_COMA = 'PUNTO_Y_COMA'   # ;
TT_COMA = 'COMA'                   # ,
TT_PARENTESIS_IZQ = 'PARENTESIS_IZQ' # (
TT_PARENTESIS_DER = 'PARENTESIS_DER' # )
TT_CORCHETE_IZQ = 'CORCHETE_IZQ'   # [
TT_CORCHETE_DER = 'CORCHETE_DER'   # ]
TT_SUBRANGO = 'SUBRANGO'           # .. (dos puntos)

TT_COMENTARIO = 'COMENTARIO'       # { ... } o (* ... *)
TT_EOF_PASCAL = 'EOF_PASCAL'
TT_ERROR_PASCAL = 'ERROR_PASCAL'
TT_WHITESPACE_PASCAL = 'WHITESPACE_PASCAL' # Espacios, tabs, nuevas líneas

# Palabras reservadas de Pascal (insensible a mayúsculas/minúsculas)
# Usaremos un subconjunto para empezar.
PALABRAS_RESERVADAS_PASCAL = {
    'program', 'var', 'const', 'type', 'array', 'of', 'record', 'file',
    'begin', 'end',
    'if', 'then', 'else',
    'for', 'to', 'downto', 'do', 'while', 'repeat', 'until',
    'function', 'procedure', 'uses',
    'integer', 'real', 'char', 'string', 'boolean',
    'true', 'false', 'nil',
    'and', 'or', 'not', 'in', 'set',
    'case', 'with', 'goto', 'label',
    # Comandos simples comunes para simulación
    'writeln', 'write', 'readln', 'read'
}




# Especificaciones de los tokens para Pascal: (expresión_regular, TIPO_TOKEN)
# El orden es importante para evitar coincidencias incorrectas.
ESPECIFICACIONES_TOKEN_PASCAL = [
    # Comentarios (manejar ambos tipos, deben ir primero)
    # Comentario tipo llave: { ... } (no anidado simple)
    (r'\{[^{}]*?\}',             TT_COMENTARIO),
    # Comentario tipo paréntesis-asterisco: (* ... *) (puede ser multilínea)
    (r'\(\*[\s\S]*?\*\)',        TT_COMENTARIO),

    # Nueva línea (se tratará como whitespace)
    (r'\n',                      TT_WHITESPACE_PASCAL),
    # Espacios y tabs (se tratarán como whitespace)
    (r'[ \t]+',                  TT_WHITESPACE_PASCAL),

    # Cadenas literales (entre comillas simples, '' para una comilla simple dentro)
    (r"'([^']|'')*?'",           TT_CADENA_LITERAL),

    # Números
    # Reales: deben tener dígitos después del punto, o un exponente.
    # Ej: 1.23, 0.45, 123.0, 1e-5, 3.14E+10
    # Este regex intenta capturar varias formas de reales.
    (r'\d+\.\d+([eE][-+]?\d+)?',  TT_NUMERO_REAL),
    (r'\d+[eE][-+]?\d+',         TT_NUMERO_REAL), # Ej: 12e3, 1E-2 (sin punto decimal pero con exponente)
    # Enteros
    (r'\d+',                     TT_NUMERO_ENTERO),

    # Operadores y delimitadores (los más largos o específicos primero)
    (r':=',                      TT_OPERADOR_ASIGNACION),
    (r'<>',                      TT_OPERADOR_RELACIONAL),
    (r'<=',                      TT_OPERADOR_RELACIONAL),
    (r'>=',                      TT_OPERADOR_RELACIONAL),
    (r'\.\.',                    TT_SUBRANGO), # Dos puntos para subrangos

    # Delimitadores y operadores de un solo carácter
    (r'\+',                      TT_OPERADOR_ARITMETICO),
    (r'-',                       TT_OPERADOR_ARITMETICO),
    (r'\*',                      TT_OPERADOR_ARITMETICO),
    (r'/',                       TT_OPERADOR_ARITMETICO), # División real
    (r'div',                     TT_OPERADOR_ARITMETICO),
    (r'mod',                     TT_OPERADOR_ARITMETICO),
    (r'=',                       TT_OPERADOR_RELACIONAL),
    (r'<',                       TT_OPERADOR_RELACIONAL),
    (r'>',                       TT_OPERADOR_RELACIONAL),
    (r'\(',                      TT_PARENTESIS_IZQ),
    (r'\)',                      TT_PARENTESIS_DER),
    (r'\[',                      TT_CORCHETE_IZQ),
    (r'\]',                      TT_CORCHETE_DER),
    (r',',                       TT_COMA),
    (r';',                       TT_PUNTO_Y_COMA),
    (r':',                       TT_DOS_PUNTOS), # Para declaración de tipos, etc.
    (r'\.',                      TT_PUNTO),      # Fin de programa o acceso a campos de record
    (r'\^',                      TT_DELIMITADOR), # Para punteros (aunque no lo usemos mucho en el subconjunto)

    # Identificadores (deben ir después de operadores y otros símbolos para evitar que consuman partes de ellos)
    # Pascal es insensible a mayúsculas/minúsculas para identificadores y palabras clave.
    # El regex captura la forma, luego la lógica del lexer manejará la insensibilidad.
    (r'[a-zA-Z][a-zA-Z0-9_]*',   TT_IDENTIFICADOR),
]

# La clase LexerPascal vendrá después.

# (Continuación, después de ESPECIFICACIONES_TOKEN_PASCAL)

class LexerPascal:
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
                    self.columna_actual = 1 # Resetear columna al inicio de nueva línea
                else:
                    self.columna_actual += 1
                self.posicion_actual += 1
            else:
                break 

    def _peek(self, cantidad=1):
        if self.posicion_actual + cantidad <= len(self.codigo):
            return self.codigo[self.posicion_actual : self.posicion_actual + cantidad]
        elif self.posicion_actual < len(self.codigo):
            return self.codigo[self.posicion_actual:]
        return None

    def tokenizar(self):
        tokens = []
        while self.posicion_actual < len(self.codigo):
            match_encontrado = None
            token_generado_esta_iteracion = False

            # Guardar posición de inicio para el token actual
            linea_inicio_token = self.linea_actual
            col_inicio_token = self.columna_actual

            for patron_regex, tipo_token_base in ESPECIFICACIONES_TOKEN_PASCAL:
                # Compilar el regex para la opción de insensibilidad a mayúsculas/minúsculas si es necesario
                # Para Pascal, las palabras clave e identificadores son insensibles.
                # Los literales de cadena SÍ son sensibles.
                # Los regex para símbolos y números son inherentemente insensibles o no aplica.
                
                # La insensibilidad para palabras clave se manejará después de identificar un IDENTIFICADOR.
                # El regex para IDENTIFICADOR ([a-zA-Z]...) ya captura ambas cajas.
                
                regex_compilado = re.compile(patron_regex) # No necesitamos re.IGNORECASE para la mayoría aquí
                match = regex_compilado.match(self.codigo, self.posicion_actual)

                if match:
                    lexema = match.group(0)
                    match_encontrado = True # Marcamos que algo coincidió
                    token_generado_esta_iteracion = True # Un token (o whitespace/comentario) se procesó

                    # Si el token es WHITESPACE o COMENTARIO, lo omitimos y continuamos
                    if tipo_token_base == TT_WHITESPACE_PASCAL or tipo_token_base == TT_COMENTARIO:
                        self._avanzar(len(lexema)) # Avanzar la posición
                        # Reiniciar el bucle interno para buscar el siguiente token desde la nueva posición
                        break # Sale del for de ESPECIFICACIONES_TOKEN, vuelve al while

                    tipo_token_final = tipo_token_base
                    valor_final = lexema # Valor por defecto es el lexema

                    if tipo_token_base == TT_IDENTIFICADOR:
                        # Pascal es insensible a mayúsculas/minúsculas para palabras reservadas e identificadores
                        if lexema.lower() in PALABRAS_RESERVADAS_PASCAL:
                            tipo_token_final = TT_PALABRA_RESERVADA
                        # El lexema se guarda tal como está en el código, pero el valor podría normalizarse
                        # o simplemente usar el lexema. Para identificadores, el lexema es el valor.
                    
                    elif tipo_token_base == TT_NUMERO_ENTERO:
                        valor_final = int(lexema)
                    
                    elif tipo_token_base == TT_NUMERO_REAL:
                        # Pascal puede usar 'E' o 'e'. El float() de Python maneja esto.
                        valor_final = float(lexema)
                    
                    elif tipo_token_base == TT_CADENA_LITERAL:
                        # Quitar comillas simples de inicio/fin y reemplazar '' por '
                        valor_final = lexema[1:-1].replace("''", "'")
                    
                    tokens.append(Token(tipo_token_final, lexema, linea_inicio_token, col_inicio_token, valor_final))
                    self._avanzar(len(lexema))
                    break # Sale del for de ESPECIFICACIONES_TOKEN, vuelve al while
            
            if not match_encontrado and self.posicion_actual < len(self.codigo):
                # Si no hubo coincidencia y no hemos llegado al final, es un error léxico.
                caracter_erroneo = self.codigo[self.posicion_actual]
                tokens.append(Token(TT_ERROR_PASCAL, caracter_erroneo, linea_inicio_token, col_inicio_token, 
                                    valor=f"Carácter no reconocido: '{caracter_erroneo}'"))
                self._avanzar() # Avanzar para evitar bucle infinito
                token_generado_esta_iteracion = True # Se generó un token de error
            
            # Si en una iteración del while no se generó ningún token ni se avanzó (ej. error no avanzó),
            # podríamos tener un bucle infinito.
            # La lógica actual con 'break' en el for y el manejo de error con _avanzar() debería prevenirlo.
            if not token_generado_esta_iteracion and self.posicion_actual < len(self.codigo):
                # Esto no debería ocurrir si la lógica de error avanza.
                # Como salvaguarda, avanzar para evitar bucles si algo muy raro pasa.
                print(f"Advertencia: LexerPascal en posible bucle, carácter: '{self.codigo[self.posicion_actual]}'. Avanzando forzosamente.")
                self._avanzar()


        # Añadir token EOF al final de la lista de tokens
        tokens.append(Token(TT_EOF_PASCAL, "EOF", self.linea_actual, self.columna_actual))
        return tokens

# Fin de la clase LexerPascal