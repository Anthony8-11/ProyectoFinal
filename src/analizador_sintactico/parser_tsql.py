# src/analizador_sintactico/parser_tsql.py
import re # Aunque no lo usemos directamente en el parser, es bueno tenerlo si se necesitaran regex complejas.

# Importaciones de los tipos de token desde el lexer de T-SQL.
# Es crucial que estos nombres coincidan con los definidos en lexer_tsql.py.
try:
    from analizador_lexico.lexer_tsql import (
        TT_PALABRA_CLAVE, TT_IDENTIFICADOR, TT_LITERAL_CADENA, TT_LITERAL_NUMERICO,
        TT_OPERADOR_COMPARACION, TT_OPERADOR_ARITMETICO,
        TT_PARENTESIS_IZQ, TT_PARENTESIS_DER, TT_COMA, TT_PUNTO_Y_COMA, TT_PUNTO,
        TT_ASTERISCO, TT_EOF_SQL
        # Añade más tipos de token según los necesites en las reglas del parser.
    )
    # Importar la clase Token si se va a usar para type hinting o inspección.
    from analizador_lexico.lexer_tsql import Token 
except ImportError:
    print("ADVERTENCIA CRÍTICA (ParserTSQL): No se pudieron importar los tipos de token de LexerTSQL.")
    # Definir placeholders para que el archivo al menos cargue si hay problemas.
    # El parser no funcionará correctamente en este estado.
    TT_PALABRA_CLAVE, TT_IDENTIFICADOR, TT_EOF_SQL = "PALABRA_CLAVE", "IDENTIFICADOR", "EOF_SQL"
    TT_LITERAL_CADENA, TT_LITERAL_NUMERICO = "LITERAL_CADENA", "LITERAL_NUMERICO"
    TT_OPERADOR_COMPARACION, TT_OPERADOR_ARITMETICO = "OPERADOR_COMPARACION", "OPERADOR_ARITMETICO"
    TT_PARENTESIS_IZQ, TT_PARENTESIS_DER, TT_COMA = "PARENTESIS_IZQ", "PARENTESIS_DER", "COMA"
    TT_PUNTO_Y_COMA, TT_PUNTO, TT_ASTERISCO = "PUNTO_Y_COMA", "PUNTO", "ASTERISCO"
    class Token: pass

# --- Definiciones de Nodos del AST para T-SQL ---

class NodoAST_SQL:
    """Clase base para todos los nodos del AST de SQL."""
    def __repr__(self, indent=0):
        indent_str = "  " * indent
        return f"{indent_str}{self.__class__.__name__}"

class NodoScriptSQL(NodoAST_SQL):
    """Representa un script SQL completo, que puede contener múltiples lotes o sentencias."""
    def __init__(self, lotes_o_sentencias):
        # Puede ser una lista de NodoLoteSQL o directamente una lista de NodoSentenciaSQL.
        self.lotes_o_sentencias = lotes_o_sentencias

    def __repr__(self, indent=0):
        indent_str = "  " * indent
        items_repr = "\n".join([item.__repr__(indent + 1) for item in self.lotes_o_sentencias])
        return (f"{indent_str}NodoScriptSQL([\n"
                f"{items_repr}\n"
                f"{indent_str}])")

class NodoLoteSQL(NodoAST_SQL):
    """Representa un lote de sentencias T-SQL, usualmente separado por GO."""
    def __init__(self, sentencias):
        self.sentencias = sentencias # Lista de NodoSentenciaSQL

    def __repr__(self, indent=0):
        indent_str = "  " * indent
        sents_repr = "\n".join([s.__repr__(indent + 1) for s in self.sentencias])
        return (f"{indent_str}NodoLoteSQL([\n"
                f"{sents_repr}\n"
                f"{indent_str}])")

class NodoSentenciaSQL(NodoAST_SQL):
    """Clase base para todas las sentencias SQL."""
    pass

# --- Nodos para DDL (Data Definition Language) ---
class NodoCreateTable(NodoSentenciaSQL):
    """Representa una sentencia CREATE TABLE."""
    def __init__(self, nombre_tabla_token, definiciones_columna):
        self.nombre_tabla_token = nombre_tabla_token # Token IDENTIFICADOR
        self.definiciones_columna = definiciones_columna # Lista de NodoDefinicionColumna

    def __repr__(self, indent=0):
        indent_str = "  " * indent
        cols_repr = "\n".join([col.__repr__(indent + 2) for col in self.definiciones_columna])
        return (f"{indent_str}NodoCreateTable(tabla='{self.nombre_tabla_token.lexema}', columnas=[\n"
                f"{cols_repr}\n"
                f"{indent_str}  ]\n"
                f"{indent_str})")

class NodoDefinicionColumna(NodoAST_SQL):
    """Representa la definición de una columna en CREATE TABLE."""
    def __init__(self, nombre_columna_token, tipo_dato_token, restricciones_tokens=None):
        self.nombre_columna_token = nombre_columna_token # Token IDENTIFICADOR
        self.tipo_dato_token = tipo_dato_token       # Token del tipo de dato (puede ser PALABRA_CLAVE o TIPO_DATO)
        self.restricciones_tokens = restricciones_tokens if restricciones_tokens is not None else [] 
 # Lista de tokens o nodos de restricción

    def __repr__(self, indent=0):
        indent_str = "  " * indent
        restrs_repr = ", ".join([str(r.lexema if hasattr(r, 'lexema') else r) for r in self.restricciones_tokens])
        return (f"{indent_str}NodoDefinicionColumna(nombre='{self.nombre_columna_token.lexema}', "
                f"tipo='{self.tipo_dato_token.lexema}'" +
                (f", restricciones=[{restrs_repr}]" if self.restricciones_tokens else "") + ")")

# --- Nodos para DML (Data Manipulation Language) ---
class NodoInsert(NodoSentenciaSQL):
    """Representa una sentencia INSERT INTO."""
    def __init__(self, nombre_tabla_token, columnas_lista_tokens, valores_lista_nodos):
        self.nombre_tabla_token = nombre_tabla_token # Token IDENTIFICADOR
        # Lista de tokens IDENTIFICADOR para las columnas, o None/lista vacía si no se especifican.
        self.columnas_lista_tokens = columnas_lista_tokens 
        # Lista de listas de nodos de expresión (literales) para los VALUES.
        # Cada sublista representa una fila de valores.
        self.filas_valores_lista_nodos = valores_lista_nodos   

    def __repr__(self, indent=0):
        indent_str = "  " * indent
        cols_repr = ", ".join([t.lexema for t in self.columnas_lista_tokens]) if self.columnas_lista_tokens else "TODAS (implícito)"
        
        filas_vals_repr_list = []
        for fila_nodos in self.filas_valores_lista_nodos:
            vals_items_repr = ", ".join([val_nodo.__repr__(0) for val_nodo in fila_nodos]) # indent 0 para valores en línea
            filas_vals_repr_list.append(f"{indent_str}    ({vals_items_repr})")
        filas_vals_repr = "\n".join(filas_vals_repr_list)

        return (f"{indent_str}NodoInsert(tabla='{self.nombre_tabla_token.lexema}',\n"
                f"{indent_str}  columnas=[{cols_repr}],\n"
                f"{indent_str}  valores=[\n{filas_vals_repr}\n{indent_str}  ]\n"
                f"{indent_str})")

class NodoSelect(NodoSentenciaSQL):
    """Representa una sentencia SELECT (simplificada)."""
    def __init__(self, columnas_select_nodos, tabla_from_token, where_condicion_nodo=None):
        # columnas_select_nodos puede ser una lista de NodoIdentificador/NodoExpresion o un NodoAsterisco.
        self.columnas_select_nodos = columnas_select_nodos
        self.tabla_from_token = tabla_from_token # Token IDENTIFICADOR
        self.where_condicion_nodo = where_condicion_nodo # NodoExpresionSQL (opcional)

    def __repr__(self, indent=0):
        indent_str = "  " * indent
        cols_repr = "\n".join([col.__repr__(indent + 2) for col in self.columnas_select_nodos])
        where_repr = self.where_condicion_nodo.__repr__(indent + 1) if self.where_condicion_nodo else f"{indent_str}  None"
        return (f"{indent_str}NodoSelect(\n"
                f"{indent_str}  columnas=[\n{cols_repr}\n{indent_str}  ],\n"
                f"{indent_str}  from_tabla='{self.tabla_from_token.lexema}',\n"
                f"{indent_str}  where_condicion=\n{where_repr}\n"
                f"{indent_str})")

class NodoUpdate(NodoSentenciaSQL):
    """Representa una sentencia UPDATE (simplificada)."""
    def __init__(self, nombre_tabla_token, asignaciones_set, where_condicion_nodo=None):
        self.nombre_tabla_token = nombre_tabla_token # Token IDENTIFICADOR
        self.asignaciones_set = asignaciones_set     # Lista de tuplas (TokenColumna, NodoExpresionSQL)
        self.where_condicion_nodo = where_condicion_nodo # NodoExpresionSQL (opcional)

    def __repr__(self, indent=0):
        indent_str = "  " * indent
        set_repr_list = []
        for col_token, val_nodo in self.asignaciones_set:
            val_repr = val_nodo.__repr__(indent + 3) if val_nodo else f"{indent_str}    None"
            set_repr_list.append(f"{indent_str}    {col_token.lexema} = \n{val_repr}")
        set_repr = "\n".join(set_repr_list)
        where_repr = self.where_condicion_nodo.__repr__(indent + 1) if self.where_condicion_nodo else f"{indent_str}  None"
        return (f"{indent_str}NodoUpdate(tabla='{self.nombre_tabla_token.lexema}',\n"
                f"{indent_str}  set=[\n{set_repr}\n{indent_str}  ],\n"
                f"{indent_str}  where_condicion=\n{where_repr}\n"
                f"{indent_str})")

class NodoUpdate(NodoSentenciaSQL):
    """Representa una sentencia UPDATE."""
    def __init__(self, nombre_tabla_token, asignaciones_set, where_condicion_nodo=None):
        self.nombre_tabla_token = nombre_tabla_token # Token IDENTIFICADOR de la tabla.
        self.asignaciones_set = asignaciones_set     # Lista de tuplas (TokenColumna, NodoExpresionSQL).
        self.where_condicion_nodo = where_condicion_nodo # NodoExpresionBinariaSQL (opcional).

    def __repr__(self, indent=0):
        indent_str = "  " * indent
        set_repr_list = []
        for col_token, val_nodo in self.asignaciones_set:
            # Asumimos que col_token es un Token y val_nodo es un NodoAST_SQL
            val_repr = val_nodo.__repr__(indent + 3) if val_nodo else f"{indent_str}    None"
            set_repr_list.append(f"{indent_str}    {col_token.lexema} =\n{val_repr}")
        set_repr = "\n".join(set_repr_list)
        
        where_repr = self.where_condicion_nodo.__repr__(indent + 1) if self.where_condicion_nodo else f"{indent_str}  None"
        
        return (f"{indent_str}NodoUpdate(tabla='{self.nombre_tabla_token.lexema}',\n"
                f"{indent_str}  set=[\n{set_repr}\n{indent_str}  ],\n"
                f"{indent_str}  where_condicion=\n{where_repr}\n"
                f"{indent_str})")
    
class NodoDelete(NodoSentenciaSQL):
    """Representa una sentencia DELETE FROM (simplificada)."""
    def __init__(self, nombre_tabla_token, where_condicion_nodo=None):
        self.nombre_tabla_token = nombre_tabla_token # Token IDENTIFICADOR de la tabla.
        self.where_condicion_nodo = where_condicion_nodo # NodoExpresionBinariaSQL (opcional).

    def __repr__(self, indent=0):
        indent_str = "  " * indent
        where_repr = self.where_condicion_nodo.__repr__(indent + 1) if self.where_condicion_nodo else f"{indent_str}  None"
        return (f"{indent_str}NodoDelete(from_tabla='{self.nombre_tabla_token.lexema}',\n"
                f"{indent_str}  where_condicion=\n{where_repr}\n"
                f"{indent_str})")

# --- Nodos para T-SQL específico y Expresiones ---
class NodoPrint(NodoSentenciaSQL):
    """Representa una sentencia PRINT de T-SQL."""
    def __init__(self, expresion_nodo):
        self.expresion_nodo = expresion_nodo # NodoExpresionSQL

    def __repr__(self, indent=0):
        indent_str = "  " * indent
        expr_repr = self.expresion_nodo.__repr__(indent + 1) if self.expresion_nodo else f"{indent_str}  None"
        return (f"{indent_str}NodoPrint(expresion=\n{expr_repr}\n{indent_str})")

class NodoDeclareVariable(NodoSentenciaSQL):
    """Representa una declaración de variable DECLARE @var TIPO."""
    def __init__(self, nombre_variable_token, tipo_dato_token, valor_inicial_nodo=None):
        self.nombre_variable_token = nombre_variable_token # Token IDENTIFICADOR (ej: @MiVar)
        self.tipo_dato_token = tipo_dato_token         # Token del tipo de dato
        self.valor_inicial_nodo = valor_inicial_nodo   # NodoExpresionSQL (opcional)

    def __repr__(self, indent=0):
        indent_str = "  " * indent
        init_val_repr = ""
        if self.valor_inicial_nodo:
            init_val_repr = f",\n{indent_str}  valor_inicial=\n{self.valor_inicial_nodo.__repr__(indent + 2)}"
        return (f"{indent_str}NodoDeclareVariable(nombre='{self.nombre_variable_token.lexema}', "
                f"tipo='{self.tipo_dato_token.lexema}'{init_val_repr}\n{indent_str})")

class NodoSetVariable(NodoSentenciaSQL):
    """Representa una asignación SET @var = expresion."""
    def __init__(self, nombre_variable_token, expresion_nodo):
        self.nombre_variable_token = nombre_variable_token # Token IDENTIFICADOR (ej: @MiVar)
        self.expresion_nodo = expresion_nodo             # NodoExpresionSQL

    def __repr__(self, indent=0):
        indent_str = "  " * indent
        expr_repr = self.expresion_nodo.__repr__(indent + 1) if self.expresion_nodo else f"{indent_str}  None"
        return (f"{indent_str}NodoSetVariable(variable='{self.nombre_variable_token.lexema}',\n"
                f"{indent_str}  expresion=\n{expr_repr}\n{indent_str})")

class NodoGo(NodoSentenciaSQL):
    """Representa un separador de lotes GO (T-SQL)."""
    def __repr__(self, indent=0):
        return f"{'  ' * indent}NodoGo()"

# Nodos para Expresiones SQL (pueden ser similares a los de Pascal, pero con semántica SQL)
class NodoExpresionSQL(NodoAST_SQL):
    """Clase base para expresiones SQL."""
    pass

class NodoIdentificadorSQL(NodoExpresionSQL):
    """Identificador en SQL (nombre de columna, variable @var, nombre de tabla)."""
    def __init__(self, id_token):
        self.id_token = id_token
        self.nombre = id_token.lexema # Puede incluir @, #, [], ""

    def __repr__(self, indent=0):
        return f"{'  ' * indent}NodoIdentificadorSQL(nombre='{self.nombre}')"

class NodoLiteralSQL(NodoExpresionSQL):
    """Literal en SQL (cadena, número)."""
    def __init__(self, literal_token):
        self.literal_token = literal_token
        self.valor = literal_token.valor 

    def __repr__(self, indent=0):
        return f"{'  ' * indent}NodoLiteralSQL(tipo={self.literal_token.tipo}, valor={repr(self.valor)})"

class NodoExpresionBinariaSQL(NodoExpresionSQL):
    """Expresión binaria en SQL (ej: col = 'valor', precio > 100, cantidad + 1)."""
    def __init__(self, operador_token, operando_izq_nodo, operando_der_nodo):
        self.operador_token = operador_token
        self.operando_izq_nodo = operando_izq_nodo
        self.operando_der_nodo = operando_der_nodo

    def __repr__(self, indent=0):
        indent_str = "  " * indent
        izq_repr = self.operando_izq_nodo.__repr__(indent + 1) if self.operando_izq_nodo else f"{indent_str}  Izquierda: None"
        der_repr = self.operando_der_nodo.__repr__(indent + 1) if self.operando_der_nodo else f"{indent_str}  Derecha: None"
        return (f"{indent_str}NodoExpresionBinariaSQL(operador='{self.operador_token.lexema}',\n"
                f"{izq_repr},\n"
                f"{der_repr}\n"
                f"{indent_str})")

class NodoFuncionSQL(NodoExpresionSQL): # Para funciones como GETDATE(), COUNT(*)
    def __init__(self, nombre_funcion_token, argumentos_nodos=None):
        self.nombre_funcion_token = nombre_funcion_token
        self.argumentos_nodos = argumentos_nodos if argumentos_nodos is not None else []

    def __repr__(self, indent=0):
        indent_str = "  " * indent
        if not self.argumentos_nodos:
            args_repr = "[]"
        else:
            args_items_repr = "\n".join([arg.__repr__(indent + 2) for arg in self.argumentos_nodos])
            args_repr = f"[\n{args_items_repr}\n{indent_str}  ]"
        return (f"{indent_str}NodoFuncionSQL(nombre='{self.nombre_funcion_token.lexema}',\n"
                f"{indent_str}  argumentos={args_repr}\n"
                f"{indent_str})")

class NodoAsteriscoSQL(NodoExpresionSQL): # Para SELECT *
    def __init__(self, asterisco_token):
        self.asterisco_token = asterisco_token

    def __repr__(self, indent=0):
        return f"{'  ' * indent}NodoAsteriscoSQL()"

# --- Clase ParserTSQL ---
class ParserTSQL:
    def __init__(self, tokens):
        """
        Inicializa el parser con la lista de tokens generada por el LexerTSQL.
        Filtra los tokens de WHITESPACE_SQL ya que no son relevantes para el análisis sintáctico.
        """
        self.tokens = [token for token in tokens if token.tipo != 'WHITESPACE_SQL']
        self.posicion_actual = 0
        self.token_actual = self.tokens[self.posicion_actual] if self.tokens else None
        self.errores_sintacticos = []
        # La tabla de símbolos para T-SQL podría ser necesaria para variables, tablas temporales, etc.
        # from nucleo_compilador.tabla_simbolos import TablaSimbolos # Mover importación arriba
        # self.tabla_simbolos = TablaSimbolos() # Se podría inicializar aquí si es necesaria globalmente.

    def _avanzar(self):
        """Avanza al siguiente token en la lista."""
        self.posicion_actual += 1
        if self.posicion_actual < len(self.tokens):
            self.token_actual = self.tokens[self.posicion_actual]
        else:
            # Si se llega al final, el token actual podría ser el último token EOF
            # o None si la lista de tokens estaba vacía o se avanzó más allá del EOF.
            self.token_actual = self.tokens[-1] if self.tokens and self.tokens[-1].tipo == TT_EOF_SQL else None

    def _error_sintactico(self, mensaje_esperado):
        """Registra un error sintáctico y lanza una excepción para detener el parsing."""
        mensaje = "Error Sintáctico Desconocido"
        if self.token_actual and self.token_actual.tipo != TT_EOF_SQL:
            mensaje = (f"Error Sintáctico en L{self.token_actual.linea}:C{self.token_actual.columna}. "
                       f"Se esperaba {mensaje_esperado}, pero se encontró '{self.token_actual.lexema}' (tipo: {self.token_actual.tipo}).")
        elif self.token_actual and self.token_actual.tipo == TT_EOF_SQL:
            mensaje = (f"Error Sintáctico: Final inesperado del archivo (L{self.token_actual.linea}:C{self.token_actual.columna}). "
                       f"Se esperaba {mensaje_esperado}.")
        else: 
            # Intentar obtener la posición del último token significativo si token_actual es None
            # Esto puede ocurrir si se esperaba algo después del último token real.
            last_meaningful_token = self.tokens[-2] if len(self.tokens) > 1 and self.tokens[-1].tipo == TT_EOF_SQL else \
                                  (self.tokens[-1] if self.tokens else None)
            linea_aprox = last_meaningful_token.linea if last_meaningful_token else 'desconocida'
            col_aprox = last_meaningful_token.columna if last_meaningful_token else 'desconocida'
            mensaje = (f"Error Sintáctico: Final inesperado de la entrada (cerca de L{linea_aprox}:C{col_aprox}). "
                       f"Se esperaba {mensaje_esperado}.")

        self.errores_sintacticos.append(mensaje)
        print(mensaje) 
        raise SyntaxError(mensaje) 

    def _consumir(self, tipo_token_esperado, lexema_esperado=None, es_sensible_mayusculas=False):
        """
        Verifica el token actual. Si coincide, lo consume y avanza. Si no, reporta error.
        Devuelve el token consumido.
        """
        token_a_consumir = self.token_actual
        if token_a_consumir and token_a_consumir.tipo == tipo_token_esperado:
            lexema_actual_para_comparar = token_a_consumir.lexema if es_sensible_mayusculas else token_a_consumir.lexema.lower()
            lexema_esperado_para_comparar = lexema_esperado if es_sensible_mayusculas or lexema_esperado is None else lexema_esperado.lower()

            if lexema_esperado is None or lexema_actual_para_comparar == lexema_esperado_para_comparar:
                self._avanzar()
                return token_a_consumir
            else:
                self._error_sintactico(f"el lexema '{lexema_esperado}' para el token de tipo '{tipo_token_esperado}'")
        else:
            if lexema_esperado:
                self._error_sintactico(f"el lexema '{lexema_esperado}' (tipo: {tipo_token_esperado})")
            else:
                self._error_sintactico(f"un token de tipo '{tipo_token_esperado}'")
        # No se debería llegar aquí si _error_sintactico siempre lanza excepción.
        return None 

    def parse(self):
        """
        Punto de entrada principal para el análisis sintáctico del script T-SQL.
        Devuelve: Un NodoScriptSQL que representa el AST del script completo, o None si hay errores.
        """
        ast_script_nodo = None
        try:
            ast_script_nodo = self.parse_script()
            
            if not self.errores_sintacticos and self.token_actual and self.token_actual.tipo != TT_EOF_SQL:
                self._error_sintactico("el final del script (EOF) o un separador de lote 'GO'")
            
            if not self.errores_sintacticos and ast_script_nodo:
                 print("Análisis sintáctico de T-SQL y construcción de AST completados exitosamente.")
            
        except SyntaxError:
            print(f"Análisis sintáctico de T-SQL detenido debido a errores.")
            ast_script_nodo = None 
        except Exception as e:
            print(f"Error inesperado durante el parsing de T-SQL: {e}")
            import traceback
            traceback.print_exc()
            ast_script_nodo = None
        
        if self.errores_sintacticos and not ast_script_nodo:
             print(f"Resumen: Parsing de T-SQL falló con {len(self.errores_sintacticos)} error(es) sintáctico(s) detectado(s).")
        
        return ast_script_nodo

    def parse_script(self):
        elementos_script = []
        while self.token_actual and self.token_actual.tipo != TT_EOF_SQL:
            print(f"[DEBUG ParserTSQL.parse_script] Inicio de iteración. Token actual: {self.token_actual}")

            token_posicion_antes_sentencia = self.posicion_actual
            elemento = self.parse_sentencia_o_go()
            
            if elemento:
                elementos_script.append(elemento)
            elif self.errores_sintacticos: # Si _error_sintactico fue llamado y lanzó excepción
                break
            elif self.token_actual and self.token_actual.tipo == TT_PUNTO_Y_COMA:
                self._consumir(TT_PUNTO_Y_COMA) # Consumir y continuar
                continue
            elif self.token_actual and self.token_actual.tipo != TT_EOF_SQL:
                # Si no se parseó un elemento, no hay errores, y la posición no avanzó,
                # significa que estamos atascados.
                if self.posicion_actual == token_posicion_antes_sentencia:
                    # print(f"[DEBUG parse_script] Atascado en token: {self.token_actual}. Posición no avanzó.")
                    self._error_sintactico("una sentencia SQL válida, 'GO', o el final del script")
                    break # Salir porque estamos atascados
                # else: La posición avanzó (probablemente _consumir_hasta_fin_sentencia_o_go), continuar.
            # else: es EOF, el bucle while terminará naturalmente.
            
        return NodoScriptSQL(elementos_script)

    def parse_sentencia_o_go(self):
        """
        Determina si el token actual es 'GO' o el inicio de otra sentencia SQL.
        Devuelve: NodoGo o un nodo de sentencia SQL.
        """
        if self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE and \
           self.token_actual.lexema.lower() == 'go':
            token_go = self._consumir(TT_PALABRA_CLAVE, 'go')
            # Opcionalmente consumir un punto y coma después de GO, aunque no es estándar.
            if self.token_actual and self.token_actual.tipo == TT_PUNTO_Y_COMA:
                self._consumir(TT_PUNTO_Y_COMA)
            return NodoGo()
        else:
            # Si no es 'GO', intenta parsear una sentencia SQL normal.
            return self.parse_sentencia_sql_principal()
        
    
    def _parse_print_statement(self):
        """Parsea una sentencia PRINT expresion."""
        self._consumir(TT_PALABRA_CLAVE, 'print')
        # PRINT espera una expresión. Usaremos _parse_expresion_sql() que es más general.
        expresion_nodo = self._parse_expresion_sql() 
        return NodoPrint(expresion_nodo)
        # PRINT puede ir seguido de una cadena, un número o un identificador (variable @)
        # if self.token_actual and self.token_actual.tipo in [TT_LITERAL_CADENA, TT_LITERAL_NUMERICO, TT_IDENTIFICADOR]:
        #     if self.token_actual.tipo == TT_IDENTIFICADOR:
        #         # Para T-SQL, un identificador en PRINT suele ser una variable @nombre
        #         # o una función como @@VERSION.
        #         # Nuestro lexer ya debería marcar @nombre y @@VERSION como TT_IDENTIFICADOR.
        #         expresion_nodo = NodoIdentificadorSQL(self._consumir(TT_IDENTIFICADOR))
        #     else: # Es un literal
        #         expresion_nodo = NodoLiteralSQL(self._consumir(self.token_actual.tipo))
        # else:
        #     self._error_sintactico("una expresión (cadena, número o variable) después de PRINT")
        
        # return NodoPrint(expresion_nodo)
    
    def _parse_insert_statement(self):
        """Parsea una sentencia INSERT INTO."""
        self._consumir(TT_PALABRA_CLAVE, 'insert')
        self._consumir(TT_PALABRA_CLAVE, 'into')
        
        nombre_tabla_token = self._consumir(TT_IDENTIFICADOR)
        
        columnas_lista_tokens = None
        if self.token_actual and self.token_actual.tipo == TT_PARENTESIS_IZQ:
            columnas_lista_tokens = self._parse_lista_nombres_columnas()
        
        self._consumir(TT_PALABRA_CLAVE, 'values')
        
        # INSERT puede tener múltiples tuplas de valores, ej: VALUES (1,2), (3,4)
        # Por ahora, parsearemos una sola tupla de valores.
        # Para múltiples tuplas, necesitaríamos un bucle aquí que busque comas.
        filas_valores_lista_nodos = []
        filas_valores_lista_nodos.append(self._parse_una_fila_de_valores())

        # (Opcional: bucle para múltiples filas de VALUES)
        while self.token_actual and self.token_actual.tipo == TT_COMA:
            self._consumir(TT_COMA) # Consume la coma entre las filas de valores
            filas_valores_lista_nodos.append(self._parse_una_fila_de_valores())
            
        return NodoInsert(nombre_tabla_token, columnas_lista_tokens, filas_valores_lista_nodos)
    
    def _parse_lista_nombres_columnas(self):
        """Parsea una lista de nombres de columna entre paréntesis: (col1, col2, ...)."""
        self._consumir(TT_PARENTESIS_IZQ)
        columnas = []
        if self.token_actual and self.token_actual.tipo != TT_PARENTESIS_DER: # Asegurar que no esté vacío
            columnas.append(self._consumir(TT_IDENTIFICADOR))
            while self.token_actual and self.token_actual.tipo == TT_COMA:
                self._consumir(TT_COMA)
                columnas.append(self._consumir(TT_IDENTIFICADOR))
        self._consumir(TT_PARENTESIS_DER)
        return columnas if columnas else None # Devolver None si la lista estaba vacía ( )
    
    def _parse_una_fila_de_valores(self):
        self._consumir(TT_PARENTESIS_IZQ)
        valores_nodos = []
        if self.token_actual and self.token_actual.tipo != TT_PARENTESIS_DER: 
            valores_nodos.append(self._parse_expresion_sql()) # Usar el parser de expresiones más general
            while self.token_actual and self.token_actual.tipo == TT_COMA:
                self._consumir(TT_COMA)
                valores_nodos.append(self._parse_expresion_sql()) # Usar el parser de expresiones más general
        self._consumir(TT_PARENTESIS_DER)
        return valores_nodos
    
    def _parse_select_statement(self):
        """Parsea una sentencia SELECT FROM [WHERE]."""
        self._consumir(TT_PALABRA_CLAVE, 'select')
        
        columnas_select_nodos = self._parse_lista_de_seleccion()
        
        self._consumir(TT_PALABRA_CLAVE, 'from')
        tabla_from_token = self._consumir(TT_IDENTIFICADOR) # Asume un solo nombre de tabla por ahora
        
        where_condicion_nodo = None
        if self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE and \
           self.token_actual.lexema.lower() == 'where':
            where_condicion_nodo = self._parse_clausula_where_simple()
            
        return NodoSelect(columnas_select_nodos, tabla_from_token, where_condicion_nodo)

    def _parse_lista_de_seleccion(self):
        """Parsea la lista de columnas en un SELECT (ej: col1, col2 o *)."""
        elementos_seleccion = []
        # Parsea el primer elemento (columna o *)
        elementos_seleccion.append(self._parse_elemento_seleccion())
        
        # Parsear elementos adicionales separados por comas
        while self.token_actual and self.token_actual.tipo == TT_COMA:
            self._consumir(TT_COMA)
            elementos_seleccion.append(self._parse_elemento_seleccion())
            
        return elementos_seleccion

    def _parse_elemento_seleccion(self): # Anteriormente _parse_expresion_sql_simple_o_asterisco
        """Parsea un elemento en la lista SELECT: *, identificador, o expresión simple."""
        if self.token_actual and self.token_actual.tipo == TT_ASTERISCO:
            return NodoAsteriscoSQL(self._consumir(TT_ASTERISCO))
        else:
            # Aquí se podría llamar a un parser de expresiones más completo si se desea
            # permitir SELECT col1 + col2 AS Suma, etc.
            # Por ahora, mantenemos la llamada a _parse_expresion_sql para expresiones simples.
            return self._parse_expresion_sql() 

    def _parse_clausula_where_simple(self):
        """Parsea una cláusula WHERE simple (ej: columna = valor)."""
        self._consumir(TT_PALABRA_CLAVE, 'where')
        # Por ahora, una condición WHERE muy simple: Identificador OPERADOR_COMPARACION Literal/Identificador
        # Se necesitaría un parser de expresiones más completo para condiciones complejas.
        
        nodo_izq = self._parse_expresion_sql_simple() # Columna o variable
        
        if not (self.token_actual and self.token_actual.tipo == TT_OPERADOR_COMPARACION):
            self._error_sintactico("un operador de comparación en la cláusula WHERE")
        
        operador_token = self._consumir(TT_OPERADOR_COMPARACION)
        
        nodo_der = self._parse_expresion_sql_simple() # Valor literal o otra columna/variable
        
        return NodoExpresionBinariaSQL(operador_token, nodo_izq, nodo_der)
    
    def _parse_update_statement(self):
        """Parsea una sentencia UPDATE nombre_tabla SET col1 = val1 ... [WHERE cond]."""
        self._consumir(TT_PALABRA_CLAVE, 'update')
        nombre_tabla_token = self._consumir(TT_IDENTIFICADOR)
        
        self._consumir(TT_PALABRA_CLAVE, 'set')
        asignaciones_set = self._parse_lista_asignaciones_set()
        
        where_condicion_nodo = self._parse_clausula_where_opcional()
            
        return NodoUpdate(nombre_tabla_token, asignaciones_set, where_condicion_nodo)
    
    def _parse_clausula_where_opcional(self):
        if self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE and \
           self.token_actual.lexema.lower() == 'where':
            self._consumir(TT_PALABRA_CLAVE, 'where') 
            # La condición WHERE es una expresión (potencialmente compleja)
            return self._parse_expresion_sql()
        return None

    def _parse_lista_asignaciones_set(self):
        asignaciones = []
        col_token = self._consumir(TT_IDENTIFICADOR)
        self._consumir(TT_OPERADOR_COMPARACION, '=') # En SET, '=' es el operador de asignación
        expr_nodo = self._parse_expresion_sql() # Usar el parser de expresiones más general
        asignaciones.append((col_token, expr_nodo))
        while self.token_actual and self.token_actual.tipo == TT_COMA:
            self._consumir(TT_COMA)
            col_token = self._consumir(TT_IDENTIFICADOR)
            self._consumir(TT_OPERADOR_COMPARACION, '=')
            expr_nodo = self._parse_expresion_sql() # Usar el parser de expresiones más general
            asignaciones.append((col_token, expr_nodo))
        return asignaciones

    # --- JERARQUÍA DE PARSING DE EXPRESIONES SQL ---
    # Similar a Pascal, para manejar precedencia.
    # expresion -> termino_logico (OR) -> factor_logico (AND) -> expresion_unaria_logica (NOT) -> expresion_comparativa -> expresion_aditiva -> termino_multiplicativo -> factor_sql

    
    def _parse_expresion_sql_simple(self):
        """Parsea una expresión SQL simple (literal, identificador)."""
        # Este es un placeholder muy básico para expresiones.
        # Un parser de expresiones SQL completo sería más complejo.
        if self.token_actual and self.token_actual.tipo in [TT_LITERAL_CADENA, TT_LITERAL_NUMERICO]:
            return NodoLiteralSQL(self._consumir(self.token_actual.tipo))
        elif self.token_actual and self.token_actual.tipo == TT_IDENTIFICADOR:
            # Podría ser una variable @var o una función como GETDATE()
            # o incluso una palabra clave como NULL.
            # Por ahora, solo identificador simple.
            return NodoIdentificadorSQL(self._consumir(TT_IDENTIFICADOR))
        elif self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE and \
             self.token_actual.lexema.lower() == 'null':
            # Crear un NodoLiteralSQL para NULL
            token_null = self._consumir(TT_PALABRA_CLAVE, 'null')
            return NodoLiteralSQL(Token(TT_LITERAL_CADENA, 'NULL', token_null.linea, token_null.columna, valor=None)) # Representar SQL NULL como Python None
        else:
            self._error_sintactico("un literal (cadena, número) o identificador como valor")
        return None
    
    def _parse_delete_statement(self):
        """Parsea una sentencia DELETE [FROM] nombre_tabla [WHERE cond]."""
        self._consumir(TT_PALABRA_CLAVE, 'delete')
        
        # La palabra clave FROM es opcional en DELETE
        if self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE and \
           self.token_actual.lexema.lower() == 'from':
            self._consumir(TT_PALABRA_CLAVE, 'from')
            
        nombre_tabla_token = self._consumir(TT_IDENTIFICADOR)
        
        where_condicion_nodo = self._parse_clausula_where_opcional()
            
        return NodoDelete(nombre_tabla_token, where_condicion_nodo)


    def parse_sentencia_sql_principal(self):
        if not self.token_actual or self.token_actual.tipo == TT_EOF_SQL:
            self._error_sintactico("una sentencia SQL válida") # No debería llegar aquí si parse_script funciona
            return None 

        nodo_sentencia = None
        token_inicio_sentencia = self.token_actual
        # print(f"[DEBUG parse_sentencia_sql_principal] Token de inicio: {token_inicio_sentencia}")

        if token_inicio_sentencia.tipo == TT_PALABRA_CLAVE:
            palabra_clave = token_inicio_sentencia.lexema.lower()
            if palabra_clave == 'create':
                nodo_sentencia = self._parse_create_statement()
            elif palabra_clave == 'insert':
                nodo_sentencia = self._parse_insert_statement()
            elif palabra_clave == 'select': 
                nodo_sentencia = self._parse_select_statement()
            elif palabra_clave == 'print':
                nodo_sentencia = self._parse_print_statement()
            elif palabra_clave == 'update':
                nodo_sentencia = self._parse_update_statement()
            elif palabra_clave == 'delete':
                nodo_sentencia = self._parse_delete_statement()
            elif palabra_clave == 'declare':
                nodo_sentencia = self._parse_declare_statement()
            elif palabra_clave == 'set':    
                nodo_sentencia = self._parse_set_statement()
            elif palabra_clave in ['update', 'delete', 'declare', 'set', 'if', 'begin', 'alter', 'drop', 'exec', 'execute']:
                print(f"INFO (ParserTSQL): Parsing de '{palabra_clave}' no implementado aún. Saltando sentencia.")
                self._consumir_hasta_fin_sentencia_o_go()
                return None 
            else:
                self._error_sintactico(f"una palabra clave de inicio de sentencia SQL válida reconocida. Se encontró '{palabra_clave}'.")
        else:
            self._error_sintactico(f"una palabra clave de inicio de sentencia SQL. Se encontró '{token_inicio_sentencia.lexema}' (tipo: {token_inicio_sentencia.tipo}).")

        # Consumir el punto y coma final si existe y se generó un nodo de sentencia
        # y no es el inicio de un GO (GO no debe tener ; antes)
        if nodo_sentencia and self.token_actual and self.token_actual.tipo == TT_PUNTO_Y_COMA:
            # Verificar que lo que sigue no sea GO, ya que GO puede ir sin ;
            siguiente_token_es_go = False
            if self.posicion_actual + 1 < len(self.tokens):
                token_siguiente = self.tokens[self.posicion_actual + 1]
                if token_siguiente.tipo == TT_PALABRA_CLAVE and token_siguiente.lexema.lower() == 'go':
                    siguiente_token_es_go = True
            
            if not (self.token_actual.tipo == TT_PALABRA_CLAVE and self.token_actual.lexema.lower() == 'go'): # No consumir ; si es GO
                 # Esta lógica es un poco compleja. Simplificando: si hay un ';', lo consumimos.
                 # El lexer de T-SQL a menudo trata ';' como opcional o parte de la sentencia.
                 # Si el ; es parte de la sentencia (ej. PRINT 'hola';), _consumir_hasta_fin_sentencia_o_go lo manejaría.
                 # Si el ; es un terminador opcional, esta lógica es para consumirlo.
                 # Por ahora, si está ahí después de una sentencia parseada, lo consumimos.
                self._consumir(TT_PUNTO_Y_COMA)
            
        return nodo_sentencia
    
    def _parse_create_statement(self):
        # print(f"[DEBUG _parse_create_statement] Token actual al entrar: {self.token_actual}")
        self._consumir(TT_PALABRA_CLAVE, 'create') 
        # print(f"[DEBUG _parse_create_statement] Después de consumir CREATE. Token actual: {self.token_actual}")
        
        if self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE and \
           self.token_actual.lexema.lower() == 'table':
            nodo_tabla = self._parse_create_table_statement()
            # print(f"[DEBUG _parse_create_statement] Retornando desde rama TABLE: {nodo_tabla}")
            return nodo_tabla
        else:
            self._error_sintactico("TABLE (u otro objeto CREATE válido) después de CREATE")
        return None

    # --- NUEVOS MÉTODOS PARA CREATE TABLE ---
    # def _parse_create_statement(self):
    #     print(f"[DEBUG _parse_create_statement] Token actual al entrar: {self.token_actual}") # NUEVA DEPURACIÓN
    #     # Se asume que el token 'create' ya fue identificado por el llamador,
    #     # pero lo consumimos aquí para asegurar el avance.
    #     self._consumir(TT_PALABRA_CLAVE, 'create') 
    #     print(f"[DEBUG _parse_create_statement] Después de consumir CREATE. Token actual: {self.token_actual}") # NUEVA DEPURACIÓN
        
    #     if self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE and \
    #        self.token_actual.lexema.lower() == 'table':
    #         nodo_tabla = self._parse_create_table_statement()
    #         print(f"[DEBUG _parse_create_statement] Retornando desde rama TABLE: {nodo_tabla}") # NUEVA DEPURACIÓN
    #         return nodo_tabla
    #     else:
    #         self._error_sintactico("TABLE (u otro objeto CREATE válido) después de CREATE")
    #     # Esta línea no debería alcanzarse si _error_sintactico lanza excepción
    #     print("[DEBUG _parse_create_statement] Retornando None (rama no TABLE o error previo)") # NUEVA DEPURACIÓN
    #     return None

    def _parse_create_table_statement(self):
        """Parsea la parte específica de CREATE TABLE."""
        self._consumir(TT_PALABRA_CLAVE, 'table') # Consume TABLE
        
        nombre_tabla_token = self._consumir(TT_IDENTIFICADOR) # Consume el nombre de la tabla
        # Aquí se podría manejar nombres de tabla de múltiples partes (schema.table)
        
        self._consumir(TT_PARENTESIS_IZQ) # Consume '('
        
        definiciones_columna = self._parse_lista_definiciones_columna()
        
        self._consumir(TT_PARENTESIS_DER) # Consume ')'
        
        # Aquí se podrían parsear opciones de tabla adicionales después del ')'
        
        return NodoCreateTable(nombre_tabla_token, definiciones_columna)
    
    def _parse_declare_statement(self):
        """Parsea una sentencia DECLARE @variable TIPO [= valor_inicial]."""
        self._consumir(TT_PALABRA_CLAVE, 'declare')
        
        # T-SQL puede declarar múltiples variables en una sola sentencia DECLARE, separadas por comas.
        # Ej: DECLARE @var1 INT, @var2 VARCHAR(10) = 'test';
        # Por ahora, simplificaremos a una variable por DECLARE.
        # Para múltiples, necesitaríamos un bucle aquí.
        
        nombre_variable_token = self._consumir(TT_IDENTIFICADOR) # Debe ser @variable
        if not nombre_variable_token.lexema.startswith('@'):
            self._error_sintactico("un nombre de variable que comience con '@' después de DECLARE")

        # La palabra clave AS es opcional en T-SQL antes del tipo de dato en DECLARE
        if self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE and \
           self.token_actual.lexema.lower() == 'as':
            self._consumir(TT_PALABRA_CLAVE, 'as')

        # Parsear el tipo de dato (similar a la definición de columna)
        if not (self.token_actual and (self.token_actual.tipo == TT_PALABRA_CLAVE or self.token_actual.tipo == TT_IDENTIFICADOR)):
            self._error_sintactico("un tipo de dato válido para la variable declarada")
        
        tipo_dato_token_original = self.token_actual 
        self._avanzar() 
        
        tipo_dato_lexema_completo = tipo_dato_token_original.lexema
        # Manejar especificadores de tamaño para tipos como VARCHAR(100)
        if tipo_dato_lexema_completo.lower() in ['varchar', 'nvarchar', 'char', 'nchar', 'decimal', 'numeric']:
            if self.token_actual and self.token_actual.tipo == TT_PARENTESIS_IZQ:
                tipo_dato_lexema_completo += self._consumir(TT_PARENTESIS_IZQ).lexema
                num1_token = self._consumir(TT_LITERAL_NUMERICO)
                tipo_dato_lexema_completo += str(num1_token.valor) 
                if self.token_actual and self.token_actual.tipo == TT_COMA:
                    tipo_dato_lexema_completo += self._consumir(TT_COMA).lexema
                    num2_token = self._consumir(TT_LITERAL_NUMERICO)
                    tipo_dato_lexema_completo += str(num2_token.valor)
                tipo_dato_lexema_completo += self._consumir(TT_PARENTESIS_DER).lexema
        
        tipo_dato_final_token = Token(tipo_dato_token_original.tipo, tipo_dato_lexema_completo, 
                                      tipo_dato_token_original.linea, tipo_dato_token_original.columna, 
                                      valor=tipo_dato_lexema_completo)
        
        # T-SQL permite inicialización opcional: DECLARE @var INT = 10;
        valor_inicial_nodo = None
        if self.token_actual and self.token_actual.tipo == TT_OPERADOR_COMPARACION and self.token_actual.lexema == '=':
            self._consumir(TT_OPERADOR_COMPARACION, '=')
            valor_inicial_nodo = self._parse_expresion_sql() # Parsear la expresión de inicialización

        return NodoDeclareVariable(nombre_variable_token, tipo_dato_final_token, valor_inicial_nodo)

    def _parse_set_statement(self):
        """Parsea una sentencia SET @variable = expresion."""
        self._consumir(TT_PALABRA_CLAVE, 'set')
        nombre_variable_token = self._consumir(TT_IDENTIFICADOR) # Debe ser @variable
        if not nombre_variable_token.lexema.startswith('@'):
            self._error_sintactico("un nombre de variable que comience con '@' después de SET")
            
        self._consumir(TT_OPERADOR_COMPARACION, '=') # En SET, '=' es el operador de asignación
        
        expresion_nodo = self._parse_expresion_sql()
        
        return NodoSetVariable(nombre_variable_token, expresion_nodo)

    def _parse_lista_definiciones_columna(self):
        """Parsea una lista de definiciones de columna dentro de CREATE TABLE."""
        definiciones = []
        
        # Parsea la primera definición de columna (obligatoria)
        definiciones.append(self._parse_definicion_columna())
        
        # Parsea definiciones de columna adicionales separadas por comas
        while self.token_actual and self.token_actual.tipo == TT_COMA:
            self._consumir(TT_COMA)
            definiciones.append(self._parse_definicion_columna())
            
        return definiciones

    def _parse_definicion_columna(self):
        nombre_col_token = self._consumir(TT_IDENTIFICADOR)
        if not (self.token_actual and (self.token_actual.tipo == TT_PALABRA_CLAVE or self.token_actual.tipo == TT_IDENTIFICADOR)):
            self._error_sintactico("un tipo de dato válido para la columna")
        
        tipo_dato_token_original = self.token_actual 
        self._avanzar() 
        
        tipo_dato_lexema_completo = tipo_dato_token_original.lexema
        tipo_dato_linea = tipo_dato_token_original.linea
        tipo_dato_columna = tipo_dato_token_original.columna

        if tipo_dato_lexema_completo.lower() in ['varchar', 'nvarchar', 'char', 'nchar', 'decimal', 'numeric']:
            if self.token_actual and self.token_actual.tipo == TT_PARENTESIS_IZQ:
                tipo_dato_lexema_completo += self._consumir(TT_PARENTESIS_IZQ).lexema
                num1_token = self._consumir(TT_LITERAL_NUMERICO)
                tipo_dato_lexema_completo += str(num1_token.valor) 
                if self.token_actual and self.token_actual.tipo == TT_COMA:
                    tipo_dato_lexema_completo += self._consumir(TT_COMA).lexema
                    num2_token = self._consumir(TT_LITERAL_NUMERICO)
                    tipo_dato_lexema_completo += str(num2_token.valor)
                tipo_dato_lexema_completo += self._consumir(TT_PARENTESIS_DER).lexema
        
        tipo_dato_final_token = Token(tipo_dato_token_original.tipo, tipo_dato_lexema_completo, tipo_dato_linea, tipo_dato_columna, valor=tipo_dato_lexema_completo)
        
        restricciones_tokens = self._parse_restricciones_columna_opcionales()
        return NodoDefinicionColumna(nombre_col_token, tipo_dato_final_token, restricciones_tokens)

    def _parse_restricciones_columna_opcionales(self):
        restricciones = []
        while self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE:
            lexema_actual = self.token_actual.lexema.lower()
            if lexema_actual == 'primary':
                restricciones.append(self._consumir(TT_PALABRA_CLAVE, 'primary'))
                if self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE and self.token_actual.lexema.lower() == 'key':
                    restricciones.append(self._consumir(TT_PALABRA_CLAVE, 'key'))
            elif lexema_actual == 'not':
                restricciones.append(self._consumir(TT_PALABRA_CLAVE, 'not'))
                token_null = self._consumir(TT_PALABRA_CLAVE, 'null') 
                restricciones.append(token_null)
            elif lexema_actual == 'null':
                restricciones.append(self._consumir(TT_PALABRA_CLAVE, 'null'))
            elif lexema_actual == 'unique':
                restricciones.append(self._consumir(TT_PALABRA_CLAVE, 'unique'))
            elif lexema_actual == 'default':
                restricciones.append(self._consumir(TT_PALABRA_CLAVE, 'default'))
                # Manejar valor por defecto: literal, función, o expresión
                if self.token_actual and (
                    self.token_actual.tipo in [TT_LITERAL_CADENA, TT_LITERAL_NUMERICO] or
                    (self.token_actual.tipo == TT_PALABRA_CLAVE and self.token_actual.lexema.lower() in ['getdate', 'current_timestamp'])
                ):
                    default_val_token = self.token_actual
                    self._avanzar() 
                    restricciones.append(default_val_token)
                    if default_val_token.lexema.lower() in ['getdate', 'current_timestamp']:
                        # Si es función, consumir paréntesis si existen, pero NO agregarlos a restricciones
                        if self.token_actual and self.token_actual.tipo == TT_PARENTESIS_IZQ:
                            self._consumir(TT_PARENTESIS_IZQ)
                        if self.token_actual and self.token_actual.tipo == TT_PARENTESIS_DER:
                            self._consumir(TT_PARENTESIS_DER)
                else:
                    self._error_sintactico("un valor literal o función (GETDATE, CURRENT_TIMESTAMP) después de DEFAULT")
            else:
                break 
        return restricciones

    def _consumir_hasta_fin_sentencia_o_go(self):
        """Método de ayuda para saltar tokens hasta el próximo ';' o 'GO' o EOF."""
        # print("[DEBUG Parser] Consumiendo hasta fin de sentencia o GO...")
        while self.token_actual and self.token_actual.tipo != TT_EOF_SQL:
            if self.token_actual.tipo == TT_PUNTO_Y_COMA:
                self._consumir(TT_PUNTO_Y_COMA)
                break
            if self.token_actual.tipo == TT_PALABRA_CLAVE and self.token_actual.lexema.lower() == 'go':
                break # No consumir GO, dejar que parse_sentencia_o_go lo maneje
            self._avanzar()
        # print(f"[DEBUG Parser] Consumido hasta: {self.token_actual}")

    def _parse_factor_sql(self):
        """Parsea los elementos más básicos de una expresión: literales, identificadores, (expresion)."""
        token_actual_val = self.token_actual
        if token_actual_val is None:
            self._error_sintactico("un factor SQL (literal, identificador, variable @, o expresión entre paréntesis)")

        tipo_actual = token_actual_val.tipo
        lexema_actual = token_actual_val.lexema # No convertir a lower aquí para identificadores

        if tipo_actual in [TT_LITERAL_CADENA, TT_LITERAL_NUMERICO]:
            return NodoLiteralSQL(self._consumir(tipo_actual))
        elif tipo_actual == TT_IDENTIFICADOR:
            # Podría ser nombre de columna, variable @, o función como GETDATE()
            # Si es una función, se necesitaría lookahead para '('
            if self.posicion_actual + 1 < len(self.tokens) and \
               self.tokens[self.posicion_actual + 1].tipo == TT_PARENTESIS_IZQ:
                # Asumir que es una llamada a función
                return self._parse_funcion_sql()
            return NodoIdentificadorSQL(self._consumir(TT_IDENTIFICADOR))
        elif tipo_actual == TT_PALABRA_CLAVE and lexema_actual.lower() == 'null':
            token_null = self._consumir(TT_PALABRA_CLAVE, 'null')
            return NodoLiteralSQL(Token(TT_LITERAL_CADENA, 'NULL', token_null.linea, token_null.columna, valor=None))
        elif tipo_actual == TT_PARENTESIS_IZQ:
            self._consumir(TT_PARENTESIS_IZQ)
            nodo_expr_interna = self._parse_expresion_sql() # Llamada recursiva al nivel más alto de expresiones
            self._consumir(TT_PARENTESIS_DER)
            return nodo_expr_interna
        else:
            self._error_sintactico(f"un factor SQL válido. Se encontró '{lexema_actual}'")
        return None

    def _parse_termino_multiplicativo_sql(self):
        """Parsea términos multiplicativos: factor (('*' | '/' | '%') factor)*."""
        nodo = self._parse_factor_sql()
        while self.token_actual and \
              ( (self.token_actual.tipo == TT_OPERADOR_ARITMETICO and self.token_actual.lexema in ['/', '%']) or \
                (self.token_actual.tipo == TT_ASTERISCO and self.token_actual.lexema == '*') ): # Acepta TT_ASTERISCO para '*'
            
            token_operador = self._consumir(self.token_actual.tipo) 
            
            nodo_derecho = self._parse_factor_sql()
            nodo = NodoExpresionBinariaSQL(token_operador, nodo, nodo_derecho)
        return nodo

    def _parse_expresion_aditiva_sql(self):
        """Parsea expresiones aditivas: termino_multiplicativo (('+' | '-') termino_multiplicativo)*."""
        nodo = self._parse_termino_multiplicativo_sql()
        while self.token_actual and \
              self.token_actual.tipo == TT_OPERADOR_ARITMETICO and \
              self.token_actual.lexema in ['+', '-']:
            token_operador = self._consumir(TT_OPERADOR_ARITMETICO)
            nodo_derecho = self._parse_termino_multiplicativo_sql()
            nodo = NodoExpresionBinariaSQL(token_operador, nodo, nodo_derecho)
        return nodo

    def _parse_expresion_comparativa_sql(self):
        """Parsea expresiones comparativas: expresion_aditiva [OPERADOR_COMPARACION expresion_aditiva]."""
        nodo_izquierdo = self._parse_expresion_aditiva_sql()
        if self.token_actual and self.token_actual.tipo == TT_OPERADOR_COMPARACION:
            token_operador = self._consumir(TT_OPERADOR_COMPARACION)
            nodo_derecho = self._parse_expresion_aditiva_sql()
            return NodoExpresionBinariaSQL(token_operador, nodo_izquierdo, nodo_derecho)
        else:
            return nodo_izquierdo
    
    def _parse_expresion_unaria_logica_sql(self):
        """Parsea factores lógicos con NOT: [NOT] expresion_comparativa."""
        token_op_not = None
        if self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE and \
           self.token_actual.lexema.lower() == 'not':
            token_op_not = self._consumir(TT_PALABRA_CLAVE, 'not')
        
        nodo_operando = self._parse_expresion_comparativa_sql() # El operando de NOT es una comparación o algo de mayor precedencia

        if token_op_not:
            # Necesitaríamos un NodoExpresionUnariaSQL
            # Por ahora, no lo creamos, pero la lógica está aquí.
            # return NodoExpresionUnariaSQL(token_op_not, nodo_operando)
            print(f"INFO: Operador NOT parseado pero NodoExpresionUnariaSQL no implementado completamente para AST.")
            return nodo_operando # Devolver el operando por ahora
        else:
            return nodo_operando

    def _parse_termino_logico_sql(self): # Para AND
        """Parsea términos lógicos: expresion_unaria_logica (AND expresion_unaria_logica)*."""
        nodo = self._parse_expresion_unaria_logica_sql()
        while self.token_actual and \
              self.token_actual.tipo == TT_PALABRA_CLAVE and \
              self.token_actual.lexema.lower() == 'and':
            token_operador_and = self._consumir(TT_PALABRA_CLAVE, 'and')
            nodo_derecho = self._parse_expresion_unaria_logica_sql()
            nodo = NodoExpresionBinariaSQL(token_operador_and, nodo, nodo_derecho)
        return nodo

    def _parse_expresion_sql(self): # Punto de entrada para expresiones SQL
        """Parsea expresiones lógicas con OR: termino_logico (OR termino_logico)*."""
        nodo = self._parse_termino_logico_sql()
        while self.token_actual and \
              self.token_actual.tipo == TT_PALABRA_CLAVE and \
              self.token_actual.lexema.lower() == 'or':
            token_operador_or = self._consumir(TT_PALABRA_CLAVE, 'or')
            nodo_derecho = self._parse_termino_logico_sql()
            nodo = NodoExpresionBinariaSQL(token_operador_or, nodo, nodo_derecho)
        return nodo

    def _parse_funcion_sql(self):
        """Parsea una llamada a función SQL simple como GETDATE() o COUNT(*)."""
        nombre_funcion_token = self._consumir(TT_IDENTIFICADOR) # Asume que el lexer lo marca como ID
        argumentos_nodos = []
        self._consumir(TT_PARENTESIS_IZQ)
        if self.token_actual and self.token_actual.tipo == TT_ASTERISCO: # Para COUNT(*)
            argumentos_nodos.append(NodoAsteriscoSQL(self._consumir(TT_ASTERISCO)))
        elif self.token_actual and self.token_actual.tipo != TT_PARENTESIS_DER:
            # Parsear lista de argumentos si los hubiera (más complejo, no implementado aquí)
            # Por ahora, asumimos funciones sin argumentos o con '*'
            self._error_sintactico("argumentos de función o ')'")
            pass 
        self._consumir(TT_PARENTESIS_DER)
        return NodoFuncionSQL(nombre_funcion_token, argumentos_nodos)

# Fin de la clase ParserTSQL