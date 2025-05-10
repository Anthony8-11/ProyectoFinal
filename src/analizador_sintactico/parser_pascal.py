# src/analizador_sintactico/parser_pascal.py

# Es crucial importar los tipos de token desde nuestro lexer de Pascal
# para que el parser sepa qué esperar.
try:
    from analizador_lexico.lexer_pascal import (
        TT_PALABRA_RESERVADA, TT_IDENTIFICADOR, TT_NUMERO_ENTERO, TT_NUMERO_REAL,
        TT_CADENA_LITERAL, TT_OPERADOR_ASIGNACION, TT_OPERADOR_RELACIONAL, # Añadir más si son necesarios
        TT_OPERADOR_ARITMETICO, TT_PUNTO_Y_COMA, TT_DOS_PUNTOS, TT_PUNTO, TT_COMA,
        TT_PARENTESIS_IZQ, TT_PARENTESIS_DER, TT_CORCHETE_IZQ, TT_CORCHETE_DER, TT_EOF_PASCAL
        # Importar todos los TT_ que se usarán en las reglas de _consumir
    )
    # Importar la clase Token si se va a usar para type hinting o inspección
    from analizador_lexico.lexer_pascal import Token 
except ImportError:
    # Fallback simple si hay problemas con la importación (no ideal para producción)
    print("ADVERTENCIA: No se pudieron importar los tipos de token de LexerPascal.")
    print("El ParserPascal podría no funcionar correctamente.")
    # Definir placeholders para que el archivo al menos cargue
    TT_PALABRA_RESERVADA, TT_IDENTIFICADOR, TT_EOF_PASCAL = "PALABRA_RESERVADA", "IDENTIFICADOR", "EOF_PASCAL"
    TT_PUNTO_Y_COMA, TT_PUNTO, TT_DOS_PUNTOS = "PUNTO_Y_COMA", "PUNTO", "DOS_PUNTOS"
    TT_OPERADOR_ASIGNACION = "OPERADOR_ASIGNACION"
    TT_PARENTESIS_IZQ, TT_PARENTESIS_DER, TT_COMA = "PARENTESIS_IZQ", "PARENTESIS_DER", "COMA"
    TT_NUMERO_ENTERO, TT_NUMERO_REAL, TT_CADENA_LITERAL = "NUMERO_ENTERO", "NUMERO_REAL", "CADENA_LITERAL"
    pass

# NUEVA IMPORTACIÓN para la Tabla de Símbolos
try:
    from nucleo_compilador.tabla_simbolos import TablaSimbolos
except ImportError:
    print("ADVERTENCIA CRÍTICA: No se pudo importar TablaSimbolos. El análisis semántico no funcionará.")
    # Un placeholder simple para que el parser no falle inmediatamente si no se encuentra TablaSimbolos
    class TablaSimbolos:
        def __init__(self): self.simbolos = {}
        def agregar_simbolo(self, *args, **kwargs): pass
        def buscar_simbolo(self, *args, **kwargs): return None
        def entrar_alcance(self): pass
        def salir_alcance(self): pass



# --- Definiciones de Nodos del AST para Pascal ---
# Cada clase representa un tipo de construcción en el lenguaje.

# --- Definiciones de Nodos del AST para Pascal ---
# Cada clase representa un tipo de construcción en el lenguaje.
# Los métodos __repr__ están diseñados para ofrecer una visualización
# legible de la estructura del árbol AST.

class NodoAST:
    """Clase base para todos los nodos del AST."""
    def __repr__(self, indent=0):
        # Representación base que muestra el nombre de la clase y su ID.
        # La indentación se controla con espacios.
        indent_str = "  " * indent 
        return f"{indent_str}{self.__class__.__name__}(id={id(self)})"

class NodoPrograma(NodoAST):
    """Representa la estructura completa de un programa Pascal."""
    def __init__(self, nombre_programa_token, bloque_nodo):
        self.nombre_programa_token = nombre_programa_token
        self.bloque_nodo = bloque_nodo

    def __repr__(self, indent=0):
        indent_str = "  " * indent
        # El bloque hijo se imprime con un nivel más de indentación.
        bloque_repr = self.bloque_nodo.__repr__(indent + 1) if self.bloque_nodo else f"{indent_str}  None"
        return (f"{indent_str}NodoPrograma(nombre='{self.nombre_programa_token.lexema}',\n"
                f"{bloque_repr}\n"
                f"{indent_str})")

class NodoBloque(NodoAST):
    """Representa un bloque de código con declaraciones y un cuerpo de sentencias."""
    def __init__(self, declaraciones_var_nodo, cuerpo_nodo):
        self.declaraciones_var_nodo = declaraciones_var_nodo
        self.cuerpo_nodo = cuerpo_nodo

    def __repr__(self, indent=0):
        indent_str = "  " * indent
        # Las declaraciones y el cuerpo se imprimen con mayor indentación.
        decls_repr = self.declaraciones_var_nodo.__repr__(indent + 1) if self.declaraciones_var_nodo else f"{indent_str}  Declaraciones: None"
        cuerpo_repr = self.cuerpo_nodo.__repr__(indent + 1) if self.cuerpo_nodo else f"{indent_str}  Cuerpo: None"
        return (f"{indent_str}NodoBloque(\n"
                f"{decls_repr},\n"
                f"{cuerpo_repr}\n"
                f"{indent_str})")

class NodoDeclaracionesVar(NodoAST):
    """Contiene una lista de nodos NodoDeclaracionVar."""
    def __init__(self, declaraciones):
        self.declaraciones = declaraciones

    def __repr__(self, indent=0):
        indent_str = "  " * indent
        if not self.declaraciones:
            return f"{indent_str}NodoDeclaracionesVar: []"
        
        # Cada declaración de variable se imprime en una nueva línea con mayor indentación.
        decls_items_repr = "\n".join([decl.__repr__(indent + 1) for decl in self.declaraciones])
        return (f"{indent_str}NodoDeclaracionesVar: [\n"
                f"{decls_items_repr}\n"
                f"{indent_str}]")

class NodoDeclaracionVar(NodoAST):
    """Representa una única línea de declaración de variable (ej: a, b : integer;)."""
    def __init__(self, lista_identificadores_tokens, tipo_nodo):
        self.lista_identificadores_tokens = lista_identificadores_tokens
        self.tipo_nodo = tipo_nodo

    def __repr__(self, indent=0):
        indent_str = "  " * indent
        nombres_var = [t.lexema for t in self.lista_identificadores_tokens]
        # El tipo se imprime con mayor indentación.
        tipo_repr = self.tipo_nodo.__repr__(indent + 1) if self.tipo_nodo else f"{indent_str}  Tipo: None"
        return (f"{indent_str}NodoDeclaracionVar(nombres={nombres_var},\n"
                f"{tipo_repr}\n"
                f"{indent_str})")

class NodoTipo(NodoAST):
    """Representa un tipo de dato en Pascal."""
    def __init__(self, tipo_token):
        self.tipo_token = tipo_token
        self.nombre_tipo = tipo_token.lexema.lower()
        self.tamaño = None

    def __repr__(self, indent=0):
        indent_str = "  " * indent
        return f"{indent_str}NodoTipo(nombre='{self.nombre_tipo}'" + (f", tamaño={self.tamaño}" if self.tamaño is not None else "") + ")"

class NodoCuerpoPrograma(NodoAST): # También para bloques begin-end anidados
    """Representa un bloque 'begin ... end' con una lista de sentencias."""
    def __init__(self, lista_sentencias_nodos):
        self.lista_sentencias_nodos = lista_sentencias_nodos

    def __repr__(self, indent=0):
        indent_str = "  " * indent
        if not self.lista_sentencias_nodos:
            return f"{indent_str}NodoCuerpoPrograma(sentencias=[])"
            
        # Cada sentencia se imprime en una nueva línea con mayor indentación.
        sentencias_items_repr = "\n".join([sent.__repr__(indent + 1) for sent in self.lista_sentencias_nodos])
        return (f"{indent_str}NodoCuerpoPrograma(sentencias=[\n"
                f"{sentencias_items_repr}\n"
                f"{indent_str}])")

class NodoSentencia(NodoAST):
    """Clase base para todas las sentencias."""
    # Hereda __repr__ de NodoAST si no se redefine en clases hijas.
    pass

class NodoAsignacion(NodoSentencia):
    """Representa una sentencia de asignación (variable := expresion)."""
    def __init__(self, variable_token_id, expresion_nodo):
        self.variable_token_id = variable_token_id
        self.expresion_nodo = expresion_nodo

    def __repr__(self, indent=0):
        indent_str = "  " * indent
        # La expresión se imprime con mayor indentación.
        expr_repr = self.expresion_nodo.__repr__(indent + 1) if self.expresion_nodo else f"{indent_str}  Expresion: None"
        return (f"{indent_str}NodoAsignacion(variable='{self.variable_token_id.lexema}',\n"
                f"{expr_repr}\n"
                f"{indent_str})")

class NodoLlamadaProcedimiento(NodoSentencia):
    """Representa una llamada a un procedimiento."""
    def __init__(self, nombre_proc_token, argumentos_nodos):
        self.nombre_proc_token = nombre_proc_token
        self.argumentos_nodos = argumentos_nodos

    def __repr__(self, indent=0):
        indent_str = "  " * indent
        if not self.argumentos_nodos:
            args_repr = "[]"
        else:
            # Cada argumento se imprime en una nueva línea con mayor indentación.
            args_items_repr = "\n".join([arg.__repr__(indent + 2) for arg in self.argumentos_nodos]) # Nivel +2 para argumentos
            args_repr = f"[\n{args_items_repr}\n{indent_str}  ]" # Cierre del corchete con indentación +1
        
        return (f"{indent_str}NodoLlamadaProcedimiento(nombre='{self.nombre_proc_token.lexema}',\n"
                f"{indent_str}  argumentos={args_repr}\n"
                f"{indent_str})")

class NodoIf(NodoSentencia):
    """Representa una sentencia condicional if-then-else."""
    def __init__(self, condicion_nodo, then_sentencia_nodo, else_sentencia_nodo=None):
        self.condicion_nodo = condicion_nodo
        self.then_sentencia_nodo = then_sentencia_nodo
        self.else_sentencia_nodo = else_sentencia_nodo

    def __repr__(self, indent=0):
        indent_str = "  " * indent
        # Condición, rama 'then' y rama 'else' (opcional) se imprimen con mayor indentación.
        cond_repr = self.condicion_nodo.__repr__(indent + 1) if self.condicion_nodo else f"{indent_str}  Condicion: None"
        then_repr = self.then_sentencia_nodo.__repr__(indent + 1) if self.then_sentencia_nodo else f"{indent_str}  Then: None"
        
        repr_str = (f"{indent_str}NodoIf(\n"
                    f"{indent_str}  condicion=\n{cond_repr},\n"
                    f"{indent_str}  then=\n{then_repr}")
        
        if self.else_sentencia_nodo:
            else_repr = self.else_sentencia_nodo.__repr__(indent + 1)
            repr_str += f",\n{indent_str}  else=\n{else_repr}"
        
        repr_str += f"\n{indent_str})"
        return repr_str
    
class NodoWhile(NodoSentencia):
    """Representa una sentencia de bucle 'while ... do ...'."""
    def __init__(self, condicion_nodo, cuerpo_sentencia_nodo):
        self.condicion_nodo = condicion_nodo           # Nodo de la expresión booleana (condición del bucle).
        self.cuerpo_sentencia_nodo = cuerpo_sentencia_nodo # Nodo de la sentencia que forma el cuerpo del bucle.

    def __repr__(self, indent=0):
        indent_str = "  " * indent
        # Representación de una sentencia while.
        cond_repr = self.condicion_nodo.__repr__(indent + 1) if self.condicion_nodo else f"{indent_str}  Condicion: None"
        cuerpo_repr = self.cuerpo_sentencia_nodo.__repr__(indent + 1) if self.cuerpo_sentencia_nodo else f"{indent_str}  Cuerpo: None"
        return (f"{indent_str}NodoWhile(\n"
                f"{indent_str}  condicion=\n{cond_repr},\n"
                f"{indent_str}  cuerpo=\n{cuerpo_repr}\n"
                f"{indent_str})")
    
class NodoRepeat(NodoSentencia):
    """Representa una sentencia de bucle 'repeat ... until ...'."""
    def __init__(self, lista_sentencias_cuerpo, condicion_nodo):
        # El cuerpo de un repeat-until es una lista de sentencias.
        self.lista_sentencias_cuerpo = lista_sentencias_cuerpo # Lista de nodos de sentencia.
        self.condicion_nodo = condicion_nodo                 # Nodo de la expresión booleana (condición de terminación).

    def __repr__(self, indent=0):
        indent_str = "  " * indent
        # Representación de una sentencia repeat-until.
        if not self.lista_sentencias_cuerpo:
            cuerpo_repr = f"{indent_str}  Cuerpo: []"
        else:
            cuerpo_items_repr = "\n".join([sent.__repr__(indent + 2) for sent in self.lista_sentencias_cuerpo])
            cuerpo_repr = (f"{indent_str}  Cuerpo: [\n{cuerpo_items_repr}\n"
                           f"{indent_str}  ]")
        
        cond_repr = self.condicion_nodo.__repr__(indent + 1) if self.condicion_nodo else f"{indent_str}  Condicion: None"
        
        return (f"{indent_str}NodoRepeat(\n"
                f"{cuerpo_repr},\n"
                f"{indent_str}  until_condicion=\n{cond_repr}\n"
                f"{indent_str})")

class NodoExpresion(NodoAST):
    """Clase base para todas las expresiones."""
    # Hereda __repr__ de NodoAST.
    pass

class NodoIdentificador(NodoExpresion):
    """Representa un identificador usado en una expresión."""
    def __init__(self, id_token):
        self.id_token = id_token
        self.nombre = id_token.lexema

    def __repr__(self, indent=0):
        indent_str = "  " * indent
        return f"{indent_str}NodoIdentificador(nombre='{self.nombre}')"

class NodoLiteral(NodoExpresion):
    """Representa un valor literal (número, cadena, booleano)."""
    def __init__(self, literal_token):
        self.literal_token = literal_token
        self.valor = literal_token.valor 

    def __repr__(self, indent=0):
        indent_str = "  " * indent
        # Usar repr(self.valor) para que las cadenas se muestren entre comillas.
        return f"{indent_str}NodoLiteral(tipo={self.literal_token.tipo}, valor={repr(self.valor)})"

class NodoExpresionBinaria(NodoExpresion):
    """Representa una expresión binaria (ej: operando_izq operador operando_der)."""
    def __init__(self, operador_token, operando_izq_nodo, operando_der_nodo):
        self.operador_token = operador_token
        self.operando_izq_nodo = operando_izq_nodo
        self.operando_der_nodo = operando_der_nodo

    def __repr__(self, indent=0):
        indent_str = "  " * indent
        # Operandos izquierdo y derecho se imprimen con mayor indentación.
        izq_repr = self.operando_izq_nodo.__repr__(indent + 1) if self.operando_izq_nodo else f"{indent_str}  Izquierda: None"
        der_repr = self.operando_der_nodo.__repr__(indent + 1) if self.operando_der_nodo else f"{indent_str}  Derecha: None"
        return (f"{indent_str}NodoExpresionBinaria(operador='{self.operador_token.lexema}',\n"
                f"{izq_repr},\n"
                f"{der_repr}\n"
                f"{indent_str})")
    
class NodoExpresionUnaria(NodoExpresion):
    """Representa una expresión unaria (ej: 'not' operando)."""
    def __init__(self, operador_token, operando_nodo):
        self.operador_token = operador_token # Token del operador unario (ej: 'not').
        self.operando_nodo = operando_nodo   # Nodo de la expresión sobre la que opera.

    def __repr__(self, indent=0):
        indent_str = "  " * indent
        # Representación de una expresión unaria.
        op_repr = self.operando_nodo.__repr__(indent + 1) if self.operando_nodo else f"{indent_str}  Operando: None"
        return (f"{indent_str}NodoExpresionUnaria(operador='{self.operador_token.lexema}',\n"
                f"{op_repr}\n"
                f"{indent_str})")

# --- Fin de Definiciones de Nodos del AST ---



class ParserPascal:
    def __init__(self, tokens):
        self.tokens = [token for token in tokens if token.tipo != 'WHITESPACE_PASCAL'] # Ignorar whitespace
        self.posicion_actual = 0
        self.token_actual = self.tokens[self.posicion_actual] if self.tokens else None
        self.errores_sintacticos = []
        self.tabla_simbolos = TablaSimbolos()
        print(f"[DEBUG Parser.__init__] id(self.tabla_simbolos) = {id(self.tabla_simbolos)}")
        if self.tabla_simbolos.alcances: # Asegurarse que alcances existe y no está vacío
            print(f"[DEBUG Parser.__init__] id(self.tabla_simbolos.alcances) = {id(self.tabla_simbolos.alcances)}")
            print(f"[DEBUG Parser.__init__] id(self.tabla_simbolos.alcances[0]) = {id(self.tabla_simbolos.alcances[0])}")
        else:
            print("[DEBUG Parser.__init__] self.tabla_simbolos.alcances está vacío o no inicializado.")

    def _avanzar(self):
        """Avanza al siguiente token en la lista."""
        self.posicion_actual += 1
        if self.posicion_actual < len(self.tokens):
            self.token_actual = self.tokens[self.posicion_actual]


        else:
            # Si hemos avanzado más allá del último token real (que debería ser EOF),
            # establecemos token_actual a un valor que indique el final.
            # Podríamos usar el mismo token EOF si está al final, o None.
            self.token_actual = self.tokens[-1] if self.tokens and self.tokens[-1].tipo == TT_EOF_PASCAL else None


    def _error_sintactico(self, mensaje_esperado):
        """Registra un error sintáctico y lanza una excepción para detener el parsing."""
        if self.token_actual and self.token_actual.tipo != TT_EOF_PASCAL:
            mensaje = (f"Error Sintáctico en L{self.token_actual.linea}:C{self.token_actual.columna}. "
                       f"Se esperaba {mensaje_esperado}, pero se encontró '{self.token_actual.lexema}' (tipo: {self.token_actual.tipo}).")
        elif self.token_actual and self.token_actual.tipo == TT_EOF_PASCAL:
            mensaje = (f"Error Sintáctico: Final inesperado del archivo (L{self.token_actual.linea}:C{self.token_actual.columna}). "
                       f"Se esperaba {mensaje_esperado}.")
        else: # No hay más tokens, pero se esperaba algo
            # Intentar obtener la posición del último token antes del EOF
            last_token = self.tokens[-2] if len(self.tokens) > 1 else (self.tokens[-1] if self.tokens else None)
            linea_aprox = last_token.linea if last_token else 'desconocida'
            col_aprox = last_token.columna if last_token else 'desconocida'
            mensaje = (f"Error Sintáctico: Final inesperado de la entrada (aprox. L{linea_aprox}:C{col_aprox}). "
                       f"Se esperaba {mensaje_esperado}.")

        self.errores_sintacticos.append(mensaje)
        print(mensaje) # Imprimir para depuración inmediata
        raise SyntaxError(mensaje) # Detener el parsing en el primer error

    def _consumir(self, tipo_token_esperado, lexema_esperado=None, error_si_no_coincide=True):
        """
        Verifica el token actual. Si coincide, lo consume y avanza. Si no, reporta error.
        Devuelve el token consumido o None si no coincide y error_si_no_coincide es False.
        """
        if self.token_actual and self.token_actual.tipo == tipo_token_esperado:
            if lexema_esperado is None or self.token_actual.lexema.lower() == lexema_esperado.lower():
                token_consumido = self.token_actual
                self._avanzar()
                return token_consumido
            elif error_si_no_coincide:
                self._error_sintactico(f"el lexema '{lexema_esperado}' para el token de tipo '{tipo_token_esperado}'")
        elif error_si_no_coincide:
            if lexema_esperado:
                self._error_sintactico(f"el lexema '{lexema_esperado}' (tipo: {tipo_token_esperado})")
            else:
                self._error_sintactico(f"un token de tipo '{tipo_token_esperado}'")
        return None # No coincidió (y no se lanzó error si error_si_no_coincide es False)

    def parse(self):
     """
     Punto de entrada principal para el análisis sintáctico.
     Intenta parsear un programa Pascal completo.
     Devuelve: El nodo raíz del AST (NodoPrograma) si el parsing es exitoso,
               o None si ocurren errores sintácticos.
     """
     ast_programa_nodo = None # Variable para almacenar el AST resultante
     try:
         # Llama al método para parsear el símbolo inicial de la gramática (un programa).
         # Este método ahora construirá y devolverá un NodoPrograma.
         ast_programa_nodo = self.parse_programa() 
         
         # Verifica si, después de un parsing teóricamente exitoso (sin excepciones),
         # quedan tokens inesperados antes del EOF.
         if not self.errores_sintacticos and \
            self.token_actual and \
            self.token_actual.tipo != TT_EOF_PASCAL:
             # Si parse_programa terminó pero no estamos en EOF, algo sobró.
             self._error_sintactico("el final del archivo (EOF) después de la estructura principal del programa")
             # _error_sintactico lanza SyntaxError, así que esto no debería continuar si hay error.
         
         # Si no hubo errores registrados y no se lanzó una excepción, el parsing fue exitoso.
         if not self.errores_sintacticos and ast_programa_nodo:
              print("Análisis sintáctico y construcción de AST de Pascal completados exitosamente.")
         
     except SyntaxError:
         # _error_sintactico lanza SyntaxError, que se captura aquí.
         # El error ya fue impreso por _error_sintactico.
         print(f"Análisis sintáctico de Pascal detenido debido a errores.")
         ast_programa_nodo = None # Asegurar que no se devuelva un AST parcial en caso de error
     except Exception as e:
         # Captura cualquier otra excepción inesperada durante el parsing.
         print(f"Error inesperado durante el parsing de Pascal: {e}")
         import traceback
         traceback.print_exc()
         ast_programa_nodo = None # No devolver AST en caso de error interno del parser
     
     # Registrar un resumen si hubo errores (aunque _error_sintactico ya los imprime).
     if self.errores_sintacticos and not ast_programa_nodo: # Si hubo errores y no se formó AST
          print(f"Resumen: Parsing de Pascal falló con {len(self.errores_sintacticos)} error(es) sintáctico(s) detectado(s).")
     
     return ast_programa_nodo # Devuelve el AST construido o None si falló.


    # ---------------------------------------------------------------------

    def parse_programa(self):
     # Gramática: programa ::= "program" IDENTIFICADOR ";" bloque "."
     # Construye y devuelve un NodoPrograma.
     
     # Consume la palabra clave 'program'.
     self._consumir(TT_PALABRA_RESERVADA, "program")
     
     # Consume el IDENTIFICADOR del nombre del programa y guarda el token.
     nombre_programa_token = self._consumir(TT_IDENTIFICADOR)
     # Si _consumir falla (porque el token no es el esperado), lanzará SyntaxError y la ejecución se detendrá aquí.

     # Consume el ';'.
     self._consumir(TT_PUNTO_Y_COMA)
     
     # Parsea el bloque principal del programa.
     # Este método (parse_bloque) ahora también devolverá un nodo (NodoBloque).
     # La tabla de símbolos ya tiene un alcance global por defecto al ser creada.
     # Si tuviéramos procedimientos/funciones, parse_bloque manejaría nuevos alcances.
     bloque_nodo = self.parse_bloque()
     # Si parse_bloque falla y lanza error, no llegaremos aquí. Si devuelve None por otra razón, propagar.
     if not bloque_nodo and not self.errores_sintacticos: # Si no hay errores pero no hay nodo, algo raro pasó
         self._error_sintactico("un bloque de programa válido después de las declaraciones iniciales")


     # Consume el '.' final del programa.
     self._consumir(TT_PUNTO)
     
     # Verificar que después del punto final del programa, estemos en EOF.
     # El método parse() también hace una verificación similar, pero es bueno ser estricto aquí.
     if self.token_actual and self.token_actual.tipo != TT_EOF_PASCAL:
         self._error_sintactico("el final del archivo (EOF) después del punto final del programa")
     # Opcionalmente, consumir el EOF si quieres ser explícito:
     # self._consumir(TT_EOF_PASCAL, error_si_no_coincide=False) # No fallar si no está, parse() lo revisará.
         
     # Crea y devuelve el nodo AST para el programa.
     return NodoPrograma(nombre_programa_token, bloque_nodo)

    # ---------------------------------------------------------------------



    def parse_bloque(self):
        # Gramática: bloque ::= [seccion_uses] [seccion_declaracion_var] cuerpo_programa
        # Construye y devuelve un NodoBloque.
        
        declaraciones_var_nodo = None # Inicializar
        if self.token_actual and \
           self.token_actual.tipo == TT_PALABRA_RESERVADA and \
           self.token_actual.lexema.lower() == "uses":
            self.parse_seccion_uses()

        if self.token_actual and \
           self.token_actual.tipo == TT_PALABRA_RESERVADA and \
           self.token_actual.lexema.lower() == "var":
            declaraciones_var_nodo = self.parse_seccion_declaracion_var()

        print(f"\n[DEBUG PARSER] ANTES de imprimir tabla: id(self.tabla_simbolos) = {id(self.tabla_simbolos)}")
        print(f"[DEBUG PARSER] ANTES de imprimir tabla: id(self.tabla_simbolos.alcances) = {id(self.tabla_simbolos.alcances)}")
        print(f"[DEBUG PARSER] ANTES de imprimir tabla: id(self.tabla_simbolos.alcances[0]) = {id(self.tabla_simbolos.alcances[0])}")
        print("\n[DEBUG PARSER] Contenido de la Tabla de Símbolos (después de VAR):")

        # --- INICIO DE IMPRESIÓN DE DEPURACIÓN ---
        # Imprime el contenido de la tabla de símbolos después de procesar las declaraciones 'var'.
        print("\n[DEBUG PARSER] Contenido de la Tabla de Símbolos (después de VAR):")
        if hasattr(self.tabla_simbolos, 'alcances') and self.tabla_simbolos.alcances:
            for i, alcance in enumerate(self.tabla_simbolos.alcances):
                print(f"  Alcance {i}:")
                if alcance: # Si el diccionario de alcance no está vacío
                    for nombre_simbolo, detalles_simbolo in alcance.items():
                        print(f"    '{nombre_simbolo}': {detalles_simbolo}")
                else:
                    print("      (vacío)")
        else:
            print("  La tabla de símbolos no tiene alcances o está vacía.")
        print("[DEBUG PARSER] --------------------------------------------------\n")
        # --- FIN DE IMPRESIÓN DE DEPURACIÓN ---
            
        cuerpo_nodo = self.parse_cuerpo_programa() # O parse_bloque_compuesto si lo renombraste
        return NodoBloque(declaraciones_var_nodo, cuerpo_nodo)

    def parse_seccion_uses(self):
        # Gramática: seccion_uses ::= "uses" lista_unidades ";"
        # lista_unidades ::= IDENTIFICADOR ("," IDENTIFICADOR)*
        self._consumir(TT_PALABRA_RESERVADA, "uses")
        self._consumir(TT_IDENTIFICADOR) # Primera unidad
        while self.token_actual and self.token_actual.tipo == TT_COMA:
            self._consumir(TT_COMA)
            self._consumir(TT_IDENTIFICADOR) # Siguiente unidad
        self._consumir(TT_PUNTO_Y_COMA)

    def parse_seccion_declaracion_var(self):
     # Gramática: seccion_declaracion_var ::= "var" (declaracion_variable)+
     # Construye y devuelve un NodoDeclaracionesVar que contiene una lista de NodoDeclaracionVar.
     self._consumir(TT_PALABRA_RESERVADA, "var") # Consume la palabra clave 'var'.
     
     lista_de_declaraciones = []
     # Debe haber al menos una declaración de variable según la gramática (declaracion_variable)+.
     # El bucle continúa mientras el token actual sea un identificador,
     # indicando el inicio de otra declaración de variable.
     if not (self.token_actual and self.token_actual.tipo == TT_IDENTIFICADOR):
          # Si 'var' no es seguido por una declaración de identificador, es un error.
         self._error_sintactico("al menos una declaración de variable después de 'var'")

     while self.token_actual and self.token_actual.tipo == TT_IDENTIFICADOR:
         nodo_decl_var = self.parse_declaracion_variable() # Parsea una línea de declaración.
         # Si parse_declaracion_variable lanza un error, no llegaremos aquí.
         # Si devuelve None por alguna razón inesperada (no debería con la lógica actual), podríamos manejarlo.
         if nodo_decl_var:
             lista_de_declaraciones.append(nodo_decl_var)
         elif not self.errores_sintacticos: # Si no hubo error pero no se creó nodo
              self._error_sintactico("una declaración de variable válida")


     if not lista_de_declaraciones:
         # Este caso no debería alcanzarse si el primer chequeo de identificador después de 'var' se cumple
         # y parse_declaracion_variable funciona correctamente o lanza error.
          self._error_sintactico("al menos una declaración de variable válida en la sección 'var'")
     
     return NodoDeclaracionesVar(lista_de_declaraciones)
    
    
    def parse_declaracion_variable(self):
        # Gramática: declaracion_variable ::= lista_identificadores ":" tipo ";"
        # Este método construye un NodoDeclaracionVar y registra los símbolos en la tabla de símbolos.
        
        print(f"[DEBUG Parser] Entrando a parse_declaracion_variable. Token actual: {self.token_actual}")
        
        lista_id_tokens = self.parse_lista_identificadores() 
        print(f"[DEBUG Parser] Después de parse_lista_identificadores. Token actual: {self.token_actual}")
        
        # Se consume el token ':' que separa los identificadores del tipo.
        self._consumir(TT_DOS_PUNTOS) 
        print(f"[DEBUG Parser] Después de consumir TT_DOS_PUNTOS (':'). Token actual: {self.token_actual}") # Esta línea es crucial.
        
        # Se parsea el tipo de dato. Este método debe devolver un NodoTipo.
        tipo_nodo = self.parse_tipo() 
        print(f"[DEBUG Parser] Después de parse_tipo. Token actual: {self.token_actual}, tipo_nodo devuelto: {tipo_nodo}")
        
        # Verificación de salvaguarda: si parse_tipo devolvió None y no hubo errores previos
        # (aunque parse_tipo debería lanzar un error si no puede parsear un tipo válido).
        if tipo_nodo is None and not self.errores_sintacticos: 
            self._error_sintactico("un tipo de dato válido después de ':'")
            # _error_sintactico está diseñado para lanzar una excepción, por lo que la ejecución no debería continuar.

        # Se itera sobre cada token de identificador en la lista obtenida.
        for id_token in lista_id_tokens: # Si lista_id_tokens fuera None, esto causaría un TypeError.
            nombre_variable = id_token.lexema
            
            # Verificación semántica: ¿El identificador ya ha sido declarado en el alcance actual?
            if self.tabla_simbolos.buscar_simbolo_en_alcance_actual(nombre_variable):
                mensaje_error_sem = f"Error Semántico: Re-declaración de la variable '{nombre_variable}' en L{id_token.linea}:C{id_token.columna}."
                self.errores_sintacticos.append(mensaje_error_sem) # Se registra el error.
                raise SyntaxError(mensaje_error_sem) # Se detiene el parsing.
            
            # Si no hay re-declaración, se agrega el símbolo a la tabla de símbolos.
            # Es importante que tipo_nodo sea un objeto NodoTipo válido aquí.
            print(f"[DEBUG Parser] Intentando agregar a tabla: nombre='{nombre_variable}', tipo='{tipo_nodo.nombre_tipo if tipo_nodo else 'TIPO_NODO_ES_NONE'}'")
            self.tabla_simbolos.agregar_simbolo(
                nombre=nombre_variable,
                tipo_dato=tipo_nodo.nombre_tipo, # Se accede al atributo nombre_tipo del NodoTipo.
                rol='variable', 
                linea=id_token.linea,
                columna=id_token.columna
            )

        # Se consume el punto y coma final de la declaración de variable.
        self._consumir(TT_PUNTO_Y_COMA)
        print(f"[DEBUG Parser] Saliendo de parse_declaracion_variable. Token actual: {self.token_actual}")
        
        # Se devuelve el nodo AST que representa esta declaración de variable.
        return NodoDeclaracionVar(lista_id_tokens, tipo_nodo)

   
    def parse_lista_identificadores(self):
        # Gramática: lista_identificadores ::= IDENTIFICADOR ("," IDENTIFICADOR)*
        # Devuelve una lista de tokens IDENTIFICADOR.
        identificadores_tokens = []
        
        token_id = self._consumir(TT_IDENTIFICADOR) # Consume el primer IDENTIFICADOR.
        identificadores_tokens.append(token_id)
        
        # Consume identificadores adicionales separados por comas.
        while self.token_actual and self.token_actual.tipo == TT_COMA:
            self._consumir(TT_COMA) # Consume la coma.
            token_id = self._consumir(TT_IDENTIFICADOR) # Consume el siguiente IDENTIFICADOR.
            identificadores_tokens.append(token_id)
            
        return identificadores_tokens

    def parse_tipo(self):
     # Este método verifica si el token actual representa un tipo de dato simple reconocido
     # y construye un NodoTipo.
     if self.token_actual and self.token_actual.tipo == TT_PALABRA_RESERVADA:
         tipo_token_consumido = None
         tipo_lexema = self.token_actual.lexema.lower()
         
         nodo_tipo_creado = None

         if tipo_lexema in ["integer", "real", "boolean", "char"]:
             tipo_token_consumido = self._consumir(TT_PALABRA_RESERVADA, tipo_lexema)
             nodo_tipo_creado = NodoTipo(tipo_token_consumido)
         
         elif tipo_lexema == "string":
             tipo_token_consumido = self._consumir(TT_PALABRA_RESERVADA, "string")
             nodo_tipo_creado = NodoTipo(tipo_token_consumido) # NodoTipo inicial para 'string'
             
             if self.token_actual and self.token_actual.tipo == TT_CORCHETE_IZQ:
                 self._consumir(TT_CORCHETE_IZQ)
                 token_tamanio = self._consumir(TT_NUMERO_ENTERO)
                 # Guardar el tamaño en el nodo_tipo_creado si es necesario para semántica/generación.
                 if token_tamanio:
                      nodo_tipo_creado.tamaño = token_tamanio.valor 
                 self._consumir(TT_CORCHETE_DER)
         else:
             self._error_sintactico("un tipo de dato válido (integer, real, string, boolean, char)")
         
         if nodo_tipo_creado:
             return nodo_tipo_creado
         else: 
             # Esto no debería ocurrir si _consumir lanza error o si tipo_lexema no está en la lista.
             # El _error_sintactico anterior ya debería haber detenido.
             self._error_sintactico("un tipo de dato válido reconocido")

     else:
         self._error_sintactico("una palabra reservada de tipo de dato (integer, real, etc.)")
     return None # No se alcanzará si _error_sintactico lanza excepción

    def parse_cuerpo_programa(self):
     # Gramática: cuerpo_programa ::= "begin" lista_sentencias "end"
     # Construye y devuelve un NodoCuerpoPrograma.
     self._consumir(TT_PALABRA_RESERVADA, "begin") # Consume 'begin'.
     
     # parse_lista_sentencias ahora debe devolver una lista de nodos de sentencia.
     lista_nodos_sentencia = self.parse_lista_sentencias()
     # Si parse_lista_sentencias falla, ya habrá lanzado un error.
     
     self._consumir(TT_PALABRA_RESERVADA, "end") # Consume 'end'.
     
     return NodoCuerpoPrograma(lista_nodos_sentencia)





    def parse_lista_sentencias(self):
     # Gramática: lista_sentencias ::= sentencia (";" sentencia)* [";"]?
     # Devuelve una lista de nodos de sentencia [NodoSentencia].
     
     lista_nodos_sent = []
     
     # Parsea la primera sentencia (obligatoria si se llama a este método desde un bloque begin-end no vacío).
     nodo_sent = self.parse_sentencia()
     if nodo_sent: # Si se parseó una sentencia válida (y no solo un error que detuvo)
         lista_nodos_sent.append(nodo_sent)
     elif not self.errores_sintacticos: # Si no hay errores pero no hay nodo, algo raro.
         # Esto podría ocurrir si parse_sentencia permite "sentencias vacías" sin devolver nodo.
         # O si hay un error de lógica.
         pass # Por ahora, si no hay nodo y no hay error, asumimos que fue una sentencia vacía procesada.

     # Parsear sentencias adicionales separadas por ';'.
     while self.token_actual and self.token_actual.tipo == TT_PUNTO_Y_COMA:
         self._consumir(TT_PUNTO_Y_COMA) # Consume el ';'.
         
         # Manejar el caso de un ';' opcional justo antes de 'end' o 'until'.
         if self.token_actual and self.token_actual.tipo == TT_PALABRA_RESERVADA and \
            self.token_actual.lexema.lower() in ["end", "until"]:
             # Si el siguiente token es 'end' o 'until', no se espera otra sentencia.
             break 
         
         # Si después del ';' no viene 'end' o 'until', se espera otra sentencia.
         # Si es EOF aquí, es un error.
         if not self.token_actual or self.token_actual.tipo == TT_EOF_PASCAL:
              self._error_sintactico("una sentencia después de ';' o la palabra clave 'end'/'until'")
              break # Salir del bucle si hay error

         nodo_sent = self.parse_sentencia()
         if nodo_sent:
             lista_nodos_sent.append(nodo_sent)
         elif not self.errores_sintacticos:
             # Similar al caso anterior, podría ser una sentencia vacía procesada.
             pass
     
     return lista_nodos_sent


    def parse_sentencia(self):
     # Gramática (subconjunto):
     # sentencia ::= asignacion | llamada_proc | bloque_compuesto | if_sentencia | (más adelante: while, for) | sentencia_vacia
     # Devuelve un nodo de sentencia (ej: NodoAsignacion, NodoIf, etc.) o None si es una sentencia vacía válida.
     
     if self.token_actual is None or self.token_actual.tipo == TT_EOF_PASCAL:
         self._error_sintactico("una sentencia válida")
         return None # No se alcanzará si _error_sintactico lanza excepción.

     token_tipo = self.token_actual.tipo
     token_lexema = self.token_actual.lexema.lower() if self.token_actual.lexema else ""
     nodo_sentencia_actual = None

     if token_tipo == TT_IDENTIFICADOR:
         # Podría ser una asignación (IDENTIFICADOR := ...) 
         # o una llamada a procedimiento (IDENTIFICADOR; o IDENTIFICADOR(...);)
         if self.posicion_actual + 1 < len(self.tokens) and \
            self.tokens[self.posicion_actual + 1].tipo == TT_OPERADOR_ASIGNACION:
             nodo_sentencia_actual = self.parse_asignacion()
         else:
             nodo_sentencia_actual = self.parse_llamada_procedimiento_generica()
     
     elif token_tipo == TT_PALABRA_RESERVADA:
         if token_lexema == "begin":
             nodo_sentencia_actual = self.parse_bloque_compuesto()
         elif token_lexema == "writeln":
             nodo_sentencia_actual = self.parse_llamada_writeln()
         elif token_lexema == "write":
             nodo_sentencia_actual = self.parse_llamada_write()
         elif token_lexema == "readln":
             nodo_sentencia_actual = self.parse_llamada_readln()
         elif token_lexema == "if":
             nodo_sentencia_actual = self.parse_if_sentencia()
         elif token_lexema == "while":
             nodo_sentencia_actual = self.parse_while_sentencia()
         elif token_lexema == "repeat": 
                nodo_sentencia_actual = self.parse_repeat_sentencia() 
         elif token_lexema == "for":
             nodo_sentencia_actual = self.parse_for_sentencia() 
         else:
             self._error_sintactico(f"un inicio de sentencia válido. Palabra reservada '{token_lexema}' no esperada aquí.")
     
     elif token_tipo == TT_PUNTO_Y_COMA:
         # Se interpreta como una sentencia vacía si la gramática lo permite en este contexto.
         # Nuestro parse_lista_sentencias maneja los ';' como separadores.
         # Si parse_sentencia es llamado y encuentra ';', significa que la lista de sentencias
         # tenía algo como ";;" o "sentencia ; ; sentencia".
         # Por ahora, una sentencia vacía no produce un nodo y simplemente se consume el token
         # si queremos permitirlo. O es un error.
         # Si una sentencia vacía es solo un ';', y parse_lista_sentencias ya lo consumió como separador,
         # entonces este caso no debería ser alcanzado a menos que haya ';;'.
         # Por simplicidad, si llegamos aquí es porque el lexer dio un ';' donde se esperaba una sentencia.
         # Podríamos tener un NodoSentenciaVacia o considerarlo error.
         # Dejándolo como estaba (error) es más simple por ahora:
         self._error_sintactico("una sentencia válida antes de ';'")

     else:
         self._error_sintactico(f"el inicio de una sentencia válida. Se encontró '{token_lexema}' (tipo: {token_tipo})")
     
     return nodo_sentencia_actual
    

    def parse_repeat_sentencia(self):
        # Gramática: sentencia_repeat ::= "repeat" lista_sentencias "until" expresion
        self._consumir(TT_PALABRA_RESERVADA, "repeat")
        lista_sentencias_cuerpo = self.parse_lista_sentencias()
        if not lista_sentencias_cuerpo and not self.errores_sintacticos:
            self._error_sintactico("al menos una sentencia dentro del bloque 'repeat...until'")

        self._consumir(TT_PALABRA_RESERVADA, "until")
        nodo_condicion = self.parse_expresion() # Usa el nuevo parse_expresion de nivel superior
        if not nodo_condicion and self.errores_sintacticos: return None 
        return NodoRepeat(lista_sentencias_cuerpo, nodo_condicion)

    
    def parse_while_sentencia(self):
        # Gramática: sentencia_while ::= "while" expresion "do" sentencia
        self._consumir(TT_PALABRA_RESERVADA, "while")
        nodo_condicion = self.parse_expresion() # Usa el nuevo parse_expresion de nivel superior
        if not nodo_condicion and self.errores_sintacticos: return None 
        self._consumir(TT_PALABRA_RESERVADA, "do")
        nodo_cuerpo_sentencia = self.parse_sentencia()
        if not nodo_cuerpo_sentencia and self.errores_sintacticos: return None
        return NodoWhile(nodo_condicion, nodo_cuerpo_sentencia)
        

    def parse_llamada_procedimiento_generica(self):
     # Gramática: llamada_procedimiento ::= IDENTIFICADOR ["(" lista_argumentos ")"]
     # Construye y devuelve un NodoLlamadaProcedimiento.
     token_nombre_proc = self._consumir(TT_IDENTIFICADOR)
     
     # --- Análisis Semántico (simple): Verificar si el procedimiento está "declarado" ---
     # Por ahora, solo permitimos procedimientos conocidos o no verificamos en profundidad.
     # Si tuviéramos una forma de registrar procedimientos en la tabla de símbolos:
     # simbolo_proc = self.tabla_simbolos.buscar_simbolo(token_nombre_proc.lexema)
     # if simbolo_proc is None or simbolo_proc.get('rol') != 'procedimiento':
     #     self._error_sintactico(f"Error Semántico: Procedimiento '{token_nombre_proc.lexema}' no declarado.")
     
     argumentos_nodos = []
     if self.token_actual and self.token_actual.tipo == TT_PARENTESIS_IZQ:
         self._consumir(TT_PARENTESIS_IZQ)
         if self.token_actual and self.token_actual.tipo != TT_PARENTESIS_DER:
             argumentos_nodos = self.parse_lista_argumentos()
         self._consumir(TT_PARENTESIS_DER)
     return NodoLlamadaProcedimiento(token_nombre_proc, argumentos_nodos)

    def parse_bloque_compuesto(self): # Renombrado de parse_cuerpo_programa si se usa en más contextos
        # Gramática: bloque_compuesto ::= "begin" lista_sentencias "end"
        # Devuelve un NodoCuerpoPrograma (o un NodoBloqueCompuesto).
        self._consumir(TT_PALABRA_RESERVADA, "begin")
        
        # parse_lista_sentencias ahora devuelve una lista de nodos de sentencia.
        lista_nodos_sentencia = self.parse_lista_sentencias()
        
        self._consumir(TT_PALABRA_RESERVADA, "end")
        
        # Crea y devuelve el nodo que representa este bloque de sentencias.
        return NodoCuerpoPrograma(lista_nodos_sentencia)

    def parse_asignacion(self):
                # Gramática: asignacion ::= IDENTIFICADOR ":=" expresion
        token_variable = self._consumir(TT_IDENTIFICADOR)
        simbolo_var = self.tabla_simbolos.buscar_simbolo(token_variable.lexema)
        if simbolo_var is None:
            mensaje_error_sem = f"Error Semántico: Variable '{token_variable.lexema}' no declarada (en asignación en L{token_variable.linea}:C{token_variable.columna})."
            self.errores_sintacticos.append(mensaje_error_sem)
            raise SyntaxError(mensaje_error_sem)

        self._consumir(TT_OPERADOR_ASIGNACION)
        nodo_expresion = self.parse_expresion() # Usa el nuevo parse_expresion de nivel superior
        if not nodo_expresion and self.errores_sintacticos: return None 

        return NodoAsignacion(token_variable, nodo_expresion)

    def parse_llamada_writeln(self):
        # Gramática: llamada_writeln ::= "writeln" ["(" lista_argumentos ")"]
        # Construye y devuelve un NodoLlamadaProcedimiento.
        token_nombre_proc = self._consumir(TT_PALABRA_RESERVADA, "writeln")
        argumentos_nodos = []
        if self.token_actual and self.token_actual.tipo == TT_PARENTESIS_IZQ:
            self._consumir(TT_PARENTESIS_IZQ)
            if self.token_actual and self.token_actual.tipo != TT_PARENTESIS_DER:
                argumentos_nodos = self.parse_lista_argumentos()
            self._consumir(TT_PARENTESIS_DER)
        return NodoLlamadaProcedimiento(token_nombre_proc, argumentos_nodos)

    def parse_llamada_write(self):
     # Gramática: llamada_write ::= "write" ["(" lista_argumentos ")"]
     # Construye y devuelve un NodoLlamadaProcedimiento.
     token_nombre_proc = self._consumir(TT_PALABRA_RESERVADA, "write")
     argumentos_nodos = []
     if self.token_actual and self.token_actual.tipo == TT_PARENTESIS_IZQ:
         self._consumir(TT_PARENTESIS_IZQ)
         if self.token_actual and self.token_actual.tipo != TT_PARENTESIS_DER:
             argumentos_nodos = self.parse_lista_argumentos()
         self._consumir(TT_PARENTESIS_DER)
     return NodoLlamadaProcedimiento(token_nombre_proc, argumentos_nodos)

    def parse_llamada_readln(self):
        # Gramática: llamada_readln ::= "readln" ["(" lista_identificadores_para_read ")"]
        token_nombre_proc = self._consumir(TT_PALABRA_RESERVADA, "readln")
        argumentos_nodos_id = [] 
        if self.token_actual and self.token_actual.tipo == TT_PARENTESIS_IZQ:
            self._consumir(TT_PARENTESIS_IZQ)
            if self.token_actual and self.token_actual.tipo != TT_PARENTESIS_DER:
                lista_id_tokens = self.parse_lista_identificadores_para_read()
                if lista_id_tokens is None and not self.errores_sintacticos: 
                    # Esto no debería pasar si parse_lista_identificadores_para_read siempre devuelve lista o lanza error
                    self._error_sintactico("una lista válida de identificadores para readln")

                for id_token in lista_id_tokens: # Si lista_id_tokens es None, esto fallará
                    simbolo = self.tabla_simbolos.buscar_simbolo(id_token.lexema)
                    if simbolo is None:
                        mensaje_error_sem = f"Error Semántico: Identificador '{id_token.lexema}' no declarado (en readln en L{id_token.linea}:C{id_token.columna})."
                        self.errores_sintacticos.append(mensaje_error_sem) # Registrar el error
                        raise SyntaxError(mensaje_error_sem) # Detener el parsing
                    argumentos_nodos_id.append(NodoIdentificador(id_token))
            self._consumir(TT_PARENTESIS_DER)
        return NodoLlamadaProcedimiento(token_nombre_proc, argumentos_nodos_id)

    def parse_lista_identificadores_para_read(self):
        # Gramática: lista_identificadores_para_read ::= IDENTIFICADOR ("," IDENTIFICADOR)*
        # Este método parsea una lista de identificadores, típicamente usada por 'readln'.
        # Devuelve: Una lista de tokens IDENTIFICADOR.
        
        # Siempre se inicializa una lista para almacenar los tokens de los identificadores.
        identificadores_tokens = [] 
        
        # Se consume el primer IDENTIFICADOR.
        # El método _consumir está diseñado para lanzar una excepción SyntaxError
        # si el token actual no es un IDENTIFICADOR. Esto detendría la ejecución
        # de este método antes de que pudiera devolver None incorrectamente.
        token_id = self._consumir(TT_IDENTIFICADOR) 
        identificadores_tokens.append(token_id) # Se añade el primer token de identificador a la lista.
        
        # Se consumen identificadores adicionales que estén separados por comas.
        while self.token_actual and self.token_actual.tipo == TT_COMA:
            self._consumir(TT_COMA) # Se consume la coma.
            
            # Se consume el siguiente IDENTIFICADOR.
            # Nuevamente, _consumir lanzará SyntaxError si el token no es un IDENTIFICADOR.
            token_id = self._consumir(TT_IDENTIFICADOR) 
            identificadores_tokens.append(token_id) # Se añade el token de identificador a la lista.
            
        # Se devuelve la lista de tokens de identificador.
        # Esta lista contendrá al menos un identificador si el análisis sintáctico
        # hasta este punto fue exitoso y la gramática se cumplió.
        return identificadores_tokens

    def parse_if_sentencia(self):
        # Gramática: sentencia_if ::= "if" expresion "then" sentencia ["else" sentencia]
        self._consumir(TT_PALABRA_RESERVADA, "if")
        nodo_condicion = self.parse_expresion() # Usa el nuevo parse_expresion de nivel superior
        if not nodo_condicion and self.errores_sintacticos: return None
        self._consumir(TT_PALABRA_RESERVADA, "then")
        nodo_sentencia_then = self.parse_sentencia()
        if not nodo_sentencia_then and self.errores_sintacticos: return None
        nodo_sentencia_else = None 
        if self.token_actual and \
           self.token_actual.tipo == TT_PALABRA_RESERVADA and \
           self.token_actual.lexema.lower() == "else":
            self._consumir(TT_PALABRA_RESERVADA, "else")
            nodo_sentencia_else = self.parse_sentencia()
            if not nodo_sentencia_else and self.errores_sintacticos: return None 
        return NodoIf(nodo_condicion, nodo_sentencia_then, nodo_sentencia_else)


    def parse_lista_argumentos(self):
        # Gramática: lista_argumentos ::= expresion ("," expresion)*
        lista_nodos_arg = []
        nodo_expr = self.parse_expresion() # Usa el nuevo parse_expresion de nivel superior
        if nodo_expr: 
            lista_nodos_arg.append(nodo_expr)
        elif not self.errores_sintacticos: 
             self._error_sintactico("una expresión como argumento")

        while self.token_actual and self.token_actual.tipo == TT_COMA:
            self._consumir(TT_COMA)
            nodo_expr = self.parse_expresion() # Usa el nuevo parse_expresion de nivel superior
            if nodo_expr:
                lista_nodos_arg.append(nodo_expr)
            elif not self.errores_sintacticos:
                 self._error_sintactico("una expresión después de la coma en la lista de argumentos")
        return lista_nodos_arg
    
    #NUEVOS METODOS
    def parse_factor(self):
        # Gramática: factor ::= IDENTIFICADOR | NUMERO_ENTERO | NUMERO_REAL | CADENA_LITERAL |
        #                     '(' expresion ')' | "true" | "false"
        # El operador 'not' ahora se maneja en parse_factor_logico.
        token_actual_val = self.token_actual 
        if token_actual_val is None:
            self._error_sintactico("un factor (identificador, número, cadena, booleano, o expresión entre paréntesis)")

        tipo_actual = token_actual_val.tipo
        lexema_actual_lower = token_actual_val.lexema.lower() if token_actual_val.lexema else ""

        if tipo_actual == TT_IDENTIFICADOR:
            token_id_consumido = self._consumir(TT_IDENTIFICADOR)
            simbolo = self.tabla_simbolos.buscar_simbolo(token_id_consumido.lexema)
            if simbolo is None:
                mensaje_error_sem = (f"Error Semántico: Identificador '{token_id_consumido.lexema}' no declarado "
                                     f"(usado en L{token_id_consumido.linea}:C{token_id_consumido.columna}).")
                self.errores_sintacticos.append(mensaje_error_sem)
                raise SyntaxError(mensaje_error_sem)
            return NodoIdentificador(token_id_consumido)
        
        elif tipo_actual in [TT_NUMERO_ENTERO, TT_NUMERO_REAL, TT_CADENA_LITERAL]:
            token_literal_consumido = self._consumir(tipo_actual)
            return NodoLiteral(token_literal_consumido)
        
        elif tipo_actual == TT_PALABRA_RESERVADA and lexema_actual_lower in ["true", "false"]:
            token_booleano_consumido = self._consumir(TT_PALABRA_RESERVADA, lexema_actual_lower)
            return NodoLiteral(token_booleano_consumido)
            
        elif tipo_actual == TT_PARENTESIS_IZQ:
            self._consumir(TT_PARENTESIS_IZQ)
            nodo_expr_interna = self.parse_expresion() # Llamada al nivel más alto de expresiones
            self._consumir(TT_PARENTESIS_DER)
            return nodo_expr_interna
            
        else:
            self._error_sintactico(
                f"un factor válido (identificador, número, cadena, 'true', 'false', o '('). "
                f"Se encontró '{token_actual_val.lexema}' (tipo: {tipo_actual})"
            )
        return None
    
    def parse_termino_aritmetico(self):
        # Gramática: termino_aritmetico ::= factor (('*' | '/' | 'div' | 'mod') factor)*
        nodo = self.parse_factor()
        while self.token_actual and \
              self.token_actual.tipo == TT_OPERADOR_ARITMETICO and \
              self.token_actual.lexema.lower() in ['*', '/', 'div', 'mod']:
            token_operador = self._consumir(TT_OPERADOR_ARITMETICO)
            nodo_derecho = self.parse_factor()
            nodo = NodoExpresionBinaria(token_operador, nodo, nodo_derecho)
        return nodo

    def parse_factor_logico(self):
        # Gramática: factor_logico ::= ["not"] expresion_comparativa
        # Maneja el operador 'not' que tiene la precedencia más alta entre los lógicos.
        token_op_not = None
        if self.token_actual and \
           self.token_actual.tipo == TT_PALABRA_RESERVADA and \
           self.token_actual.lexema.lower() == 'not':
            token_op_not = self._consumir(TT_PALABRA_RESERVADA, 'not')
        
        nodo_operando = self.parse_expresion_comparativa()

        if token_op_not:
            return NodoExpresionUnaria(token_op_not, nodo_operando)
        else:
            return nodo_operando
    
    def parse_termino_logico(self):
        # Gramática: termino_logico ::= factor_logico ("and" factor_logico)*
        # Maneja el operador 'and'.
        nodo = self.parse_factor_logico()

        while self.token_actual and \
              self.token_actual.tipo == TT_PALABRA_RESERVADA and \
              self.token_actual.lexema.lower() == 'and':
            token_operador_and = self._consumir(TT_PALABRA_RESERVADA, 'and')
            nodo_derecho = self.parse_factor_logico()
            nodo = NodoExpresionBinaria(token_operador_and, nodo, nodo_derecho)
        return nodo
    
    def parse_expresion_simple(self):
        # Gramática: expresion_simple ::= ['+'|'-'] termino_aritmetico (('+' | '-') termino_aritmetico)*
        # (Manejo de unario +/- se podría añadir aquí si se desea mayor complejidad)
        nodo = self.parse_termino_aritmetico()
        while self.token_actual and \
              self.token_actual.tipo == TT_OPERADOR_ARITMETICO and \
              self.token_actual.lexema in ['+', '-']:
            token_operador = self._consumir(TT_OPERADOR_ARITMETICO)
            nodo_derecho = self.parse_termino_aritmetico()
            nodo = NodoExpresionBinaria(token_operador, nodo, nodo_derecho)
        return nodo
    

    def parse_expresion_logica(self): # Anteriormente llamado parse_expresion
        # Gramática: expresion_logica ::= expresion_simple [OPERADOR_RELACIONAL expresion_simple]
        # Devuelve: NodoExpresion (el resultado de expresion_simple o un NodoExpresionBinaria para la comparación).
        
        nodo = self.parse_termino_logico() # Parsea la primera parte (que puede incluir 'not' y 'and').

        while self.token_actual and \
              self.token_actual.tipo == TT_PALABRA_RESERVADA and \
              self.token_actual.lexema.lower() == 'or':
            
            token_operador_or = self._consumir(TT_PALABRA_RESERVADA, 'or')
            nodo_derecho = self.parse_termino_logico() # Parsea el siguiente operando.
            nodo = NodoExpresionBinaria(token_operador_or, nodo, nodo_derecho)
            
        return nodo

    
    def parse_factor(self):
        # Gramática: factor ::= IDENTIFICADOR | NUMERO_ENTERO | NUMERO_REAL | CADENA_LITERAL |
        #                     '(' expresion_logica ')' | "true" | "false" | "not" factor
        # Devuelve: NodoIdentificador, NodoLiteral, o el nodo de la expresion_logica entre paréntesis.
        # Nota: El operador 'not' unario se podría añadir aquí. Por ahora, lo omitimos.

        token_actual = self.token_actual
        if token_actual is None:
            self._error_sintactico("un factor (identificador, número, cadena, booleano, o expresión entre paréntesis)")

        tipo_actual = token_actual.tipo
        lexema_actual_lower = token_actual.lexema.lower() if token_actual.lexema else ""

        if tipo_actual == TT_IDENTIFICADOR:
            token_id_consumido = self._consumir(TT_IDENTIFICADOR)
            simbolo = self.tabla_simbolos.buscar_simbolo(token_id_consumido.lexema)
            if simbolo is None:
                mensaje_error_sem = (
                    f"Error Semántico: Identificador '{token_id_consumido.lexema}' no declarado "
                    f"(usado en L{token_id_consumido.linea}:C{token_id_consumido.columna})."
                )
                self.errores_sintacticos.append(mensaje_error_sem)
                raise SyntaxError(mensaje_error_sem)
            return NodoIdentificador(token_id_consumido)
        
        elif tipo_actual in [TT_NUMERO_ENTERO, TT_NUMERO_REAL, TT_CADENA_LITERAL]:
            token_literal_consumido = self._consumir(tipo_actual)
            return NodoLiteral(token_literal_consumido)
        
        elif tipo_actual == TT_PALABRA_RESERVADA and lexema_actual_lower in ["true", "false"]:
            token_booleano_consumido = self._consumir(TT_PALABRA_RESERVADA, lexema_actual_lower)
            return NodoLiteral(token_booleano_consumido)
            
        elif tipo_actual == TT_PARENTESIS_IZQ:
            self._consumir(TT_PARENTESIS_IZQ) # Consume '('.
            nodo_expr_interna = self.parse_expresion_logica() # Parsea la expresión interna (puede ser lógica o aritmética).
            self._consumir(TT_PARENTESIS_DER)  # Consume ')'.
            return nodo_expr_interna # El nodo de la sub-expresión es el resultado.
            
        else:
            self._error_sintactico(
                f"un factor válido (identificador, número, cadena, 'true', 'false', o '('). "
                f"Se encontró '{token_actual.lexema}' (tipo: {tipo_actual})"
            )
        return None # No se alcanza si _error_sintactico lanza excepción.




    def parse_termino(self):
        # Gramática: termino ::= factor (('*' | '/' | 'div' | 'mod') factor)*
        # Devuelve: NodoExpresion (el factor inicial o un NodoExpresionBinaria).
        # Por ahora, solo implementaremos '*'
        
        nodo = self.parse_factor() # Parsea el primer factor.

        # Mientras el token actual sea un operador de multiplicación o división.
        while self.token_actual and \
              self.token_actual.tipo == TT_OPERADOR_ARITMETICO and \
              self.token_actual.lexema in ['*', '/', 'div', 'mod']: # Añadir '/', 'div', 'mod' aquí si se implementan
            
            token_operador = self._consumir(TT_OPERADOR_ARITMETICO) # Consume el operador.
            nodo_derecho = self.parse_factor() # Parsea el siguiente factor.
            # Crea un nodo de expresión binaria con el nodo actual como izquierdo.
            nodo = NodoExpresionBinaria(token_operador, nodo, nodo_derecho)
            
        return nodo

    def parse_expresion_comparativa(self): 
        # Gramática: expresion_comparativa ::= expresion_simple [OPERADOR_RELACIONAL expresion_simple]
        nodo_izquierdo = self.parse_expresion_simple()
        if self.token_actual and self.token_actual.tipo == TT_OPERADOR_RELACIONAL:
            token_operador = self._consumir(TT_OPERADOR_RELACIONAL)
            nodo_derecho = self.parse_expresion_simple()
            return NodoExpresionBinaria(token_operador, nodo_izquierdo, nodo_derecho)
        else:
            return nodo_izquierdo

    def parse_expresion(self): # Punto de entrada principal para expresiones
            # Gramática: expresion ::= termino_logico ("or" termino_logico)*
            # Maneja el operador 'or', que tiene la precedencia más baja entre los lógicos.
            
            nodo = self.parse_termino_logico() # Parsea la primera parte (que puede incluir 'not' y 'and').
            print(f"[DEBUG Parser.parse_expresion] Después de parse_termino_logico. Token actual: {self.token_actual}, Nodo izquierdo para OR: {nodo}")


            while self.token_actual and \
                self.token_actual.tipo == TT_PALABRA_RESERVADA and \
                self.token_actual.lexema.lower() == 'or':
                print(f"[DEBUG Parser.parse_expresion] Entrando al bucle OR. Token actual: {self.token_actual}")


                token_operador_or = self._consumir(TT_PALABRA_RESERVADA, 'or')
                nodo_derecho = self.parse_termino_logico() # Parsea el siguiente operando.
                nodo = NodoExpresionBinaria(token_operador_or, nodo, nodo_derecho)
                print(f"[DEBUG Parser.parse_expresion] Después de procesar OR. Token actual: {self.token_actual}, Nuevo nodo: {nodo}")

                
            return nodo