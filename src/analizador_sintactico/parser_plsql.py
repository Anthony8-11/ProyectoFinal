# src/analizador_sintactico/parser_plsql.py
import re 

# Importaciones de los tipos de token desde el lexer de PL/SQL.
try:
    from analizador_lexico.lexer_plsql import (
        TT_PALABRA_CLAVE_PLSQL, TT_IDENTIFICADOR_PLSQL, TT_IDENTIFICADOR_ENTRECOMILLADO_PLSQL,
        TT_LITERAL_CADENA_PLSQL, TT_LITERAL_NUMERICO_PLSQL, TT_LITERAL_FECHA_PLSQL,
        TT_LITERAL_BOOLEANO_PLSQL, TT_LITERAL_NULL_PLSQL,
        TT_OPERADOR_ASIGNACION_PLSQL, TT_OPERADOR_ARITMETICO_PLSQL,
        TT_OPERADOR_COMPARACION_PLSQL, TT_OPERADOR_CONCATENACION_PLSQL,
        TT_OPERADOR_LOGICO_PLSQL, TT_OPERADOR_MIEMBRO_PLSQL, TT_PUNTO_PLSQL,
        TT_PARENTESIS_IZQ_PLSQL, TT_PARENTESIS_DER_PLSQL, TT_COMA_PLSQL, 
        TT_PUNTO_Y_COMA_PLSQL, TT_DOS_PUNTOS_PLSQL, TT_PORCENTAJE_PLSQL,
        TT_ETIQUETA_PLSQL, TT_EOF_PLSQL, TT_ERROR_PLSQL,
        TT_WHITESPACE_PLSQL, TT_ASTERISCO,
        TT_OPERADOR_RANGO_PLSQL, # Asegurarse de que esté importado
        IDENTIFIER_LIKE_KEYWORDS_PLSQL 
    )
    from analizador_lexico.lexer_plsql import Token
except ImportError:
    print("ADVERTENCIA CRÍTICA (ParserPLSQL): No se pudieron importar los tipos de token de LexerPLSQL.")
    # Definir placeholders para que el archivo al menos cargue.
    TT_PALABRA_CLAVE_PLSQL, TT_IDENTIFICADOR_PLSQL, TT_EOF_PLSQL = "PALABRA_CLAVE_PLSQL", "IDENTIFICADOR_PLSQL", "EOF_PLSQL"
    TT_IDENTIFICADOR_ENTRECOMILLADO_PLSQL = "IDENTIFICADOR_ENTRECOMILLADO_PLSQL"
    TT_LITERAL_CADENA_PLSQL, TT_LITERAL_NUMERICO_PLSQL = "LITERAL_CADENA_PLSQL", "LITERAL_NUMERICO_PLSQL"
    TT_LITERAL_FECHA_PLSQL = "LITERAL_FECHA_PLSQL"
    TT_LITERAL_BOOLEANO_PLSQL, TT_LITERAL_NULL_PLSQL = "LITERAL_BOOLEANO_PLSQL", "LITERAL_NULL_PLSQL"
    TT_OPERADOR_ASIGNACION_PLSQL, TT_OPERADOR_ARITMETICO_PLSQL = "OPERADOR_ASIGNACION_PLSQL", "OPERADOR_ARITMETICO_PLSQL"
    TT_OPERADOR_COMPARACION_PLSQL, TT_OPERADOR_CONCATENACION_PLSQL = "OPERADOR_COMPARACION_PLSQL", "OPERADOR_CONCATENACION_PLSQL"
    TT_OPERADOR_LOGICO_PLSQL, TT_OPERADOR_MIEMBRO_PLSQL, TT_PUNTO_PLSQL = "OPERADOR_LOGICO_PLSQL", "OPERADOR_MIEMBRO_PLSQL", "PUNTO_PLSQL"
    TT_PARENTESIS_IZQ_PLSQL, TT_PARENTESIS_DER_PLSQL, TT_COMA_PLSQL = "PARENTESIS_IZQ_PLSQL", "PARENTESIS_DER_PLSQL", "COMA_PLSQL"
    TT_PUNTO_Y_COMA_PLSQL, TT_DOS_PUNTOS_PLSQL = "PUNTO_Y_COMA_PLSQL", "DOS_PUNTOS_PLSQL"
    TT_PORCENTAJE_PLSQL = "PORCENTAJE_PLSQL"
    TT_ETIQUETA_PLSQL = "ETIQUETA_PLSQL"
    TT_ERROR_PLSQL = "ERROR_PLSQL"
    TT_WHITESPACE_PLSQL = "WHITESPACE_PLSQL"
    TT_ASTERISCO = "ASTERISCO_PLSQL" 
    TT_OPERADOR_RANGO_PLSQL = "OPERADOR_RANGO_PLSQL" 
    IDENTIFIER_LIKE_KEYWORDS_PLSQL = {'sqlcode', 'sqlerrm', 'sysdate', 'user', 'uid', 'rownum'}
    class Token: pass

# --- Definiciones de Nodos del AST para PL/SQL ---
class NodoAST_PLSQL:
    def __repr__(self, indent=0):
        indent_str = "  " * indent
        attrs = {k: v for k, v in self.__dict__.items() if not k.startswith('_') and not isinstance(v, list) and not isinstance(v, NodoAST_PLSQL) and v is not None}
        attr_str_parts = []
        for k,v_item in attrs.items(): 
            if isinstance(v_item, Token): attr_str_parts.append(f"{k}='{v_item.lexema}'")
            elif isinstance(v_item, str): attr_str_parts.append(f"{k}='{v_item}'")
            else: attr_str_parts.append(f"{k}={v_item}")
        attr_str = ", ".join(attr_str_parts)
        children_repr_list = []
        for k, v_child in self.__dict__.items(): 
            if isinstance(v_child, NodoAST_PLSQL):
                children_repr_list.append(f"\n{v_child.__repr__(indent + 1)}")
            elif isinstance(v_child, list) and all(isinstance(item, (NodoAST_PLSQL, Token)) for item in v_child): 
                if v_child: 
                    list_items_repr = "\n".join([(item.__repr__(indent + 2) if isinstance(item, NodoAST_PLSQL) else f"{indent_str}  Token({item.tipo},'{item.lexema}')") for item in v_child])
                    children_repr_list.append(f"\n{indent_str}  {k}=[\n{list_items_repr}\n{indent_str}  ]")
                else: children_repr_list.append(f"\n{indent_str}  {k}=[]")
        children_repr = "".join(children_repr_list)
        base_repr = f"{indent_str}{self.__class__.__name__}"
        if attr_str: base_repr += f"({attr_str})"
        if children_repr: base_repr += f"({children_repr}\n{indent_str})" if not attr_str else f"({children_repr}\n{indent_str})"
        elif not attr_str : base_repr += "()"
        return base_repr
class NodoScriptPLSQL(NodoAST_PLSQL):
    def __init__(self, elementos): self.elementos = elementos
class NodoBloquePLSQL(NodoAST_PLSQL):
    def __init__(self, seccion_declaracion, seccion_ejecutable, seccion_excepcion=None):
        self.seccion_declaracion = seccion_declaracion 
        self.seccion_ejecutable = seccion_ejecutable   
        self.seccion_excepcion = seccion_excepcion     
class NodoDeclaracionVariablePLSQL(NodoAST_PLSQL):
    def __init__(self, nombre_variable_token, tipo_dato_nodo, valor_inicial_nodo=None):
        self.nombre_variable_token = nombre_variable_token
        self.tipo_dato_nodo = tipo_dato_nodo 
        self.valor_inicial_nodo = valor_inicial_nodo 
class NodoTipoDatoPLSQL(NodoAST_PLSQL):
    def __init__(self, tokens_tipo): 
        self.tokens_tipo = tokens_tipo
        self.nombre_tipo_str = "".join([t.lexema for t in tokens_tipo])
class NodoSentenciaPLSQL(NodoAST_PLSQL): pass
class NodoSentenciaAsignacionPLSQL(NodoSentenciaPLSQL):
    def __init__(self, variable_nodo, expresion_nodo):
        self.variable_nodo = variable_nodo 
        self.expresion_nodo = expresion_nodo 
class NodoLlamadaProcedimientoPLSQL(NodoSentenciaPLSQL):
    def __init__(self, callee_nodo, argumentos_nodos=None):
        self.callee_nodo = callee_nodo 
        self.argumentos_nodos = argumentos_nodos if argumentos_nodos is not None else []
class NodoSentenciaLoopPLSQL(NodoSentenciaPLSQL):
    def __init__(self, cuerpo_sentencias):
        self.cuerpo_sentencias = cuerpo_sentencias
class NodoSentenciaExitWhenPLSQL(NodoSentenciaPLSQL):
    def __init__(self, condicion_nodo):
        self.condicion_nodo = condicion_nodo
class NodoSentenciaIfPLSQL(NodoSentenciaPLSQL):
    def __init__(self, casos_if_elsif, cuerpo_else=None):
        self.casos_if_elsif = casos_if_elsif
        self.cuerpo_else = cuerpo_else 
class NodoSelect(NodoSentenciaPLSQL): 
    def __init__(self, columnas_select_nodos, tabla_from_token, where_condicion_nodo=None, into_clausula_nodos=None):
        self.columnas_select_nodos = columnas_select_nodos 
        self.tabla_from_token = tabla_from_token         
        self.where_condicion_nodo = where_condicion_nodo 
        self.into_clausula_nodos = into_clausula_nodos   
class NodoSeccionExcepcionPLSQL(NodoAST_PLSQL):
    def __init__(self, clausulas_when):
        self.clausulas_when = clausulas_when 
class NodoClausulaWhenPLSQL(NodoAST_PLSQL):
    def __init__(self, nombres_excepcion_tokens, cuerpo_sentencias_nodos):
        self.nombres_excepcion_tokens = nombres_excepcion_tokens
        self.cuerpo_sentencias_nodos = cuerpo_sentencias_nodos
class NodoSentenciaForLoopPLSQL(NodoSentenciaPLSQL):
    def __init__(self, variable_iteracion_token, es_reverse, expresion_inicio_nodo, expresion_fin_nodo, cuerpo_sentencias_nodos):
        self.variable_iteracion_token = variable_iteracion_token 
        self.es_reverse = es_reverse                         
        self.expresion_inicio_nodo = expresion_inicio_nodo     
        self.expresion_fin_nodo = expresion_fin_nodo         
        self.cuerpo_sentencias_nodos = cuerpo_sentencias_nodos 
class NodoExpresionSQL(NodoAST_PLSQL): pass
NodoExpresionPLSQL = NodoExpresionSQL 
class NodoIdentificadorPLSQL(NodoExpresionPLSQL):
    def __init__(self, id_token):
        self.id_token = id_token
        self.nombre = id_token.lexema 
class NodoLiteralPLSQL(NodoExpresionPLSQL):
    def __init__(self, literal_token):
        self.literal_token = literal_token
        self.valor = literal_token.valor 
class NodoExpresionBinariaPLSQL(NodoExpresionPLSQL):
    def __init__(self, operador_token, izquierda_nodo, derecha_nodo):
        self.operador_token = operador_token
        self.izquierda_nodo = izquierda_nodo
        self.derecha_nodo = derecha_nodo
        self.operador = operador_token.lexema
class NodoMiembroExpresionPLSQL(NodoExpresionPLSQL):
    def __init__(self, objeto_nodo, miembro_token):
        self.objeto_nodo = objeto_nodo 
        self.miembro_token = miembro_token 
        self.nombre_miembro = miembro_token.lexema
class NodoFuncionSQL(NodoExpresionPLSQL): 
    def __init__(self, nombre_funcion_token, argumentos_nodos=None):
        self.nombre_funcion_token = nombre_funcion_token 
        self.argumentos_nodos = argumentos_nodos if argumentos_nodos is not None else [] 
        self.nombre_funcion = nombre_funcion_token.lexema
class NodoAsteriscoSQL(NodoExpresionPLSQL): 
    def __init__(self, asterisco_token):
        self.asterisco_token = asterisco_token
class NodoExpresionUnariaPLSQL(NodoExpresionPLSQL): 
    def __init__(self, operador_token, operando_nodo):
        self.operador_token = operador_token
        self.operando_nodo = operando_nodo
        self.operador = operador_token.lexema
class NodoSentenciaRaisePLSQL(NodoSentenciaPLSQL):
    def __init__(self, exception_name_token=None):
        self.exception_name_token = exception_name_token
# --- Clase ParserPLSQL ---
class ParserPLSQL:
    def __init__(self, tokens):
        self.tokens = [token for token in tokens if token.tipo != TT_WHITESPACE_PLSQL]
        self.posicion_actual = 0
        self.token_actual = self.tokens[self.posicion_actual] if self.tokens else None
        self.errores_sintacticos = []

    def _avanzar(self):
        self.posicion_actual += 1
        if self.posicion_actual < len(self.tokens):
            self.token_actual = self.tokens[self.posicion_actual]
        else:
            self.token_actual = self.tokens[-1] if self.tokens and self.tokens[-1].tipo == TT_EOF_PLSQL else None

    def _error_sintactico(self, mensaje_esperado):
        mensaje = "Error Sintáctico Desconocido en PL/SQL"
        if self.token_actual and self.token_actual.tipo != TT_EOF_PLSQL:
            mensaje = (f"Error Sintáctico PL/SQL en L{self.token_actual.linea}:C{self.token_actual.columna}. "
                       f"Se esperaba {mensaje_esperado}, pero se encontró '{self.token_actual.lexema}' (tipo: {self.token_actual.tipo}).")
        elif self.token_actual and self.token_actual.tipo == TT_EOF_PLSQL:
            mensaje = (f"Error Sintáctico PL/SQL: Final inesperado del archivo (L{self.token_actual.linea}:C{self.token_actual.columna}). "
                       f"Se esperaba {mensaje_esperado}.")
        else: 
            last_token_info = self.tokens[self.posicion_actual -1] if self.posicion_actual > 0 and self.posicion_actual <= len(self.tokens) else \
                              (self.tokens[-1] if self.tokens else None) 
            linea_aprox = last_token_info.linea if last_token_info else 'desconocida'
            col_aprox = last_token_info.columna if last_token_info else 'desconocida'
            mensaje = (f"Error Sintáctico PL/SQL: Final inesperado de la entrada (cerca de L{linea_aprox}:C{col_aprox}). "
                       f"Se esperaba {mensaje_esperado}.")
        self.errores_sintacticos.append(mensaje)
        print(mensaje) 
        raise SyntaxError(mensaje) 

    def _consumir(self, tipo_token_esperado, lexema_esperado=None, es_sensible_mayusculas=False):
        token_a_consumir = self.token_actual
        if token_a_consumir and token_a_consumir.tipo == tipo_token_esperado:
            lexema_actual_para_comparar = token_a_consumir.lexema if es_sensible_mayusculas else token_a_consumir.lexema.lower()
            lexema_esperado_para_comparar = lexema_esperado.lower() if lexema_esperado and not es_sensible_mayusculas else lexema_esperado
            
            if lexema_esperado is None or lexema_actual_para_comparar == lexema_esperado_para_comparar:
                self._avanzar()
                return token_a_consumir
            else:
                self._error_sintactico(f"el lexema '{lexema_esperado}' para el token de tipo '{tipo_token_esperado}' (se encontró '{token_a_consumir.lexema}')")
        else:
            tipo_encontrado = token_a_consumir.tipo if token_a_consumir else "None (fin de entrada inesperado)"
            lexema_encontrado = token_a_consumir.lexema if token_a_consumir else ""
            if lexema_esperado:
                self._error_sintactico(f"el lexema '{lexema_esperado}' (tipo: {tipo_token_esperado}), pero se encontró '{lexema_encontrado}' (tipo: {tipo_encontrado})")
            else:
                self._error_sintactico(f"un token de tipo '{tipo_token_esperado}', pero se encontró '{lexema_encontrado}' (tipo: {tipo_encontrado})")
        return None 

    def parse(self):
        ast_script_nodo = None
        try:
            ast_script_nodo = self._parse_script_plsql()
            if not self.errores_sintacticos and self.token_actual and self.token_actual.tipo != TT_EOF_PLSQL:
                if self.token_actual.tipo == TT_OPERADOR_ARITMETICO_PLSQL and self.token_actual.lexema == '/':
                    self._consumir(TT_OPERADOR_ARITMETICO_PLSQL, '/') 
                if self.token_actual and self.token_actual.tipo != TT_EOF_PLSQL: 
                     self._error_sintactico("el final del script (EOF) o un separador de bloque '/'")
            
            if not self.errores_sintacticos and ast_script_nodo:
                 print("Análisis sintáctico de PL/SQL y construcción de AST completados exitosamente.")
            
        except SyntaxError:
            ast_script_nodo = None 
        except Exception as e:
            print(f"Error inesperado durante el parsing de PL/SQL: {e}")
            import traceback
            traceback.print_exc()
            ast_script_nodo = None
        
        if self.errores_sintacticos and not ast_script_nodo: 
             print(f"Resumen: Parsing de PL/SQL falló con {len(self.errores_sintacticos)} error(es) sintáctico(s) detectado(s).")
        
        return ast_script_nodo

    def _parse_script_plsql(self):
        elementos = []
        while self.token_actual and self.token_actual.tipo != TT_EOF_PLSQL:
            if self.token_actual.tipo == TT_PALABRA_CLAVE_PLSQL and \
               self.token_actual.lexema.lower() in ['declare', 'begin']:
                elementos.append(self._parse_bloque_anonimo_plsql())
            elif self.token_actual.tipo == TT_OPERADOR_ARITMETICO_PLSQL and self.token_actual.lexema == '/':
                self._consumir(TT_OPERADOR_ARITMETICO_PLSQL, '/')
            elif self.token_actual.tipo == TT_PALABRA_CLAVE_PLSQL and self.token_actual.lexema.lower() == 'select': 
                elementos.append(self._parse_select_simple_sql()) 
                if self.token_actual and self.token_actual.tipo == TT_PUNTO_Y_COMA_PLSQL:
                    self._consumir(TT_PUNTO_Y_COMA_PLSQL)
            else:
                if self.token_actual.tipo != TT_EOF_PLSQL:
                    self._error_sintactico("un bloque PL/SQL (DECLARE o BEGIN), una sentencia SELECT o un terminador '/'")
        return NodoScriptPLSQL(elementos)

    def _parse_bloque_anonimo_plsql(self):
        seccion_declaracion = []
        if self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE_PLSQL and \
           self.token_actual.lexema.lower() == 'declare':
            self._consumir(TT_PALABRA_CLAVE_PLSQL, 'declare')
            seccion_declaracion = self._parse_seccion_declaracion_plsql()
        self._consumir(TT_PALABRA_CLAVE_PLSQL, 'begin')
        seccion_ejecutable = self._parse_seccion_ejecutable_plsql()
        seccion_excepcion_nodo = None 
        if self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE_PLSQL and \
           self.token_actual.lexema.lower() == 'exception':
            seccion_excepcion_nodo = self._parse_seccion_excepcion_plsql() 
        self._consumir(TT_PALABRA_CLAVE_PLSQL, 'end')
        if self.token_actual and self.token_actual.tipo == TT_PUNTO_Y_COMA_PLSQL:
            self._consumir(TT_PUNTO_Y_COMA_PLSQL)
        return NodoBloquePLSQL(seccion_declaracion, seccion_ejecutable, seccion_excepcion_nodo)

    def _parse_seccion_excepcion_plsql(self):
        self._consumir(TT_PALABRA_CLAVE_PLSQL, 'exception')
        clausulas_when = []
        while self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE_PLSQL and \
              self.token_actual.lexema.lower() == 'when':
            clausulas_when.append(self._parse_clausula_when_plsql())
        if not clausulas_when: 
            self._error_sintactico("al menos una cláusula WHEN después de EXCEPTION")
        return NodoSeccionExcepcionPLSQL(clausulas_when)

    def _parse_clausula_when_plsql(self):
        self._consumir(TT_PALABRA_CLAVE_PLSQL, 'when')
        nombres_excepcion_tokens = []
        if self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE_PLSQL and \
           self.token_actual.lexema.lower() == 'others':
            nombres_excepcion_tokens.append(self._consumir(TT_PALABRA_CLAVE_PLSQL, 'others'))
        else:
            nombres_excepcion_tokens.append(self._consumir(TT_IDENTIFICADOR_PLSQL)) 
            while self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE_PLSQL and \
                  self.token_actual.lexema.lower() == 'or':
                self._consumir(TT_PALABRA_CLAVE_PLSQL, 'or')
                nombres_excepcion_tokens.append(self._consumir(TT_IDENTIFICADOR_PLSQL))
        self._consumir(TT_PALABRA_CLAVE_PLSQL, 'then')
        cuerpo_sentencias_nodos = self._parse_lista_sentencias_hasta_palabras_clave(['when', 'end'])
        return NodoClausulaWhenPLSQL(nombres_excepcion_tokens, cuerpo_sentencias_nodos)

    def _parse_seccion_declaracion_plsql(self):
        declaraciones = []
        while self.token_actual and not (
              self.token_actual.tipo == TT_PALABRA_CLAVE_PLSQL and \
              self.token_actual.lexema.lower() in ['begin', 'exception', 'end']
              ):
            if self.token_actual.tipo == TT_IDENTIFICADOR_PLSQL: 
                declaraciones.append(self._parse_declaracion_variable_plsql_item())
            elif self.token_actual.tipo == TT_PUNTO_Y_COMA_PLSQL: 
                self._consumir(TT_PUNTO_Y_COMA_PLSQL)
            else:
                self._error_sintactico("una declaración de variable, tipo, cursor, etc., o la palabra clave BEGIN")
        return declaraciones

    def _parse_declaracion_variable_plsql_item(self):
        nombre_var_token = self._consumir(TT_IDENTIFICADOR_PLSQL)
        tokens_tipo = []
        if self.token_actual and (self.token_actual.tipo == TT_IDENTIFICADOR_PLSQL or \
                                   self.token_actual.tipo == TT_PALABRA_CLAVE_PLSQL): 
            tokens_tipo.append(self._consumir(self.token_actual.tipo)) 
        else:
            self._error_sintactico("un tipo de dato (identificador o palabra clave como VARCHAR2, NUMBER)")
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR_MIEMBRO_PLSQL: 
            tokens_tipo.append(self._consumir(TT_OPERADOR_MIEMBRO_PLSQL))
            tokens_tipo.append(self._consumir(TT_IDENTIFICADOR_PLSQL))
        if self.token_actual and self.token_actual.tipo == TT_PARENTESIS_IZQ_PLSQL:
            tokens_tipo.append(self._consumir(TT_PARENTESIS_IZQ_PLSQL))
            tokens_tipo.append(self._consumir(TT_LITERAL_NUMERICO_PLSQL)) 
            if self.token_actual and self.token_actual.tipo == TT_COMA_PLSQL: 
                 tokens_tipo.append(self._consumir(TT_COMA_PLSQL))
                 tokens_tipo.append(self._consumir(TT_LITERAL_NUMERICO_PLSQL))
            tokens_tipo.append(self._consumir(TT_PARENTESIS_DER_PLSQL))
        if self.token_actual and self.token_actual.tipo == TT_PORCENTAJE_PLSQL:
            tokens_tipo.append(self._consumir(TT_PORCENTAJE_PLSQL))
            if self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE_PLSQL and \
               self.token_actual.lexema.lower() in ['type', 'rowtype']:
                tokens_tipo.append(self._consumir(TT_PALABRA_CLAVE_PLSQL))
            else:
                self._error_sintactico("TYPE o ROWTYPE después de '%'")
        tipo_dato_nodo = NodoTipoDatoPLSQL(tokens_tipo)
        valor_inicial_nodo = None
        if self.token_actual and self.token_actual.tipo == TT_OPERADOR_ASIGNACION_PLSQL: 
            self._consumir(TT_OPERADOR_ASIGNACION_PLSQL)
            valor_inicial_nodo = self._parse_expresion_plsql() 
        elif self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE_PLSQL and self.token_actual.lexema.lower() == 'default':
            self._consumir(TT_PALABRA_CLAVE_PLSQL, 'default')
            valor_inicial_nodo = self._parse_expresion_plsql()
        self._consumir(TT_PUNTO_Y_COMA_PLSQL)
        return NodoDeclaracionVariablePLSQL(nombre_var_token, tipo_dato_nodo, valor_inicial_nodo)

    def _parse_seccion_ejecutable_plsql(self):
        sentencias = []
        while self.token_actual and not (
              self.token_actual.tipo == TT_PALABRA_CLAVE_PLSQL and \
              self.token_actual.lexema.lower() in ['exception', 'end']
              ):
            nodo_sentencia = self._parse_sentencia_plsql_simple() 
            if nodo_sentencia:
                sentencias.append(nodo_sentencia)
            elif not self.errores_sintacticos and \
                 self.token_actual and self.token_actual.tipo not in [TT_PALABRA_CLAVE_PLSQL, TT_EOF_PLSQL]:
                 self._error_sintactico("una sentencia PL/SQL válida o las palabras clave EXCEPTION o END")
        return sentencias

    def _parse_sentencia_plsql_simple(self):
        if self.token_actual is None: return None
        if self.token_actual.tipo == TT_IDENTIFICADOR_PLSQL:
            siguiente_token_pos = self.posicion_actual + 1
            if siguiente_token_pos < len(self.tokens):
                siguiente_token = self.tokens[siguiente_token_pos]
                if siguiente_token.tipo == TT_OPERADOR_ASIGNACION_PLSQL: 
                    return self._parse_sentencia_asignacion_plsql()
                return self._parse_llamada_procedimiento_plsql()
            else: 
                self._error_sintactico("una sentencia PL/SQL completa")
        elif self.token_actual.tipo == TT_PALABRA_CLAVE_PLSQL:
            lexema = self.token_actual.lexema.lower()
            if lexema == 'loop': return self._parse_sentencia_loop_plsql()
            if lexema == 'exit': return self._parse_sentencia_exit_when_plsql()
            if lexema == 'if': return self._parse_sentencia_if_plsql()
            if lexema == 'for': return self._parse_sentencia_for_loop_plsql()
            if lexema == 'begin': return self._parse_bloque_anonimo_plsql()  # <-- Permitir BEGIN anidado
            if lexema == 'raise': return self._parse_sentencia_raise_plsql()
            else:
                self._error_sintactico(f"una sentencia PL/SQL válida. Palabra clave '{lexema}' no esperada aquí.")
        elif self.token_actual.tipo == TT_PUNTO_Y_COMA_PLSQL: 
            self._consumir(TT_PUNTO_Y_COMA_PLSQL)
            return None
        else:
            self._error_sintactico("una sentencia PL/SQL válida")
        return None 

    def _parse_sentencia_asignacion_plsql(self):
        variable_nodo = self._parse_expresion_primaria_plsql() 
        self._consumir(TT_OPERADOR_ASIGNACION_PLSQL)
        expresion_nodo = self._parse_expresion_plsql()
        self._consumir(TT_PUNTO_Y_COMA_PLSQL)
        return NodoSentenciaAsignacionPLSQL(variable_nodo, expresion_nodo)

    def _parse_llamada_procedimiento_plsql(self):
        callee_nodo = self._parse_expresion_primaria_plsql() 
        argumentos_nodos = []
        if self.token_actual and self.token_actual.tipo == TT_PARENTESIS_IZQ_PLSQL:
            self._consumir(TT_PARENTESIS_IZQ_PLSQL)
            if self.token_actual.tipo != TT_PARENTESIS_DER_PLSQL:
                while True:
                    argumentos_nodos.append(self._parse_expresion_plsql())
                    if self.token_actual.tipo == TT_COMA_PLSQL:
                        self._consumir(TT_COMA_PLSQL)
                    else:
                        break
            self._consumir(TT_PARENTESIS_DER_PLSQL)
        self._consumir(TT_PUNTO_Y_COMA_PLSQL)
        return NodoLlamadaProcedimientoPLSQL(callee_nodo, argumentos_nodos)
        
    def _parse_sentencia_loop_plsql(self):
        self._consumir(TT_PALABRA_CLAVE_PLSQL, 'loop')
        cuerpo_sentencias = self._parse_lista_sentencias_hasta_end_loop()
        self._consumir(TT_PALABRA_CLAVE_PLSQL, 'end')
        self._consumir(TT_PALABRA_CLAVE_PLSQL, 'loop')
        self._consumir(TT_PUNTO_Y_COMA_PLSQL)
        return NodoSentenciaLoopPLSQL(cuerpo_sentencias)

    def _parse_lista_sentencias_hasta_end_loop(self):
        sentencias = []
        while not (self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE_PLSQL and \
                   self.token_actual.lexema.lower() == 'end'):
            if self.token_actual.tipo == TT_EOF_PLSQL:
                self._error_sintactico("END LOOP para cerrar el bucle LOOP")
            nodo_sent = self._parse_sentencia_plsql_simple()
            if nodo_sent:
                sentencias.append(nodo_sent)
            elif not self.errores_sintacticos: 
                 if self.token_actual and self.token_actual.tipo == TT_PUNTO_Y_COMA_PLSQL:
                     self._consumir(TT_PUNTO_Y_COMA_PLSQL)
                 else: 
                     self._error_sintactico("una sentencia válida o END LOOP")
        return sentencias

    def _parse_sentencia_exit_when_plsql(self):
        self._consumir(TT_PALABRA_CLAVE_PLSQL, 'exit')
        self._consumir(TT_PALABRA_CLAVE_PLSQL, 'when')
        condicion_nodo = self._parse_expresion_plsql()
        self._consumir(TT_PUNTO_Y_COMA_PLSQL)
        return NodoSentenciaExitWhenPLSQL(condicion_nodo)

    def _parse_sentencia_if_plsql(self):
        self._consumir(TT_PALABRA_CLAVE_PLSQL, 'if')
        condicion_if = self._parse_expresion_plsql()
        self._consumir(TT_PALABRA_CLAVE_PLSQL, 'then')
        cuerpo_if = self._parse_lista_sentencias_hasta_palabras_clave(['elsif', 'else', 'end'])
        
        casos_if_elsif = [(condicion_if, cuerpo_if)]
        cuerpo_else = None

        while self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE_PLSQL and \
              self.token_actual.lexema.lower() == 'elsif':
            self._consumir(TT_PALABRA_CLAVE_PLSQL, 'elsif')
            condicion_elsif = self._parse_expresion_plsql()
            self._consumir(TT_PALABRA_CLAVE_PLSQL, 'then')
            cuerpo_elsif = self._parse_lista_sentencias_hasta_palabras_clave(['elsif', 'else', 'end'])
            casos_if_elsif.append((condicion_elsif, cuerpo_elsif))

        if self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE_PLSQL and \
           self.token_actual.lexema.lower() == 'else':
            self._consumir(TT_PALABRA_CLAVE_PLSQL, 'else')
            cuerpo_else = self._parse_lista_sentencias_hasta_palabras_clave(['end'])
            
        self._consumir(TT_PALABRA_CLAVE_PLSQL, 'end')
        self._consumir(TT_PALABRA_CLAVE_PLSQL, 'if')
        self._consumir(TT_PUNTO_Y_COMA_PLSQL)
        return NodoSentenciaIfPLSQL(casos_if_elsif, cuerpo_else)

    def _parse_sentencia_for_loop_plsql(self):
        self._consumir(TT_PALABRA_CLAVE_PLSQL, 'for')
        variable_iteracion_token = self._consumir(TT_IDENTIFICADOR_PLSQL)
        self._consumir(TT_PALABRA_CLAVE_PLSQL, 'in')
        es_reverse = False
        if self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE_PLSQL and \
           self.token_actual.lexema.lower() == 'reverse':
            self._consumir(TT_PALABRA_CLAVE_PLSQL, 'reverse')
            es_reverse = True
        expresion_inicio_nodo = self._parse_expresion_plsql()
        self._consumir(TT_OPERADOR_RANGO_PLSQL, '..') # <-- USO CORRECTO DE TT_OPERADOR_RANGO_PLSQL
        expresion_fin_nodo = self._parse_expresion_plsql()
        self._consumir(TT_PALABRA_CLAVE_PLSQL, 'loop')
        cuerpo_sentencias_nodos = self._parse_lista_sentencias_hasta_end_loop() 
        self._consumir(TT_PALABRA_CLAVE_PLSQL, 'end')
        self._consumir(TT_PALABRA_CLAVE_PLSQL, 'loop')
        self._consumir(TT_PUNTO_Y_COMA_PLSQL)
        return NodoSentenciaForLoopPLSQL(
            variable_iteracion_token, 
            es_reverse, 
            expresion_inicio_nodo, 
            expresion_fin_nodo, 
            cuerpo_sentencias_nodos
        )

    def _parse_lista_sentencias_hasta_palabras_clave(self, palabras_clave_fin):
        sentencias = []
        while not (self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE_PLSQL and \
                   self.token_actual.lexema.lower() in palabras_clave_fin):
            if self.token_actual.tipo == TT_EOF_PLSQL:
                self._error_sintactico(f"una de las palabras clave: {', '.join(palabras_clave_fin)}")
            
            nodo_sent = self._parse_sentencia_plsql_simple()
            if nodo_sent:
                sentencias.append(nodo_sent)
            elif not self.errores_sintacticos:
                 if self.token_actual and self.token_actual.tipo == TT_PUNTO_Y_COMA_PLSQL:
                     self._consumir(TT_PUNTO_Y_COMA_PLSQL)
                 else:
                     self._error_sintactico(f"una sentencia válida o una de las palabras clave: {', '.join(palabras_clave_fin)}")
        return sentencias

    def _parse_select_simple_sql(self):
        self._consumir(TT_PALABRA_CLAVE_PLSQL, 'select')
        columnas_select_nodos = self._parse_lista_de_seleccion_plsql()
        
        tabla_from_token = None
        if self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE_PLSQL and self.token_actual.lexema.lower() == 'from':
            self._consumir(TT_PALABRA_CLAVE_PLSQL, 'from')
            tabla_from_token = self._consumir(TT_IDENTIFICADOR_PLSQL) 
        
        if self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE_PLSQL and self.token_actual.lexema.lower() == 'where':
            self._consumir_hasta_fin_sentencia_o_go() 
            
        return NodoSelect(columnas_select_nodos, tabla_from_token, None) 

    def _parse_lista_de_seleccion_plsql(self):
        elementos = []
        # print(f"[DEBUG PARSER PLSQL] _parse_lista_de_seleccion_plsql. Token actual: {self.token_actual}, Constante TT_ASTERISCO: {TT_ASTERISCO}") 
        if self.token_actual and self.token_actual.tipo == TT_ASTERISCO: 
            # print(f"[DEBUG PARSER PLSQL] _parse_lista_de_seleccion_plsql: '*' encontrado con tipo '{self.token_actual.tipo}'.")
            elementos.append(NodoAsteriscoSQL(self._consumir(TT_ASTERISCO)))
        else:
            # print(f"[DEBUG PARSER PLSQL] _parse_lista_de_seleccion_plsql: '*' NO encontrado o tipo incorrecto. Token: {self.token_actual}. Intentando como expresión.")
            elementos.append(self._parse_expresion_plsql()) 
            while self.token_actual and self.token_actual.tipo == TT_COMA_PLSQL:
                self._consumir(TT_COMA_PLSQL)
                elementos.append(self._parse_expresion_plsql())
        return elementos

    def _parse_expresion_plsql(self):
        return self._parse_expresion_logica_or_plsql()

    def _parse_expresion_logica_or_plsql(self):
        nodo = self._parse_expresion_logica_and_plsql()
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR_LOGICO_PLSQL and \
              self.token_actual.lexema.lower() == 'or':
            op_token = self._consumir(TT_OPERADOR_LOGICO_PLSQL)
            nodo_der = self._parse_expresion_logica_and_plsql()
            nodo = NodoExpresionBinariaPLSQL(op_token, nodo, nodo_der)
        return nodo

    def _parse_expresion_logica_and_plsql(self):
        nodo = self._parse_expresion_unaria_logica_plsql() 
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR_LOGICO_PLSQL and \
              self.token_actual.lexema.lower() == 'and':
            op_token = self._consumir(TT_OPERADOR_LOGICO_PLSQL)
            nodo_der = self._parse_expresion_unaria_logica_plsql()
            nodo = NodoExpresionBinariaPLSQL(op_token, nodo, nodo_der)
        return nodo

    def _parse_expresion_unaria_logica_plsql(self): 
        if self.token_actual and self.token_actual.tipo == TT_OPERADOR_LOGICO_PLSQL and \
           self.token_actual.lexema.lower() == 'not':
            op_token = self._consumir(TT_OPERADOR_LOGICO_PLSQL)
            operando_nodo = self._parse_expresion_unaria_logica_plsql() 
            return NodoExpresionUnariaPLSQL(op_token, operando_nodo)
        return self._parse_expresion_comparativa_plsql()

    def _parse_expresion_comparativa_plsql(self):
        nodo_izq = self._parse_expresion_concatenacion_plsql()
        if self.token_actual and self.token_actual.tipo == TT_OPERADOR_COMPARACION_PLSQL:
            if self.token_actual.lexema.lower() == 'is':
                op_is_token = self._consumir(TT_OPERADOR_COMPARACION_PLSQL)
                op_not_null_token = None
                if self.token_actual and self.token_actual.tipo == TT_OPERADOR_LOGICO_PLSQL and \
                   self.token_actual.lexema.lower() == 'not':
                    op_not_null_token = self._consumir(TT_OPERADOR_LOGICO_PLSQL)
                self._consumir(TT_PALABRA_CLAVE_PLSQL, 'null')
                lexema_op_is = op_is_token.lexema + (" " + op_not_null_token.lexema if op_not_null_token else "") + " NULL"
                token_is_null_completo = Token(TT_OPERADOR_COMPARACION_PLSQL, lexema_op_is, op_is_token.linea, op_is_token.columna)
                return NodoExpresionBinariaPLSQL(token_is_null_completo, nodo_izq, NodoLiteralPLSQL(Token(TT_LITERAL_NULL_PLSQL, "NULL",0,0, None)))
            while self.token_actual and self.token_actual.tipo == TT_OPERADOR_COMPARACION_PLSQL:
                op_token = self._consumir(TT_OPERADOR_COMPARACION_PLSQL)
                nodo_der = self._parse_expresion_concatenacion_plsql()
                nodo_izq = NodoExpresionBinariaPLSQL(op_token, nodo_izq, nodo_der)
        return nodo_izq

    def _parse_expresion_concatenacion_plsql(self):
        nodo = self._parse_expresion_aditiva_plsql()
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR_CONCATENACION_PLSQL:
            op_token = self._consumir(TT_OPERADOR_CONCATENACION_PLSQL)
            nodo_der = self._parse_expresion_aditiva_plsql()
            nodo = NodoExpresionBinariaPLSQL(op_token, nodo, nodo_der)
        return nodo

    def _parse_expresion_aditiva_plsql(self):
        nodo = self._parse_expresion_multiplicativa_plsql()
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR_ARITMETICO_PLSQL and \
              self.token_actual.lexema in ['+', '-']:
            op_token = self._consumir(TT_OPERADOR_ARITMETICO_PLSQL)
            nodo_der = self._parse_expresion_multiplicativa_plsql()
            nodo = NodoExpresionBinariaPLSQL(op_token, nodo, nodo_der)
        return nodo

    def _parse_expresion_multiplicativa_plsql(self):
        nodo = self._parse_expresion_exponencial_plsql() 
        while self.token_actual and \
              ( (self.token_actual.tipo == TT_OPERADOR_ARITMETICO_PLSQL and self.token_actual.lexema in ['/', '%']) or \
                (self.token_actual.tipo == TT_ASTERISCO and self.token_actual.lexema == '*') ): 
            op_token = self._consumir(self.token_actual.tipo) 
            nodo_der = self._parse_expresion_exponencial_plsql()
            nodo = NodoExpresionBinariaPLSQL(op_token, nodo, nodo_der)
        return nodo

    def _parse_expresion_exponencial_plsql(self):
        nodo = self._parse_expresion_unaria_plsql()
        if self.token_actual and self.token_actual.tipo == TT_OPERADOR_ARITMETICO_PLSQL and \
           self.token_actual.lexema == '**':
            op_token = self._consumir(TT_OPERADOR_ARITMETICO_PLSQL)
            nodo_der = self._parse_expresion_exponencial_plsql() 
            nodo = NodoExpresionBinariaPLSQL(op_token, nodo, nodo_der)
        return nodo

    def _parse_expresion_unaria_plsql(self):
        # Maneja operadores unarios + y -
        if self.token_actual and self.token_actual.tipo == TT_OPERADOR_ARITMETICO_PLSQL and \
           self.token_actual.lexema in ['+', '-']:
            op_token = self._consumir(TT_OPERADOR_ARITMETICO_PLSQL)
            operando_nodo = self._parse_expresion_unaria_plsql()
            return NodoExpresionUnariaPLSQL(op_token, operando_nodo)
        return self._parse_expresion_primaria_plsql()

    def _parse_expresion_primaria_plsql(self):
        token = self.token_actual
        if token is None:
            self._error_sintactico("una expresión primaria (identificador, literal, etc.)")

        if token.tipo in [TT_LITERAL_CADENA_PLSQL, TT_LITERAL_NUMERICO_PLSQL, TT_LITERAL_BOOLEANO_PLSQL, TT_LITERAL_NULL_PLSQL, TT_LITERAL_FECHA_PLSQL]:
            return NodoLiteralPLSQL(self._consumir(token.tipo))
        elif token.tipo == TT_PALABRA_CLAVE_PLSQL and token.lexema.lower() in IDENTIFIER_LIKE_KEYWORDS_PLSQL:
            return NodoIdentificadorPLSQL(self._consumir(TT_PALABRA_CLAVE_PLSQL))
        elif token.tipo == TT_IDENTIFICADOR_PLSQL:
            identificador_token = self._consumir(TT_IDENTIFICADOR_PLSQL)
            if self.token_actual and self.token_actual.tipo == TT_PARENTESIS_IZQ_PLSQL:
                self._avanzar() 
                argumentos_nodos = []
                if self.token_actual.tipo != TT_PARENTESIS_DER_PLSQL:
                    while True:
                        argumentos_nodos.append(self._parse_expresion_plsql())
                        if self.token_actual.tipo == TT_COMA_PLSQL:
                            self._consumir(TT_COMA_PLSQL)
                        else:
                            break
                self._consumir(TT_PARENTESIS_DER_PLSQL)
                return NodoFuncionSQL(identificador_token, argumentos_nodos)
            elif self.token_actual and self.token_actual.tipo == TT_OPERADOR_MIEMBRO_PLSQL: 
                objeto_nodo = NodoIdentificadorPLSQL(identificador_token)
                while self.token_actual and self.token_actual.tipo == TT_OPERADOR_MIEMBRO_PLSQL:
                    self._consumir(TT_OPERADOR_MIEMBRO_PLSQL) 
                    miembro_token = self._consumir(TT_IDENTIFICADOR_PLSQL)
                    objeto_nodo = NodoMiembroExpresionPLSQL(objeto_nodo, miembro_token)
                return objeto_nodo
            else:
                return NodoIdentificadorPLSQL(identificador_token)
        elif token.tipo == TT_PARENTESIS_IZQ_PLSQL:
            self._consumir(TT_PARENTESIS_IZQ_PLSQL)
            nodo_expr_interna = self._parse_expresion_plsql() 
            self._consumir(TT_PARENTESIS_DER_PLSQL)
            return nodo_expr_interna
        else:
            self._error_sintactico(f"una expresión primaria válida. Se encontró '{token.lexema}' (tipo: {token.tipo})")
        return None

    def _consumir_hasta_palabra_clave(self, palabra_clave_buscada):
        while self.token_actual and not (self.token_actual.tipo == TT_PALABRA_CLAVE_PLSQL and \
                                         self.token_actual.lexema.lower() == palabra_clave_buscada.lower()):
            if self.token_actual.tipo == TT_EOF_PLSQL:
                self._error_sintactico(f"la palabra clave '{palabra_clave_buscada}'")
            self._avanzar()
        if not self.token_actual: 
            self._error_sintactico(f"la palabra clave '{palabra_clave_buscada}'")

    def _consumir_hasta_fin_sentencia_o_go(self):
        while self.token_actual and \
              self.token_actual.tipo != TT_PUNTO_Y_COMA_PLSQL and \
              not (self.token_actual.tipo == TT_PALABRA_CLAVE_PLSQL and self.token_actual.lexema.lower() == 'go') and \
              self.token_actual.tipo != TT_EOF_PLSQL: 
            self._avanzar()
        if self.token_actual and self.token_actual.tipo == TT_PUNTO_Y_COMA_PLSQL: 
            self._avanzar() 
    
    def _parse_sentencia_raise_plsql(self):
        self._consumir(TT_PALABRA_CLAVE_PLSQL, 'raise')
        exception_name_token = None
        if self.token_actual and self.token_actual.tipo == TT_IDENTIFICADOR_PLSQL:
            exception_name_token = self._consumir(TT_IDENTIFICADOR_PLSQL)
        self._consumir(TT_PUNTO_Y_COMA_PLSQL)
        return NodoSentenciaRaisePLSQL(exception_name_token)

# Fin de la clase ParserPLSQL
