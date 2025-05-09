# src/analizador_sintactico/parser_pascal.py

# Es crucial importar los tipos de token desde nuestro lexer de Pascal
# para que el parser sepa qué esperar.
try:
    from analizador_lexico.lexer_pascal import (
        TT_PALABRA_RESERVADA, TT_IDENTIFICADOR, TT_NUMERO_ENTERO, TT_NUMERO_REAL,
        TT_CADENA_LITERAL, TT_OPERADOR_ASIGNACION, TT_OPERADOR_RELACIONAL, # Añadir más si son necesarios
        TT_OPERADOR_ARITMETICO, TT_PUNTO_Y_COMA, TT_DOS_PUNTOS, TT_PUNTO, TT_COMA,
        TT_PARENTESIS_IZQ, TT_PARENTESIS_DER, TT_EOF_PASCAL
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


class ParserPascal:
    def __init__(self, tokens):
        self.tokens = [token for token in tokens if token.tipo != 'WHITESPACE_PASCAL'] # Ignorar whitespace
        self.posicion_actual = 0
        self.token_actual = self.tokens[self.posicion_actual] if self.tokens else None
        self.errores_sintacticos = []

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
        """Punto de entrada principal para el análisis sintáctico."""
        try:
            self.parse_programa() # El símbolo inicial de nuestra gramática Pascal
            # Después de parse_programa, deberíamos haber consumido todos los tokens hasta EOF
            if not self.errores_sintacticos and self.token_actual and self.token_actual.tipo != TT_EOF_PASCAL:
                # Si parse_programa terminó pero quedan tokens antes de EOF, es un error.
                self._error_sintactico("el final del archivo (EOF) después de la estructura principal del programa")
            
            if not self.errores_sintacticos:
                 print("Análisis sintáctico de Pascal completado exitosamente.")
                 return True # O un AST si lo construimos
            
        except SyntaxError:
            # El error ya fue impreso por _error_sintactico
            print(f"Análisis sintáctico de Pascal detenido debido a errores.")
        except Exception as e:
            print(f"Error inesperado durante el parsing de Pascal: {e}")
            import traceback
            traceback.print_exc()
        
        # Si llegamos aquí, hubo errores o una excepción.
        if self.errores_sintacticos:
             print(f"Resumen: Se encontraron {len(self.errores_sintacticos)} errores sintácticos.")
        return False

    # ---------------------------------------------------------------------
    # Aquí comenzarán los métodos para cada regla de producción (no-terminal)
    # de nuestra gramática Pascal. Ej: parse_programa, parse_bloque, etc.
    # ---------------------------------------------------------------------

    def parse_programa(self):
        # Gramática: programa ::= "program" IDENTIFICADOR ";" bloque "."
        self._consumir(TT_PALABRA_RESERVADA, "program")
        self._consumir(TT_IDENTIFICADOR) # Nombre del programa
        self._consumir(TT_PUNTO_Y_COMA)
        self.parse_bloque()
        self._consumir(TT_PUNTO)
        # Opcional: consumir el EOF aquí si es el final esperado.
        self._consumir(TT_EOF_PASCAL, error_si_no_coincide=False) # No es un error si no está, parse() lo verificará





    def parse_bloque(self):
        # Gramática: bloque ::= [seccion_declaracion_var] cuerpo_programa
        # La sección de declaración de variables es opcional.
        # Miramos el siguiente token para decidir si hay una sección 'var'.
        if self.token_actual and \
           self.token_actual.tipo == TT_PALABRA_RESERVADA and \
           self.token_actual.lexema.lower() == "var":
            self.parse_seccion_declaracion_var()
        
        self.parse_cuerpo_programa()

    def parse_seccion_declaracion_var(self):
        # Gramática: seccion_declaracion_var ::= "var" (declaracion_variable)+
        self._consumir(TT_PALABRA_RESERVADA, "var")
        
        # Debe haber al menos una declaración de variable.
        # Continuar mientras la siguiente parte parezca una declaración de variable
        # (es decir, un identificador, ya que "begin" marcaría el fin de las 'var').
        while self.token_actual and \
              self.token_actual.tipo == TT_IDENTIFICADOR: # Una nueva declaración de var empieza con un identificador
            self.parse_declaracion_variable()
        
        # Podríamos añadir una verificación aquí para asegurar que al menos una declaración fue parseada
        # si la gramática estrictamente requiere (declaracion_variable)+.
        # Por ahora, permitimos que la sección 'var' esté vacía después de la palabra clave 'var',
        # aunque la buena práctica de Pascal requeriría al menos una.

    def parse_declaracion_variable(self):
        # Gramática (simplificada): declaracion_variable ::= lista_identificadores ":" tipo ";"
        # Nuestra simplificación inicial: un solo identificador para empezar.
        # lista_identificadores ::= IDENTIFICADOR ("," IDENTIFICADOR)* -- implementaremos esto
        
        self.parse_lista_identificadores()
        self._consumir(TT_DOS_PUNTOS)
        self.parse_tipo()
        self._consumir(TT_PUNTO_Y_COMA)

    def parse_lista_identificadores(self):
        # Gramática: lista_identificadores ::= IDENTIFICADOR ("," IDENTIFICADOR)*
        self._consumir(TT_IDENTIFICADOR)
        while self.token_actual and self.token_actual.tipo == TT_COMA:
            self._consumir(TT_COMA)
            self._consumir(TT_IDENTIFICADOR)

    def parse_tipo(self):
        # Gramática (simplificada): tipo ::= "integer" | "real" | "string" | "boolean"
        if self.token_actual and self.token_actual.tipo == TT_PALABRA_RESERVADA:
            tipo_lexema = self.token_actual.lexema.lower()
            if tipo_lexema in ["integer", "real", "string", "boolean"]:
                self._consumir(TT_PALABRA_RESERVADA, tipo_lexema) # Consume el tipo
            else:
                self._error_sintactico("un tipo válido (integer, real, string, boolean)")
        else:
            self._error_sintactico("un tipo válido (integer, real, string, boolean)")

    def parse_cuerpo_programa(self):
        # Gramática: cuerpo_programa ::= "begin" lista_sentencias "end"
        self._consumir(TT_PALABRA_RESERVADA, "begin")
        self.parse_lista_sentencias()
        self._consumir(TT_PALABRA_RESERVADA, "end")





    def parse_lista_sentencias(self):
        # Gramática: lista_sentencias ::= sentencia (";" sentencia)* [";"]?
        # Esta es una forma común de manejar listas de sentencias separadas por ;
        # donde el último ; antes de 'end' podría ser opcional o requerido.
        
        # Parsear la primera sentencia obligatoria
        self.parse_sentencia()
        
        # Parsear sentencias adicionales separadas por ;
        while self.token_actual and self.token_actual.tipo == TT_PUNTO_Y_COMA:
            # Consumir el ';'
            self._consumir(TT_PUNTO_Y_COMA)
            
            # Manejar el caso de un ';' opcional justo antes de 'end' o 'until'
            # Si después del ';' viene 'end' (o 'until' en un bucle repeat),
            # entonces no debería haber otra sentencia.
            if self.token_actual and self.token_actual.tipo == TT_PALABRA_RESERVADA and \
               self.token_actual.lexema.lower() in ["end", "until"]: # 'until' para bucles REPEAT
                break # No hay más sentencias después de este ;
            
            # Si el token actual es None (EOF inesperado aquí) o EOF, también es un error si se esperaba una sentencia.
            if not self.token_actual or self.token_actual.tipo == TT_EOF_PASCAL:
                # A menos que un ; final sea opcional y estemos realmente al final del bloque.
                # Este caso se maneja mejor por la estructura que llama a lista_sentencias.
                # Por ahora, si hay un ; debe seguir una sentencia o un 'end'/'until'.
                # Si no es 'end' o 'until', se esperaba una sentencia.
                 self._error_sintactico("una sentencia después de ';' o la palabra clave 'end'/'until'")

            self.parse_sentencia()
        
        # No consumimos un ';' final aquí; la estructura que llama (ej. bloque_compuesto)
        # o la propia sentencia (si el ; es parte de ella) se encarga de eso.
        # Pascal es un poco flexible con el último ';' antes de un 'end'.

    def parse_sentencia(self):
        # Gramática (subconjunto):
        # sentencia ::= asignacion | llamada_writeln | bloque_compuesto | if_sentencia | while_sentencia | for_sentencia | sentencia_vacia
        # sentencia_vacia ::= (* puede ser solo un ';' si la gramática lo permite en ciertos contextos *)

        if self.token_actual is None or self.token_actual.tipo == TT_EOF_PASCAL:
            self._error_sintactico("una sentencia válida")
            return # No debería alcanzarse debido a la excepción en _error_sintactico

        token_tipo = self.token_actual.tipo
        token_lexema = self.token_actual.lexema.lower() if self.token_actual.lexema else ""

        if token_tipo == TT_IDENTIFICADOR:
            # Podría ser una asignación (IDENTIFICADOR := ...) o una llamada a procedimiento.
            # Necesitamos mirar un token adelante (lookahead) para el ':='
            if self.posicion_actual + 1 < len(self.tokens) and \
               self.tokens[self.posicion_actual + 1].tipo == TT_OPERADOR_ASIGNACION:
                self.parse_asignacion()
            # Podríamos añadir chequeos para otros procedimientos conocidos aquí si no son palabras reservadas
            else:
                # Por ahora, si es un identificador y no le sigue ':=', y no es 'writeln',
                # lo marcamos como error para nuestro subconjunto.
                # En un Pascal completo, podría ser una llamada a procedimiento definido por el usuario.
                self._error_sintactico(f"un operador de asignación (:=) después del identificador '{self.token_actual.lexema}' o una llamada a procedimiento conocida")
        
        elif token_tipo == TT_PALABRA_RESERVADA:
            if token_lexema == "begin":
                self.parse_bloque_compuesto()
            elif token_lexema == "writeln": # o "write"
                self.parse_llamada_writeln()
            # elif token_lexema == "if":
            #     self.parse_if_sentencia() # Por implementar
            # elif token_lexema == "while":
            #     self.parse_while_sentencia() # Por implementar
            # elif token_lexema == "for":
            #     self.parse_for_sentencia() # Por implementar
            else:
                self._error_sintactico(f"un inicio de sentencia válido. Palabra reservada '{token_lexema}' no esperada aquí.")
        
        elif token_tipo == TT_PUNTO_Y_COMA:
            # Esto podría interpretarse como una sentencia vacía.
            # En algunos contextos, un ';' solo es válido.
            # Por ahora, nuestro `parse_lista_sentencias` consume el ';'.
            # Si llegamos aquí con un ';', podría ser un error o una sentencia vacía
            # que no debería ser manejada por `parse_sentencia` directamente sino por `parse_lista_sentencias`.
            # Vamos a considerarlo un error si se llama a `parse_sentencia` y lo primero que encuentra es ';'.
             self._error_sintactico("una sentencia antes de ';'")

        else:
            self._error_sintactico(f"el inicio de una sentencia válida (ej: identificador, 'begin', 'writeln'). Se encontró '{token_lexema}'")

    def parse_bloque_compuesto(self):
        # Gramática: bloque_compuesto ::= "begin" lista_sentencias "end"
        # (Ya lo teníamos, pero lo pongo aquí por completitud de las sentencias)
        self._consumir(TT_PALABRA_RESERVADA, "begin")
        self.parse_lista_sentencias()
        self._consumir(TT_PALABRA_RESERVADA, "end")

    def parse_asignacion(self):
        # Gramática: asignacion ::= IDENTIFICADOR ":=" expresion
        self._consumir(TT_IDENTIFICADOR) # El identificador ya fue verificado por el llamador (parse_sentencia)
        self._consumir(TT_OPERADOR_ASIGNACION) # Consume ':='
        self.parse_expresion()
        # El ; después de la asignación lo consume parse_lista_sentencias

    def parse_llamada_writeln(self):
        # Gramática: llamada_writeln ::= "writeln" ["(" lista_argumentos ")"]
        self._consumir(TT_PALABRA_RESERVADA, "writeln")
        if self.token_actual and self.token_actual.tipo == TT_PARENTESIS_IZQ:
            self._consumir(TT_PARENTESIS_IZQ)
            # Si el siguiente token no es ')', entonces hay argumentos
            if self.token_actual and self.token_actual.tipo != TT_PARENTESIS_DER:
                self.parse_lista_argumentos()
            self._consumir(TT_PARENTESIS_DER)
        # Si no hay '(', es un writeln sin argumentos, lo cual es válido.
        # El ; después de la llamada lo consume parse_lista_sentencias

    def parse_lista_argumentos(self):
        # Gramática: lista_argumentos ::= expresion ("," expresion)*
        self.parse_expresion() # Parsear la primera expresión (obligatoria si se llama a esta función)
        while self.token_actual and self.token_actual.tipo == TT_COMA:
            self._consumir(TT_COMA)
            self.parse_expresion()

    def parse_expresion(self):
        # Gramática (SUPER SIMPLIFICADA POR AHORA):
        # expresion ::= IDENTIFICADOR | NUMERO_ENTERO | NUMERO_REAL | CADENA_LITERAL | "true" | "false"
        # Esta es una placeholder. Un parser de expresiones real es mucho más complejo
        # y manejaría operadores, precedencia, asociatividad, paréntesis, etc.
        
        # print(f"DEBUG: parse_expresion, token_actual={self.token_actual}") # Para depuración
        
        if self.token_actual is None:
            self._error_sintactico("una expresión (identificador, número, cadena, true/false)")
            return

        token_tipo = self.token_actual.tipo
        token_lexema = self.token_actual.lexema.lower() if self.token_actual.lexema else ""

        if token_tipo == TT_IDENTIFICADOR:
            self._consumir(TT_IDENTIFICADOR)
        elif token_tipo == TT_NUMERO_ENTERO:
            self._consumir(TT_NUMERO_ENTERO)
        elif token_tipo == TT_NUMERO_REAL:
            self._consumir(TT_NUMERO_REAL)
        elif token_tipo == TT_CADENA_LITERAL:
            self._consumir(TT_CADENA_LITERAL)
        elif token_tipo == TT_PALABRA_RESERVADA and token_lexema in ["true", "false"]:
            self._consumir(TT_PALABRA_RESERVADA, token_lexema)
        # Podríamos añadir "(" expresion ")" aquí, pero eso introduce recursión directa
        # que necesita ser manejada cuidadosamente en el parser de expresiones completo.
        # elif token_tipo == TT_PARENTESIS_IZQ:
        #     self._consumir(TT_PARENTESIS_IZQ)
        #     self.parse_expresion() # Recursión
        #     self._consumir(TT_PARENTESIS_DER)
        else:
            self._error_sintactico(f"una expresión válida (identificador, número, cadena, 'true', o 'false'). Se encontró '{self.token_actual.lexema}'")

    # Aún faltan: parse_if_sentencia, parse_while_sentencia, parse_for_sentencia,
    # y una implementación más robusta de parse_expresion.