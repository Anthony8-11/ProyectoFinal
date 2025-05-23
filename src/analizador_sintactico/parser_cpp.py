# src/analizador_sintactico/parser_cpp.py

# Importaciones necesarias
try:
    from analizador_lexico.lexer_cpp import (
        TT_PALABRA_CLAVE, TT_IDENTIFICADOR, TT_LITERAL_ENTERO, TT_LITERAL_FLOTANTE,
        TT_LITERAL_CADENA, TT_LITERAL_CARACTER, TT_DIRECTIVA_PREPROCESADOR,
        TT_OPERADOR_ASIGNACION, TT_OPERADOR_ARITMETICO, TT_OPERADOR_COMPARACION,
        TT_OPERADOR_LOGICO, TT_OPERADOR_MIEMBRO, TT_PUNTO_Y_COMA, TT_COMA, TT_PUNTO,
        TT_PARENTESIS_IZQ, TT_PARENTESIS_DER, TT_LLAVE_IZQ, TT_LLAVE_DER,
        TT_CORCHETE_IZQ, TT_CORCHETE_DER, TT_EOF_CPP, TT_OPERADOR_BITWISE, TT_DOS_PUNTOS,
        TT_ASTERISCO 
    )
    from analizador_lexico.lexer_cpp import Token 
except ImportError:
    print("ADVERTENCIA CRÍTICA (ParserCPP): No se pudieron importar los tipos de token de LexerCPP.")
    # Definir placeholders
    TT_PALABRA_CLAVE, TT_IDENTIFICADOR, TT_EOF_CPP = "PALABRA_CLAVE_CPP", "IDENTIFICADOR_CPP", "EOF_CPP"
    TT_DIRECTIVA_PREPROCESADOR = "DIRECTIVA_PREPROCESADOR_CPP"; TT_LITERAL_ENTERO="LITERAL_ENTERO_CPP"
    TT_LLAVE_IZQ, TT_LLAVE_DER = "LLAVE_IZQ_CPP", "LLAVE_DER_CPP"; TT_LITERAL_CADENA="LITERAL_CADENA_CPP"
    TT_PUNTO_Y_COMA = "PUNTO_Y_COMA_CPP"; TT_OPERADOR_MIEMBRO = "OPERADOR_MIEMBRO_CPP" 
    TT_PARENTESIS_IZQ, TT_PARENTESIS_DER = "PARENTESIS_IZQ_CPP", "PARENTESIS_DER_CPP"
    TT_OPERADOR_ARITMETICO = "OPERADOR_ARITMETICO_CPP"; TT_OPERADOR_BITWISE = "OPERADOR_BITWISE_CPP" 
    TT_OPERADOR_ASIGNACION = "OPERADOR_ASIGNACION_CPP"; TT_OPERADOR_LOGICO = "OPERADOR_LOGICO_CPP"
    TT_OPERADOR_COMPARACION = "OPERADOR_COMPARACION_CPP"; TT_COMA = "COMA_CPP"
    TT_CORCHETE_IZQ, TT_CORCHETE_DER = "CORCHETE_IZQ_CPP", "CORCHETE_DER_CPP"
    TT_DOS_PUNTOS = "DOS_PUNTOS_CPP"
    TT_ASTERISCO = "ASTERISCO_CPP" 
    TT_PUNTO = "PUNTO_CPP" 
    class Token: pass
    pass

# --- Definiciones de Nodos del AST para C++ ---
class NodoAST_CPP:
    """Clase base para todos los nodos del AST de C++."""
    def __repr__(self, indent=0):
        indent_str = "  " * indent
        attrs = {k: v for k, v in self.__dict__.items() if not k.startswith('_') and not isinstance(v, list) and not isinstance(v, NodoAST_CPP) and v is not None}
        attr_str_parts = []
        for k,v_item in attrs.items(): 
            if isinstance(v_item, Token): attr_str_parts.append(f"{k}='{v_item.lexema}'")
            elif isinstance(v_item, str): attr_str_parts.append(f"{k}='{v_item}'")
            else: attr_str_parts.append(f"{k}={v_item}")
        attr_str = ", ".join(attr_str_parts)
        
        children_repr_list = []
        for k, v_child in self.__dict__.items(): 
            if isinstance(v_child, NodoAST_CPP):
                children_repr_list.append(f"\n{v_child.__repr__(indent + 1)}")
            elif isinstance(v_child, list) and all(isinstance(item, (NodoAST_CPP, Token)) for item in v_child): 
                if v_child: 
                    list_items_repr = "\n".join([(item.__repr__(indent + 2) if isinstance(item, NodoAST_CPP) else f"{indent_str}  Token({item.tipo},'{item.lexema}')") for item in v_child])
                    children_repr_list.append(f"\n{indent_str}  {k}=[\n{list_items_repr}\n{indent_str}  ]")
                else:
                    children_repr_list.append(f"\n{indent_str}  {k}=[]")
        children_repr = "".join(children_repr_list)
        base_repr = f"{indent_str}{self.__class__.__name__}"
        if attr_str: base_repr += f"({attr_str})"
        if children_repr:
            base_repr += f"({children_repr}\n{indent_str})" if not attr_str else f"({children_repr}\n{indent_str})"
        elif not attr_str : base_repr += "()"
        return base_repr

class NodoTraduccionUnidad(NodoAST_CPP):
    def __init__(self, declaraciones_globales): self.declaraciones_globales = declaraciones_globales
class NodoDeclaracion(NodoAST_CPP): pass
class NodoSentencia(NodoAST_CPP): pass
class NodoExpresion(NodoAST_CPP): pass
class NodoDirectivaPreprocesador(NodoDeclaracion):
    def __init__(self, token_directiva):
        self.token_directiva = token_directiva; self.directiva = ''; self.argumentos = ''; self.archivo_cabecera = None; self.tipo_cabecera = None
        if isinstance(token_directiva.valor, dict):
            self.directiva = token_directiva.valor.get('directiva', ''); self.argumentos = token_directiva.valor.get('argumentos', '')
            if 'archivo' in token_directiva.valor: self.archivo_cabecera = token_directiva.valor['archivo']; self.tipo_cabecera = token_directiva.valor.get('tipo_cabecera')
class NodoUsingNamespace(NodoDeclaracion):
    def __init__(self, tokens_qname_namespace): self.tokens_qname_namespace = tokens_qname_namespace; self.nombre_namespace_str = "".join([t.lexema for t in tokens_qname_namespace])
class NodoNamespaceDefinicion(NodoDeclaracion):
    def __init__(self, nombre_namespace_token, declaraciones_internas):
        self.nombre_namespace_token = nombre_namespace_token; self.declaraciones_internas = declaraciones_internas; self.nombre = nombre_namespace_token.lexema if nombre_namespace_token else None 
class NodoDefinicionClase(NodoDeclaracion):
    def __init__(self, token_clase_o_struct, nombre_clase_token, miembros_nodos):
        self.token_clase_o_struct = token_clase_o_struct; self.nombre_clase_token = nombre_clase_token; self.miembros_nodos = miembros_nodos; self.nombre = nombre_clase_token.lexema if nombre_clase_token else "ClaseAnónima"
class NodoDefinicionFuncion(NodoDeclaracion): # También usado para métodos de clase
    def __init__(self, tipo_retorno_nodo, nombre_funcion_qname_tokens, parametros_nodos, cuerpo_nodo_bloque, es_const=False, es_extern_c=False, es_metodo_clase=False):
        self.tipo_retorno_nodo = tipo_retorno_nodo; self.nombre_funcion_qname_tokens = nombre_funcion_qname_tokens; self.parametros_nodos = parametros_nodos; self.cuerpo_nodo_bloque = cuerpo_nodo_bloque; self.nombre = "".join([t.lexema for t in nombre_funcion_qname_tokens]); self.es_const = es_const; self.es_extern_c = es_extern_c; self.es_metodo_clase = es_metodo_clase
class NodoParametroFuncion(NodoAST_CPP):
    def __init__(self, tipo_param_nodo, nombre_param_token=None, valor_defecto_nodo=None):
        self.tipo_param_nodo = tipo_param_nodo; self.nombre_param_token = nombre_param_token; self.valor_defecto_nodo = valor_defecto_nodo 
class NodoTipoCPP(NodoAST_CPP):
    def __init__(self, tokens_tipo, es_puntero=0, es_referencia=False, es_const_qualifier=False, es_volatile_qualifier=False): 
        self.tokens_tipo = tokens_tipo; self.es_puntero = es_puntero; self.es_referencia = es_referencia; self.es_const_qualifier = es_const_qualifier; self.es_volatile_qualifier = es_volatile_qualifier
        nombre_base = "".join([t.lexema for t in tokens_tipo]); 
        self.nombre_tipo_str = ("const " if es_const_qualifier and not any(t.lexema=='const' for t in tokens_tipo) else "") + ("volatile " if es_volatile_qualifier and not any(t.lexema=='volatile' for t in tokens_tipo) else "") + nombre_base + "*"*es_puntero + ("&" if es_referencia else "")
class NodoBloqueSentenciasCPP(NodoSentencia):
    def __init__(self, sentencias): self.sentencias = sentencias 
class NodoDeclaracionVariableCPP(NodoSentencia): 
    def __init__(self, tipo_nodo, declaradores): self.tipo_nodo = tipo_nodo; self.declaradores = declaradores 
class NodoDeclaradorVariableCPP(NodoAST_CPP):
    def __init__(self, nombre_variable_qname_tokens, inicializador_nodo=None, es_puntero=0, es_referencia=False, es_array_dims=None):
        self.nombre_variable_qname_tokens = nombre_variable_qname_tokens; self.inicializador_nodo = inicializador_nodo; self.nombre = "".join([t.lexema for t in nombre_variable_qname_tokens]); self.es_puntero = es_puntero; self.es_referencia = es_referencia; self.es_array_dims = es_array_dims if es_array_dims is not None else [] 
class NodoSentenciaExpresionCPP(NodoSentencia):
    def __init__(self, expresion_nodo): self.expresion_nodo = expresion_nodo
class NodoSentenciaReturnCPP(NodoSentencia):
    def __init__(self, expresion_nodo=None): self.expresion_nodo = expresion_nodo
class NodoSentenciaIfCPP(NodoSentencia):
    def __init__(self, condicion_nodo, cuerpo_then_nodo, cuerpo_else_nodo=None):
        self.condicion_nodo = condicion_nodo; self.cuerpo_then_nodo = cuerpo_then_nodo; self.cuerpo_else_nodo = cuerpo_else_nodo
class NodoIdentificadorCPP(NodoExpresion):
    def __init__(self, qname_tokens): 
        self.qname_tokens = qname_tokens; self.nombre_completo = "".join([t.lexema for t in qname_tokens]); self.nombre_simple = qname_tokens[-1].lexema; self.es_calificado = len(qname_tokens) > 1 and any(t.lexema == "::" for t in qname_tokens)
class NodoLiteralCPP(NodoExpresion):
    def __init__(self, token_literal):
        self.token_literal = token_literal; self.valor = token_literal.valor; self.tipo_literal_original = token_literal.tipo 
class NodoExpresionBinariaCPP(NodoExpresion):
    def __init__(self, operador_token, izquierda_nodo, derecha_nodo):
        self.operador_token = operador_token; self.izquierda_nodo = izquierda_nodo; self.derecha_nodo = derecha_nodo; self.operador = operador_token.lexema
class NodoLlamadaFuncionCPP(NodoExpresion): 
    def __init__(self, callee_nodo, argumentos_nodos): self.callee_nodo = callee_nodo; self.argumentos_nodos = argumentos_nodos 
class NodoMiembroExpresion(NodoExpresion): 
    def __init__(self, objeto_nodo, propiedad_token_o_nodo, es_arrow=False, es_calculado=False):
        self.objeto_nodo = objeto_nodo
        self.propiedad_token_o_nodo = propiedad_token_o_nodo 
        self.es_arrow = es_arrow 
        self.es_calculado = es_calculado
        if isinstance(propiedad_token_o_nodo, Token):
            self.nombre_propiedad = propiedad_token_o_nodo.lexema
        elif isinstance(propiedad_token_o_nodo, NodoIdentificadorCPP): 
            self.nombre_propiedad = propiedad_token_o_nodo.nombre_simple 
        else: 
            self.nombre_propiedad = None

class NodoSentenciaWhileCPP(NodoSentencia):
    """Representa una sentencia while en C++: while (condicion) cuerpo;"""
    def __init__(self, condicion_nodo, cuerpo_nodo):
        self.condicion_nodo = condicion_nodo # NodoExpresion
        self.cuerpo_nodo = cuerpo_nodo       # NodoSentencia (puede ser NodoBloqueSentenciasCPP) 

class NodoSentenciaForCPP(NodoSentencia):
    """Representa una sentencia for en C++: for (init; cond; update) cuerpo;"""
    def __init__(self, inicializacion_nodo, condicion_nodo, actualizacion_nodo, cuerpo_nodo):
        self.inicializacion_nodo = inicializacion_nodo # Puede ser NodoDeclaracionVariableCPP o NodoExpresionSQL
        self.condicion_nodo = condicion_nodo         # NodoExpresionSQL o None
        self.actualizacion_nodo = actualizacion_nodo   # NodoExpresionSQL o None
        self.cuerpo_nodo = cuerpo_nodo               # NodoSentencia
# --- Fin de Definiciones de Nodos del AST ---

class ParserCPP:
    def __init__(self, tokens):
        self.tokens = [token for token in tokens if token.tipo != 'WHITESPACE_CPP']
        self.posicion_actual = 0
        self.token_actual = self.tokens[self.posicion_actual] if self.tokens else None
        self.errores_sintacticos = []

    def _avanzar(self):
        self.posicion_actual += 1
        if self.posicion_actual < len(self.tokens):
            self.token_actual = self.tokens[self.posicion_actual]
        else:
            self.token_actual = self.tokens[-1] if self.tokens and self.tokens[-1].tipo == TT_EOF_CPP else None

    def _error_sintactico(self, mensaje_esperado):
        mensaje = "Error Sintáctico Desconocido en C++"
        if self.token_actual and self.token_actual.tipo != TT_EOF_CPP:
            mensaje = (f"Error Sintáctico C++ en L{self.token_actual.linea}:C{self.token_actual.columna}. "
                       f"Se esperaba {mensaje_esperado}, pero se encontró '{self.token_actual.lexema}' (tipo: {self.token_actual.tipo}).")
        elif self.token_actual and self.token_actual.tipo == TT_EOF_CPP:
            mensaje = (f"Error Sintáctico C++: Final inesperado del archivo (L{self.token_actual.linea}:C{self.token_actual.columna}). "
                       f"Se esperaba {mensaje_esperado}.")
        else: 
            last_token_info = self.tokens[-2] if len(self.tokens) > 1 and self.tokens[-1].tipo == TT_EOF_CPP else \
                              (self.tokens[-1] if self.tokens else None)
            linea_aprox = last_token_info.linea if last_token_info else 'desconocida'
            col_aprox = last_token_info.columna if last_token_info else 'desconocida'
            mensaje = (f"Error Sintáctico C++: Final inesperado de la entrada (cerca de L{linea_aprox}:C{col_aprox}). "
                       f"Se esperaba {mensaje_esperado}.")
        self.errores_sintacticos.append(mensaje)
        print(mensaje) 
        raise SyntaxError(mensaje)

    def _consumir(self, tipo_token_esperado, lexema_esperado=None):
        token_a_consumir = self.token_actual
        if token_a_consumir and token_a_consumir.tipo == tipo_token_esperado:
            if lexema_esperado is None or token_a_consumir.lexema == lexema_esperado:
                self._avanzar()
                return token_a_consumir
            else:
                self._error_sintactico(f"el lexema '{lexema_esperado}' para el token de tipo '{tipo_token_esperado}'")
        else:
            if lexema_esperado:
                self._error_sintactico(f"el lexema '{lexema_esperado}' (tipo: {tipo_token_esperado})")
            else:
                self._error_sintactico(f"un token de tipo '{tipo_token_esperado}'")
        return None 

    def parse(self):
        ast_raiz = None
        try:
            ast_raiz = self._parse_traduccion_unidad()
            if not self.errores_sintacticos and self.token_actual and self.token_actual.tipo != TT_EOF_CPP:
                self._error_sintactico("el final de la unidad de traducción (EOF)")
            if not self.errores_sintacticos and ast_raiz:
                 print("Análisis sintáctico de C++ y construcción de AST completados exitosamente.")
        except SyntaxError:
            ast_raiz = None 
        except Exception as e:
            print(f"Error inesperado durante el parsing de C++: {e}")
            import traceback
            traceback.print_exc()
            ast_raiz = None
        if self.errores_sintacticos and not ast_raiz:
             print(f"Resumen: Parsing de C++ falló con {len(self.errores_sintacticos)} error(es) sintáctico(s) detectado(s).")
        return ast_raiz

    def _parse_traduccion_unidad(self):
        # print("[DEBUG CPP Parser] _parse_traduccion_unidad") 
        declaraciones = []
        while self.token_actual and self.token_actual.tipo != TT_EOF_CPP:
            while self.token_actual and self.token_actual.tipo == TT_PUNTO_Y_COMA:
                self._consumir(TT_PUNTO_Y_COMA)
            if self.token_actual and self.token_actual.tipo != TT_EOF_CPP:
                declaracion_nodo = self._parse_declaracion_global_o_definicion()
                if declaracion_nodo:
                    declaraciones.append(declaracion_nodo)
                elif not self.errores_sintacticos and \
                     self.token_actual and self.token_actual.tipo != TT_EOF_CPP:
                     self._error_sintactico("una declaración o definición global válida")
        return NodoTraduccionUnidad(declaraciones)

    def _parse_declaracion_global_o_definicion(self):
        # print(f"[DEBUG CPP Parser] _parse_declaracion_global_o_definicion. Token: {self.token_actual}") 
        if self.token_actual is None: return None
        if self.token_actual.tipo == TT_DIRECTIVA_PREPROCESADOR:
            token_directiva = self._consumir(TT_DIRECTIVA_PREPROCESADOR)
            return NodoDirectivaPreprocesador(token_directiva)
        elif self.token_actual.tipo == TT_PALABRA_CLAVE:
            lexema_actual = self.token_actual.lexema 
            if lexema_actual == 'using':
                return self._parse_using_namespace_statement()
            elif lexema_actual == 'namespace':
                return self._parse_namespace_definicion()
            elif lexema_actual in ['class', 'struct', 'union', 'enum']: 
                return self._parse_definicion_tipo_agregado()
            elif self._es_potencial_inicio_de_declaracion_o_definicion_tipo():
                if self._es_definicion_funcion_probable():
                    return self._parse_definicion_funcion()
                else:
                    return self._parse_declaracion_variable_cpp_global_o_sentencia() 
            else:
                self._error_sintactico(f"una declaración o definición global válida. Palabra clave '{lexema_actual}' no esperada aquí.")
        elif self.token_actual.tipo == TT_IDENTIFICADOR and self._es_potencial_inicio_de_declaracion_o_definicion_tipo():
            if self._es_definicion_funcion_probable():
                 return self._parse_definicion_funcion()
            else:
                return self._parse_declaracion_variable_cpp_global_o_sentencia() 
        elif self.token_actual.tipo == TT_PUNTO_Y_COMA: 
            self._consumir(TT_PUNTO_Y_COMA)
            return None 
        else:
            self._error_sintactico(f"una declaración o definición global válida. Se encontró '{self.token_actual.lexema if self.token_actual else 'EOF'}'.")
        return None 

    def _es_potencial_inicio_de_declaracion_o_definicion_tipo(self):
        # print(f"[DEBUG CPP Parser] _es_potencial_inicio_de_declaracion_o_definicion_tipo. Token: {self.token_actual}") 
        if not self.token_actual: return False
        if self.token_actual.tipo == TT_PALABRA_CLAVE and \
           self.token_actual.lexema in ['int', 'void', 'char', 'double', 'float', 'bool', 'auto', 
                                       'class', 'struct', 'enum', 'union', 'typename', 
                                       'const', 'static', 'extern', 'typedef', 'unsigned', 
                                       'signed', 'long', 'short', 'template', 'constexpr']:
            # print(f"[DEBUG CPP Parser] _es_potencial_inicio_de_declaracion_o_definicion_tipo: Es palabra clave de tipo.")
            return True
        if self.token_actual.tipo == TT_IDENTIFICADOR: 
            # print(f"[DEBUG CPP Parser] _es_potencial_inicio_de_declaracion_o_definicion_tipo: Es identificador (potencial tipo).")
            return True
        # print(f"[DEBUG CPP Parser] _es_potencial_inicio_de_declaracion_o_definicion_tipo: No es tipo potencial.")
        return False

    def _parse_using_namespace_statement(self):
        # print("[DEBUG CPP Parser] _parse_using_namespace_statement") 
        self._consumir(TT_PALABRA_CLAVE, 'using')
        self._consumir(TT_PALABRA_CLAVE, 'namespace')
        qname_tokens = []
        qname_tokens.append(self._consumir(TT_IDENTIFICADOR)) 
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR_MIEMBRO and self.token_actual.lexema == '::':
            qname_tokens.append(self._consumir(TT_OPERADOR_MIEMBRO, '::'))
            qname_tokens.append(self._consumir(TT_IDENTIFICADOR))
        self._consumir(TT_PUNTO_Y_COMA)
        return NodoUsingNamespace(qname_tokens)

    def _parse_namespace_definicion(self):
        # print("[DEBUG CPP Parser] _parse_namespace_definicion") 
        self._consumir(TT_PALABRA_CLAVE, 'namespace')
        nombre_ns_token = None
        if self.token_actual and self.token_actual.tipo == TT_IDENTIFICADOR:
            nombre_ns_token = self._consumir(TT_IDENTIFICADOR)
        self._consumir(TT_LLAVE_IZQ)
        declaraciones_internas = self._parse_lista_declaraciones_globales_hasta_llave_der()
        self._consumir(TT_LLAVE_DER)
        if self.token_actual and self.token_actual.tipo == TT_PUNTO_Y_COMA:
            self._consumir(TT_PUNTO_Y_COMA)
        return NodoNamespaceDefinicion(nombre_ns_token, declaraciones_internas)

    def _parse_definicion_tipo_agregado(self): 
        # print(f"[DEBUG CPP Parser] _parse_definicion_tipo_agregado. Token: {self.token_actual}") 
        token_clase_o_struct = self._consumir(TT_PALABRA_CLAVE) 
        nombre_clase_token = None
        if self.token_actual and self.token_actual.tipo == TT_IDENTIFICADOR:
            nombre_clase_token = self._consumir(TT_IDENTIFICADOR)
        miembros_nodos = []
        if self.token_actual and self.token_actual.tipo == TT_LLAVE_IZQ:
            self._consumir(TT_LLAVE_IZQ)
            miembros_nodos = self._parse_lista_miembros_clase() 
            self._consumir(TT_LLAVE_DER)
        self._consumir(TT_PUNTO_Y_COMA) 
        if nombre_clase_token: 
            return NodoDefinicionClase(token_clase_o_struct, nombre_clase_token, miembros_nodos)
        else:
            # print(f"INFO (ParserCPP): Definición de tipo agregado '{token_clase_o_struct.lexema}' sin nombre o no soportada completamente.")
            return None

    # --- MÉTODO _parse_lista_miembros_clase ACTUALIZADO ---
    def _parse_lista_miembros_clase(self):
        """Parsea la lista de miembros dentro de una clase/struct."""
        miembros = []
        # print(f"[DEBUG CPP Parser] Entrando a _parse_lista_miembros_clase. Token actual: {self.token_actual}")
        while self.token_actual and self.token_actual.tipo != TT_LLAVE_DER and self.token_actual.tipo != TT_EOF_CPP:
            # print(f"[DEBUG CPP Parser _parse_lista_miembros_clase] Iteración. Token: {self.token_actual}")
            miembro_nodo = self._parse_miembro_clase() 
            if miembro_nodo:
                # print(f"[DEBUG CPP Parser _parse_lista_miembros_clase] Miembro parseado: {type(miembro_nodo).__name__}")
                miembros.append(miembro_nodo)
            elif not self.errores_sintacticos and \
                 self.token_actual and self.token_actual.tipo != TT_LLAVE_DER:
                 # Si _parse_miembro_clase devolvió None (ej. para especificador de acceso o ';')
                 # y no avanzó el token, podría causar un bucle infinito.
                 # Sin embargo, _parse_miembro_clase debería consumir el token o lanzar error.
                 # Si no se consumió nada y no es el fin del bloque, es un error.
                 # Esta condición es para atrapar si _parse_miembro_clase devuelve None sin consumir.
                 # Pero en la lógica actual, si devuelve None, ya consumió (ej. 'public:').
                 pass
            # print(f"[DEBUG CPP Parser _parse_lista_miembros_clase] Fin de iteración. Token: {self.token_actual}")
        # print(f"[DEBUG CPP Parser] Saliendo de _parse_lista_miembros_clase. Miembros encontrados: {len(miembros)}")
        return miembros

    # --- MÉTODO DESPACHADOR PARA MIEMBROS DE CLASE ACTUALIZADO ---
    def _parse_miembro_clase(self):
        """
        Parsea una declaración de miembro dentro de una clase/struct.
        Puede ser un especificador de acceso, una variable miembro, o una función miembro.
        """
        # print(f"[DEBUG CPP Parser] _parse_miembro_clase. Token actual: {self.token_actual}")
        if self.token_actual is None: return None

        if self.token_actual.tipo == TT_PALABRA_CLAVE and \
           self.token_actual.lexema in ['public', 'private', 'protected']:
            especificador_token = self._consumir(TT_PALABRA_CLAVE)
            self._consumir(TT_DOS_PUNTOS) 
            # print(f"INFO (ParserCPP): Especificador de acceso '{especificador_token.lexema}' parseado.")
            return None 
        
        # print(f"[DEBUG CPP Parser _parse_miembro_clase] Antes de _es_potencial_inicio_de_declaracion_o_definicion_tipo. Token: {self.token_actual}")
        es_potencial_tipo = self._es_potencial_inicio_de_declaracion_o_definicion_tipo()
        # print(f"[DEBUG CPP Parser _parse_miembro_clase] Resultado de _es_potencial_inicio_de_declaracion_o_definicion_tipo: {es_potencial_tipo}")

        if es_potencial_tipo:
            # print(f"[DEBUG CPP Parser - _parse_miembro_clase] Potencial tipo detectado: {self.token_actual}")
            # print(f"[DEBUG CPP Parser _parse_miembro_clase] Antes de _es_definicion_funcion_probable. Token: {self.token_actual}")
            es_func_probable = self._es_definicion_funcion_probable()
            # print(f"[DEBUG CPP Parser _parse_miembro_clase] Resultado de _es_definicion_funcion_probable: {es_func_probable}")
            if es_func_probable: 
                # print(f"[DEBUG CPP Parser - _parse_miembro_clase] Es función probable. Llamando a _parse_definicion_funcion.")
                nodo_funcion = self._parse_definicion_funcion()
                if nodo_funcion: 
                    if hasattr(nodo_funcion, 'es_metodo_clase'):
                        nodo_funcion.es_metodo_clase = True 
                    # print(f"[DEBUG CPP Parser _parse_miembro_clase] Definición de función parseada: {nodo_funcion.nombre if nodo_funcion else 'None'}")
                return nodo_funcion
            else:
                # print(f"[DEBUG CPP Parser - _parse_miembro_clase] No es función probable. Tratando como declaración de variable miembro.")
                nodo_decl_var = self._parse_declaracion_variable_cpp_local() 
                # print(f"[DEBUG CPP Parser _parse_miembro_clase] Declaración de variable parseada.")
                return nodo_decl_var
        
        elif self.token_actual.tipo == TT_PUNTO_Y_COMA: 
            # print(f"[DEBUG CPP Parser _parse_miembro_clase] Consumiendo punto y coma vacío.")
            self._consumir(TT_PUNTO_Y_COMA)
            return None
            
        else:
            # print(f"[DEBUG CPP Parser _parse_miembro_clase] Error: Token inesperado {self.token_actual}")
            self._error_sintactico("una declaración de miembro de clase/struct válida (tipo, función, especificador de acceso) o '}'")
        return None
    # --- FIN DE ACTUALIZACIÓN ---
    
    def _consumir_bloque_simple_llaves(self):
        self._consumir(TT_LLAVE_IZQ)
        profundidad = 1
        while self.token_actual and self.token_actual.tipo != TT_EOF_CPP and profundidad > 0:
            if self.token_actual.tipo == TT_LLAVE_IZQ: profundidad += 1
            elif self.token_actual.tipo == TT_LLAVE_DER: profundidad -= 1
            self._avanzar()
        if profundidad != 0: self._error_sintactico("llave de cierre '}' para el bloque")

    def _es_definicion_funcion_probable(self):
        # print(f"[DEBUG _es_func_probable] Inicio. Token actual: {self.token_actual}") 
        pos_original = self.posicion_actual; token_original = self.token_actual
        es_probable = False
        try:
            # print(f"[DEBUG _es_func_probable] Antes de _parse_tipo_simple_cpp. Token: {self.token_actual}") 
            if not self._parse_tipo_simple_cpp(avanzar_tokens=False): 
                # print(f"[DEBUG _es_func_probable] _parse_tipo_simple_cpp (peek) devolvió False.") 
                return False 
            
            self._parse_tipo_simple_cpp(avanzar_tokens=True) 
            # print(f"[DEBUG _es_func_probable] Después de _parse_tipo_simple_cpp(avanzar=True). Token actual: {self.token_actual}") 
            
            if self.token_actual and (self.token_actual.tipo == TT_IDENTIFICADOR or \
               (self.token_actual.tipo == TT_PALABRA_CLAVE and self.token_actual.lexema == 'operator')):
                # print(f"[DEBUG _es_func_probable] Potencial nombre/operator: {self.token_actual.lexema}") 
                self._avanzar() 
                
                if token_original.lexema == 'operator' and self.token_actual and \
                   self.token_actual.tipo in [TT_OPERADOR_ARITMETICO, TT_OPERADOR_COMPARACION, TT_PARENTESIS_IZQ, TT_CORCHETE_IZQ]:
                    # print(f"[DEBUG _es_func_probable] Consumiendo símbolo de operador: {self.token_actual.lexema}") 
                    self._avanzar()

                while self.token_actual and self.token_actual.tipo == TT_OPERADOR_MIEMBRO and self.token_actual.lexema == '::':
                    # print(f"[DEBUG _es_func_probable] Consumiendo ::") 
                    self._avanzar() 
                    if self.token_actual and self.token_actual.tipo == TT_IDENTIFICADOR:
                        # print(f"[DEBUG _es_func_probable] Consumiendo parte del nombre calificado: {self.token_actual.lexema}") 
                        self._avanzar() 
                    else: 
                        # print(f"[DEBUG _es_func_probable] Se esperaba ID después de :: pero se encontró {self.token_actual}") 
                        break 
            else: 
                # print(f"[DEBUG _es_func_probable] No es ID u operator después del tipo. Token: {self.token_actual}") 
                return False 

            if self.token_actual and self.token_actual.tipo == TT_PARENTESIS_IZQ:
                # print(f"[DEBUG _es_func_probable] Encontrado '('. Es probable función.") 
                es_probable = True 
            # else:
                # print(f"[DEBUG _es_func_probable] No se encontró '('. Token: {self.token_actual}") 

        except SyntaxError: 
            # print(f"[DEBUG _es_func_probable] SyntaxError durante el lookahead.") 
            pass 
        finally:
            self.posicion_actual = pos_original 
            self.token_actual = token_original
            # print(f"[DEBUG _es_func_probable] Restaurado. Token actual: {self.token_actual}. Retornando: {es_probable}") 
        return es_probable

    def _parse_definicion_funcion(self):
        # print(f"[DEBUG CPP Parser] _parse_definicion_funcion. Token: {self.token_actual}") # DEBUG
        tipo_retorno_nodo = self._parse_tipo_cpp() 
        nombre_qname_tokens = []
        while True:
            if self.token_actual and (self.token_actual.tipo == TT_IDENTIFICADOR or \
                (self.token_actual.tipo == TT_PALABRA_CLAVE and self.token_actual.lexema == 'operator')):
                nombre_qname_tokens.append(self._consumir(self.token_actual.tipo))
                if nombre_qname_tokens[-1].lexema == 'operator' and self.token_actual and \
                   self.token_actual.tipo in [TT_OPERADOR_ARITMETICO, TT_OPERADOR_COMPARACION, TT_PARENTESIS_IZQ, TT_CORCHETE_IZQ]: 
                    nombre_qname_tokens.append(self._consumir(self.token_actual.tipo)) 
            else: self._error_sintactico("un nombre de función o 'operator'")
            if self.token_actual and self.token_actual.tipo == TT_OPERADOR_MIEMBRO and self.token_actual.lexema == '::':
                nombre_qname_tokens.append(self._consumir(TT_OPERADOR_MIEMBRO, '::'))
            else: break 
        self._consumir(TT_PARENTESIS_IZQ)
        parametros_nodos = self._parse_lista_parametros_funcion_cpp()
        self._consumir(TT_PARENTESIS_DER)
        es_const_metodo = False
        if self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE and self.token_actual.lexema == 'const':
            self._consumir(TT_PALABRA_CLAVE, 'const')
            es_const_metodo = True
        cuerpo_nodo = None
        if self.token_actual and self.token_actual.tipo == TT_LLAVE_IZQ: 
            cuerpo_nodo = self._parse_bloque_sentencias_cpp() 
        elif self.token_actual and self.token_actual.tipo == TT_PUNTO_Y_COMA: 
            self._consumir(TT_PUNTO_Y_COMA)
            # print(f"INFO (ParserCPP): Prototipo de función '{''.join([t.lexema for t in nombre_qname_tokens])}' parseado.")
        else: self._error_sintactico("'{' para el cuerpo de la función o ';' para una declaración de función")
        return NodoDefinicionFuncion(tipo_retorno_nodo, nombre_qname_tokens, parametros_nodos, cuerpo_nodo, es_const=es_const_metodo)

    def _parse_tipo_cpp(self, permitir_void_sin_nombre=False):
        # print(f"[DEBUG CPP Parser] _parse_tipo_cpp. Token: {self.token_actual}") # DEBUG
        tokens_del_tipo = []; es_const = False; es_volatile = False 
        is_qualifier = True
        while is_qualifier and self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE:
            lex = self.token_actual.lexema
            if lex == 'const': tokens_del_tipo.append(self._consumir(TT_PALABRA_CLAVE, 'const')); es_const = True
            elif lex == 'volatile': tokens_del_tipo.append(self._consumir(TT_PALABRA_CLAVE, 'volatile')); es_volatile = True
            else: is_qualifier = False
        is_type_modifier = True
        while is_type_modifier and self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE:
            lex = self.token_actual.lexema
            if lex in ['unsigned', 'signed', 'long', 'short']: tokens_del_tipo.append(self._consumir(TT_PALABRA_CLAVE, lex))
            else: is_type_modifier = False
        
        if self.token_actual and (self.token_actual.tipo == TT_PALABRA_CLAVE or self.token_actual.tipo == TT_IDENTIFICADOR):
            if self.token_actual.lexema == 'void' and permitir_void_sin_nombre:
                 tokens_del_tipo.append(self._consumir(TT_PALABRA_CLAVE, 'void'))
            elif self.token_actual.lexema != 'void' or not permitir_void_sin_nombre: 
                 tokens_del_tipo.append(self._consumir(self.token_actual.tipo)) 
                 while self.token_actual and self.token_actual.tipo == TT_OPERADOR_MIEMBRO and self.token_actual.lexema == '::':
                     tokens_del_tipo.append(self._consumir(TT_OPERADOR_MIEMBRO, '::'))
                     tokens_del_tipo.append(self._consumir(TT_IDENTIFICADOR)) 
            else: 
                if not permitir_void_sin_nombre and self.token_actual.lexema == 'void':
                    es_puntero_o_ref_void = False
                    if self.posicion_actual + 1 < len(self.tokens):
                        siguiente_token = self.tokens[self.posicion_actual + 1] 
                        if (siguiente_token.tipo == TT_OPERADOR_ARITMETICO and siguiente_token.lexema == '*') or \
                           (siguiente_token.tipo == TT_OPERADOR_BITWISE and siguiente_token.lexema == '&'):
                           es_puntero_o_ref_void = True
                    if not es_puntero_o_ref_void: self._error_sintactico("un tipo de dato válido (void solo es válido como tipo de retorno o puntero/referencia void)")
                    else: tokens_del_tipo.append(self._consumir(TT_PALABRA_CLAVE, 'void'))
        elif not tokens_del_tipo: self._error_sintactico("un tipo de dato válido")

        nivel_puntero = 0; es_referencia = False
        while self.token_actual and (
              (self.token_actual.tipo == TT_OPERADOR_ARITMETICO and self.token_actual.lexema == '*') or \
              (self.token_actual.tipo == TT_ASTERISCO and self.token_actual.lexema == '*') or 
              (self.token_actual.tipo == TT_OPERADOR_BITWISE and self.token_actual.lexema == '&') ): 
            if self.token_actual.lexema == '*': 
                self._consumir(self.token_actual.tipo, '*')
                nivel_puntero += 1
            elif self.token_actual.lexema == '&':
                if es_referencia or nivel_puntero > 0: self._error_sintactico("modificador de tipo inválido después de puntero o referencia")
                self._consumir(TT_OPERADOR_BITWISE, '&'); es_referencia = True
            else: break
        if self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE:
            if self.token_actual.lexema == 'const' and not es_const : tokens_del_tipo.append(self._consumir(TT_PALABRA_CLAVE, 'const')); es_const = True 
            elif self.token_actual.lexema == 'volatile' and not es_volatile: tokens_del_tipo.append(self._consumir(TT_PALABRA_CLAVE, 'volatile')); es_volatile = True
        return NodoTipoCPP(tokens_del_tipo, es_puntero=nivel_puntero, es_referencia=es_referencia, es_const_qualifier=es_const, es_volatile_qualifier=es_volatile)

    def _parse_tipo_simple_cpp(self, avanzar_tokens=False):
        # print(f"[DEBUG _parse_tipo_simple_cpp] (avanzar={avanzar_tokens}) Inicio. Token: {self.token_actual if avanzar_tokens else self.tokens[self.posicion_actual] if self.posicion_actual < len(self.tokens) else None}") 
        pos_guardada = self.posicion_actual; token_guardado = self.token_actual
        tipo_consumido_lexemas = [] 
        
        current_pos_temp = pos_guardada 
        current_token_temp = token_guardado

        def _avanzar_effective():
            nonlocal current_pos_temp, current_token_temp
            if avanzar_tokens:
                self._avanzar()
            else:
                current_pos_temp += 1
                if current_pos_temp < len(self.tokens): current_token_temp = self.tokens[current_pos_temp]
                else: current_token_temp = None
        
        def _get_token_effective():
            return self.token_actual if avanzar_tokens else current_token_temp

        try:
            while _get_token_effective() and _get_token_effective().tipo == TT_PALABRA_CLAVE and \
                  _get_token_effective().lexema in ['const', 'unsigned', 'signed', 'long', 'short', 'static', 'extern', 'volatile']:
                tipo_consumido_lexemas.append(_get_token_effective().lexema); _avanzar_effective()
            
            if _get_token_effective() and (_get_token_effective().tipo == TT_PALABRA_CLAVE or _get_token_effective().tipo == TT_IDENTIFICADOR):
                tipo_consumido_lexemas.append(_get_token_effective().lexema); _avanzar_effective()
            elif not tipo_consumido_lexemas: 
                # print(f"[DEBUG _parse_tipo_simple_cpp] (avanzar={avanzar_tokens}) No se consumió nada, retornando False.") 
                if not avanzar_tokens: self.posicion_actual = pos_guardada; self.token_actual = token_guardado
                return False 

            while _get_token_effective() and _get_token_effective().tipo == TT_OPERADOR_MIEMBRO and _get_token_effective().lexema == '::':
                tipo_consumido_lexemas.append("::"); _avanzar_effective() 
                if _get_token_effective() and _get_token_effective().tipo == TT_IDENTIFICADOR:
                    tipo_consumido_lexemas.append(_get_token_effective().lexema); _avanzar_effective() 
                else: 
                    # print(f"[DEBUG _parse_tipo_simple_cpp] (avanzar={avanzar_tokens}) Se esperaba ID después de ::. Retornando False.") 
                    if not avanzar_tokens: self.posicion_actual = pos_guardada; self.token_actual = token_guardado
                    return False 
            
            while _get_token_effective() and _get_token_effective().lexema in ['*', '&'] and \
                  ( (_get_token_effective().lexema == '*' and _get_token_effective().tipo in [TT_OPERADOR_ARITMETICO, TT_ASTERISCO]) or \
                    (_get_token_effective().lexema == '&' and _get_token_effective().tipo == TT_OPERADOR_BITWISE) ):
                 tipo_consumido_lexemas.append(_get_token_effective().lexema); _avanzar_effective()
            
            # print(f"[DEBUG _parse_tipo_simple_cpp] (avanzar={avanzar_tokens}) Consumido: {tipo_consumido_lexemas}, Próximo token para _es_func_probable: {_get_token_effective()}") 
            return True
            
        except Exception: 
            # print(f"[DEBUG _parse_tipo_simple_cpp] (avanzar={avanzar_tokens}) Excepción. Retornando False.") 
            if not avanzar_tokens: self.posicion_actual = pos_guardada; self.token_actual = token_guardado
            return False
        finally:
            if not avanzar_tokens: 
                self.posicion_actual = pos_guardada
                self.token_actual = token_guardado

    def _parse_lista_parametros_funcion_cpp(self):
        
        parametros = []
        if self.token_actual and self.token_actual.tipo != TT_PARENTESIS_DER:
            while True:
                tipo_nodo = self._parse_tipo_cpp(permitir_void_sin_nombre=True) 
                nombre_token = None
                if self.token_actual and self.token_actual.tipo == TT_IDENTIFICADOR:
                    nombre_token = self._consumir(TT_IDENTIFICADOR)
                parametros.append(NodoParametroFuncion(tipo_nodo, nombre_token))
                if self.token_actual and self.token_actual.tipo == TT_COMA:
                    self._consumir(TT_COMA)
                else:
                    break
        return parametros

    def _parse_bloque_sentencias_cpp(self):
        # print(f"[DEBUG CPP Parser] Entrando a _parse_bloque_sentencias_cpp. Token: {self.token_actual}") # DEBUG
        self._consumir(TT_LLAVE_IZQ)
        sentencias = []
        while self.token_actual and self.token_actual.tipo != TT_LLAVE_DER and self.token_actual.tipo != TT_EOF_CPP:
            while self.token_actual and self.token_actual.tipo == TT_PUNTO_Y_COMA:
                self._consumir(TT_PUNTO_Y_COMA)
            if self.token_actual and self.token_actual.tipo != TT_LLAVE_DER and self.token_actual.tipo != TT_EOF_CPP:
                nodo_sent = self._parse_sentencia_cpp_interna() 
                if nodo_sent:
                    sentencias.append(nodo_sent)
                elif not self.errores_sintacticos and \
                     self.token_actual and self.token_actual.tipo not in [TT_LLAVE_DER, TT_EOF_CPP]:
                     self._error_sintactico("una sentencia válida o '}'")
        self._consumir(TT_LLAVE_DER)
        # print(f"[DEBUG CPP Parser] Saliendo de _parse_bloque_sentencias_cpp. Token: {self.token_actual}") # DEBUG
        return NodoBloqueSentenciasCPP(sentencias)

    def _parse_sentencia_cpp_interna(self):
        # print(f"[DEBUG CPP Parser] _parse_sentencia_cpp_interna. Token: {self.token_actual}") # DEBUG
        if self.token_actual is None: return None
        if self.token_actual.tipo == TT_DIRECTIVA_PREPROCESADOR:
            token_directiva = self._consumir(TT_DIRECTIVA_PREPROCESADOR)
            return NodoDirectivaPreprocesador(token_directiva)
        if self._es_potencial_inicio_de_declaracion_o_definicion_tipo():
            pos_guardada = self.posicion_actual; token_guardado = self.token_actual
            es_decl_var_probable = False
            try:
                self._parse_tipo_simple_cpp(avanzar_tokens=True) 
                if self.token_actual and self.token_actual.tipo == TT_IDENTIFICADOR:
                    self._avanzar() 
                    if self.token_actual and self.token_actual.tipo in [TT_PUNTO_Y_COMA, TT_OPERADOR_ASIGNACION, TT_PARENTESIS_IZQ, TT_CORCHETE_IZQ, TT_COMA]:
                        es_decl_var_probable = True
                elif self.token_actual and self.token_actual.tipo == TT_PUNTO_Y_COMA: 
                    es_decl_var_probable = True 
            except SyntaxError: pass 
            finally: self.posicion_actual = pos_guardada; self.token_actual = token_guardado
            if es_decl_var_probable:
                return self._parse_declaracion_variable_cpp_local()
        if self.token_actual.tipo == TT_PALABRA_CLAVE:
            lexema = self.token_actual.lexema
            if lexema == 'return':
                return self._parse_sentencia_return_cpp()
            if lexema == 'if': 
                return self._parse_sentencia_if_cpp()
            if lexema == 'while': 
                return self._parse_sentencia_while_cpp()
            if lexema == 'for': 
                return self._parse_sentencia_for_cpp()
        nodo_expr = self._parse_expresion_cpp() 
        self._consumir(TT_PUNTO_Y_COMA) 
        return NodoSentenciaExpresionCPP(nodo_expr)

    def _parse_declaracion_variable_cpp_local(self):
        # print(f"[DEBUG CPP Parser] _parse_declaracion_variable_cpp_local. Token: {self.token_actual}") # DEBUG
        tipo_nodo = self._parse_tipo_cpp()
        declaradores = self._parse_declarador_variable_cpp_lista()
        self._consumir(TT_PUNTO_Y_COMA)
        return NodoDeclaracionVariableCPP(tipo_nodo, declaradores)

    def _parse_declaracion_variable_cpp_global_o_sentencia(self):
        # print(f"[DEBUG CPP Parser] _parse_declaracion_variable_cpp_global_o_sentencia. Token: {self.token_actual}") # DEBUG
        pos_guardada = self.posicion_actual; token_guardado = self.token_actual
        try:
            tipo_nodo = self._parse_tipo_cpp()
            declaradores = self._parse_declarador_variable_cpp_lista()
            self._consumir(TT_PUNTO_Y_COMA)
            return NodoDeclaracionVariableCPP(tipo_nodo, declaradores)
        except SyntaxError:
            self.posicion_actual = pos_guardada; self.token_actual = token_guardado
            if self._es_potencial_inicio_de_declaracion_o_definicion_tipo() or \
               (self.token_actual and (self.token_actual.tipo == TT_IDENTIFICADOR or \
                self.token_actual.tipo == TT_LITERAL_ENTERO) ): 
                expr_nodo = self._parse_expresion_cpp()
                self._consumir(TT_PUNTO_Y_COMA)
                return NodoSentenciaExpresionCPP(expr_nodo)
            else:
                self._error_sintactico("una declaración de variable o una sentencia de expresión válida")
        return None

    def _parse_declarador_variable_cpp_lista(self):
        # print(f"[DEBUG CPP Parser] _parse_declarador_variable_cpp_lista. Token: {self.token_actual}") # DEBUG
        declaradores = []
        declaradores.append(self._parse_un_declarador_cpp())
        while self.token_actual and self.token_actual.tipo == TT_COMA:
            self._consumir(TT_COMA)
            declaradores.append(self._parse_un_declarador_cpp())
        return declaradores

    def _parse_un_declarador_cpp(self):
        # print(f"[DEBUG CPP Parser] _parse_un_declarador_cpp. Token: {self.token_actual}") # DEBUG
        es_puntero_decl = 0; es_referencia_decl = False
        while self.token_actual and \
              ((self.token_actual.tipo == TT_OPERADOR_ARITMETICO and self.token_actual.lexema == '*') or \
               (self.token_actual.tipo == TT_ASTERISCO and self.token_actual.lexema == '*') or \
               (self.token_actual.tipo == TT_OPERADOR_BITWISE and self.token_actual.lexema == '&')):
            if self.token_actual.lexema == '*':
                self._consumir(self.token_actual.tipo, '*')
                es_puntero_decl += 1
            elif self.token_actual.lexema == '&':
                if es_referencia_decl or es_puntero_decl > 0: self._error_sintactico("modificador de tipo inválido en declarador")
                self._consumir(TT_OPERADOR_BITWISE, '&'); es_referencia_decl = True
        nombre_token = self._consumir(TT_IDENTIFICADOR) 
        qname_tokens_var = [nombre_token] 
        array_dims_nodos = []
        while self.token_actual and self.token_actual.tipo == TT_CORCHETE_IZQ:
            self._consumir(TT_CORCHETE_IZQ)
            if self.token_actual.tipo != TT_CORCHETE_DER: 
                array_dims_nodos.append(self._parse_expresion_cpp())
            else: array_dims_nodos.append(None) 
            self._consumir(TT_CORCHETE_DER)
        inicializador_nodo = None
        if self.token_actual and self.token_actual.tipo == TT_OPERADOR_ASIGNACION and self.token_actual.lexema == '=':
            self._consumir(TT_OPERADOR_ASIGNACION, '=')
            inicializador_nodo = self._parse_expresion_cpp() 
        elif self.token_actual and self.token_actual.tipo == TT_PARENTESIS_IZQ: 
            self._consumir(TT_PARENTESIS_IZQ)
            args_init = []
            if self.token_actual.tipo != TT_PARENTESIS_DER:
                while True:
                    args_init.append(self._parse_expresion_cpp()) 
                    if self.token_actual.tipo == TT_COMA: self._consumir(TT_COMA)
                    else: break
            self._consumir(TT_PARENTESIS_DER)
            inicializador_nodo = NodoLlamadaFuncionCPP(NodoIdentificadorCPP(qname_tokens_var), args_init)
        elif self.token_actual and self.token_actual.tipo == TT_LLAVE_IZQ: 
            self._consumir_bloque_simple_llaves()
        return NodoDeclaradorVariableCPP(qname_tokens_var, inicializador_nodo, 
                                         es_puntero=es_puntero_decl, 
                                         es_referencia=es_referencia_decl,
                                         es_array_dims=array_dims_nodos)

    def _parse_sentencia_return_cpp(self):
        # print("[DEBUG CPP Parser] _parse_sentencia_return_cpp") # DEBUG
        self._consumir(TT_PALABRA_CLAVE, 'return')
        expresion_nodo = None
        if self.token_actual and self.token_actual.tipo != TT_PUNTO_Y_COMA:
            expresion_nodo = self._parse_expresion_cpp() 
        self._consumir(TT_PUNTO_Y_COMA)
        return NodoSentenciaReturnCPP(expresion_nodo)
    
    def _parse_sentencia_if_cpp(self):
        # print("[DEBUG CPP Parser] _parse_sentencia_if_cpp") # DEBUG
        self._consumir(TT_PALABRA_CLAVE, 'if')
        self._consumir(TT_PARENTESIS_IZQ)
        condicion_nodo = self._parse_expresion_cpp() 
        self._consumir(TT_PARENTESIS_DER)
        cuerpo_then_nodo = self._parse_cuerpo_de_control_cpp()
        cuerpo_else_nodo = None
        if self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE and self.token_actual.lexema == 'else':
            self._consumir(TT_PALABRA_CLAVE, 'else')
            cuerpo_else_nodo = self._parse_cuerpo_de_control_cpp()
        return NodoSentenciaIfCPP(condicion_nodo, cuerpo_then_nodo, cuerpo_else_nodo)
    
    def _parse_sentencia_while_cpp(self):
        """Parsea una sentencia while: while (expresion) sentencia_o_bloque"""
        # print(f"[DEBUG CPP Parser] _parse_sentencia_while_cpp. Token: {self.token_actual}") # DEBUG
        self._consumir(TT_PALABRA_CLAVE, 'while')
        self._consumir(TT_PARENTESIS_IZQ)
        condicion_nodo = self._parse_expresion_cpp()
        self._consumir(TT_PARENTESIS_DER)
        cuerpo_nodo = self._parse_cuerpo_de_control_cpp()
        return NodoSentenciaWhileCPP(condicion_nodo, cuerpo_nodo)
    
    def _parse_sentencia_for_cpp(self):
        """Parsea una sentencia for: for (inicializacion; condicion; actualizacion) cuerpo"""
        # print(f"[DEBUG CPP Parser] _parse_sentencia_for_cpp. Token: {self.token_actual}") # DEBUG
        self._consumir(TT_PALABRA_CLAVE, 'for')
        self._consumir(TT_PARENTESIS_IZQ)

        # 1. Inicialización (puede ser declaración de variable o expresión)
        inicializacion_nodo = None
        if self.token_actual and self.token_actual.tipo != TT_PUNTO_Y_COMA:
            # ¿Cómo distinguir una declaración de una expresión aquí?
            # Si comienza con un tipo conocido o 'auto', es una declaración.
            # Sino, es una lista de expresiones.
            # Por ahora, simplificamos: si es un tipo, es declaración, sino expresión.
            if self._es_potencial_inicio_de_declaracion_o_definicion_tipo():
                # Nota: _parse_declaracion_variable_cpp_local espera un ';' al final,
                # pero en un for, la declaración de inicialización no lo lleva.
                # Necesitamos una variante o consumir el ';' opcionalmente.
                # Por ahora, vamos a asumir que si es un tipo, es una declaración completa
                # y el ; lo manejará el consumo del ; de la cabecera del for.
                # Esto es una simplificación y podría necesitar un método
                # _parse_declaracion_simple_sin_semicolon()
                
                # Guardar estado para retroceder si no es una declaración válida aquí
                pos_guardada_init = self.posicion_actual
                token_guardado_init = self.token_actual
                try:
                    # Intentar parsear como una declaración de variable, pero sin consumir el ; final
                    # Esto es complicado porque _parse_declaracion_variable_cpp_local espera un ;
                    # Solución temporal: parsear el tipo y luego los declaradores, pero no el ;
                    
                    # Si el siguiente token es ';', es una declaración vacía.
                    if self.token_actual.tipo != TT_PUNTO_Y_COMA:
                        tipo_nodo_init = self._parse_tipo_cpp()
                        declaradores_init = self._parse_declarador_variable_cpp_lista()
                        inicializacion_nodo = NodoDeclaracionVariableCPP(tipo_nodo_init, declaradores_init)
                    # No consumir el ';' aquí, lo hace el for.
                except SyntaxError:
                    # Si falla como declaración, restaurar e intentar como expresión
                    self.posicion_actual = pos_guardada_init
                    self.token_actual = token_guardado_init
                    if self.token_actual.tipo != TT_PUNTO_Y_COMA: # Solo si no es una inicialización vacía
                        inicializacion_nodo = self._parse_expresion_cpp() 
            elif self.token_actual.tipo != TT_PUNTO_Y_COMA: # No es tipo, pero no es ; -> es expresión
                inicializacion_nodo = self._parse_expresion_cpp()
        
        self._consumir(TT_PUNTO_Y_COMA)

        # 2. Condición (expresión opcional)
        condicion_nodo = None
        if self.token_actual and self.token_actual.tipo != TT_PUNTO_Y_COMA:
            condicion_nodo = self._parse_expresion_cpp()
        self._consumir(TT_PUNTO_Y_COMA)

        # 3. Actualización (expresión opcional)
        actualizacion_nodo = None
        if self.token_actual and self.token_actual.tipo != TT_PARENTESIS_DER:
            actualizacion_nodo = self._parse_expresion_cpp()
        
        self._consumir(TT_PARENTESIS_DER)
        cuerpo_nodo = self._parse_cuerpo_de_control_cpp()
        
        return NodoSentenciaForCPP(inicializacion_nodo, condicion_nodo, actualizacion_nodo, cuerpo_nodo)


    def _parse_cuerpo_de_control_cpp(self):
        # print(f"[DEBUG CPP Parser] _parse_cuerpo_de_control_cpp. Token: {self.token_actual}") # DEBUG
        if self.token_actual and self.token_actual.tipo == TT_LLAVE_IZQ:
            return self._parse_bloque_sentencias_cpp()
        else:
            return self._parse_sentencia_cpp_interna()
    
    # --- JERARQUÍA DE PARSING DE EXPRESIONES C++ ---
    def _parse_expresion_cpp(self): 
        # print(f"[DEBUG CPP Parser] _parse_expresion_cpp. Token: {self.token_actual}") # DEBUG
        return self._parse_expresion_asignacion_cpp()

    def _parse_expresion_asignacion_cpp(self):
        # print(f"[DEBUG CPP Parser] _parse_expresion_asignacion_cpp. Token: {self.token_actual}") # DEBUG
        nodo_izq = self._parse_expresion_logica_or_cpp() 
        if self.token_actual and self.token_actual.tipo == TT_OPERADOR_ASIGNACION:
            op_token = self._consumir(TT_OPERADOR_ASIGNACION)
            nodo_der = self._parse_expresion_asignacion_cpp() 
            return NodoExpresionBinariaCPP(op_token, nodo_izq, nodo_der) 
        return nodo_izq

    def _parse_expresion_logica_or_cpp(self):
        # print(f"[DEBUG CPP Parser] _parse_expresion_logica_or_cpp. Token: {self.token_actual}") # DEBUG
        nodo = self._parse_expresion_logica_and_cpp()
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR_LOGICO and self.token_actual.lexema == '||':
            op_token = self._consumir(TT_OPERADOR_LOGICO)
            nodo_der = self._parse_expresion_logica_and_cpp()
            nodo = NodoExpresionBinariaCPP(op_token, nodo, nodo_der)
        return nodo

    def _parse_expresion_logica_and_cpp(self):
        # print(f"[DEBUG CPP Parser] _parse_expresion_logica_and_cpp. Token: {self.token_actual}") # DEBUG
        nodo = self._parse_expresion_bitwise_or_cpp()
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR_LOGICO and self.token_actual.lexema == '&&':
            op_token = self._consumir(TT_OPERADOR_LOGICO)
            nodo_der = self._parse_expresion_bitwise_or_cpp()
            nodo = NodoExpresionBinariaCPP(op_token, nodo, nodo_der)
        return nodo

    def _parse_expresion_bitwise_or_cpp(self):
        # print(f"[DEBUG CPP Parser] _parse_expresion_bitwise_or_cpp. Token: {self.token_actual}") # DEBUG
        nodo = self._parse_expresion_bitwise_xor_cpp()
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR_BITWISE and self.token_actual.lexema == '|':
            op_token = self._consumir(TT_OPERADOR_BITWISE)
            nodo_der = self._parse_expresion_bitwise_xor_cpp()
            nodo = NodoExpresionBinariaCPP(op_token, nodo, nodo_der)
        return nodo

    def _parse_expresion_bitwise_xor_cpp(self):
        # print(f"[DEBUG CPP Parser] _parse_expresion_bitwise_xor_cpp. Token: {self.token_actual}") # DEBUG
        nodo = self._parse_expresion_bitwise_and_cpp()
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR_BITWISE and self.token_actual.lexema == '^':
            op_token = self._consumir(TT_OPERADOR_BITWISE)
            nodo_der = self._parse_expresion_bitwise_and_cpp()
            nodo = NodoExpresionBinariaCPP(op_token, nodo, nodo_der)
        return nodo

    def _parse_expresion_bitwise_and_cpp(self):
        # print(f"[DEBUG CPP Parser] _parse_expresion_bitwise_and_cpp. Token: {self.token_actual}") # DEBUG
        nodo = self._parse_expresion_igualdad_cpp()
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR_BITWISE and self.token_actual.lexema == '&':
            op_token = self._consumir(TT_OPERADOR_BITWISE)
            nodo_der = self._parse_expresion_igualdad_cpp()
            nodo = NodoExpresionBinariaCPP(op_token, nodo, nodo_der)
        return nodo

    def _parse_expresion_igualdad_cpp(self):
        # print(f"[DEBUG CPP Parser] _parse_expresion_igualdad_cpp. Token: {self.token_actual}") # DEBUG
        nodo = self._parse_expresion_relacional_cpp()
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR_COMPARACION and \
              self.token_actual.lexema in ['==', '!=']:
            op_token = self._consumir(TT_OPERADOR_COMPARACION)
            nodo_der = self._parse_expresion_relacional_cpp()
            nodo = NodoExpresionBinariaCPP(op_token, nodo, nodo_der)
        return nodo

    def _parse_expresion_relacional_cpp(self):
        # print(f"[DEBUG CPP Parser] _parse_expresion_relacional_cpp. Token: {self.token_actual}") # DEBUG
        nodo = self._parse_expresion_shift_cpp()
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR_COMPARACION and \
              self.token_actual.lexema in ['<', '<=', '>', '>=']:
            op_token = self._consumir(TT_OPERADOR_COMPARACION)
            nodo_der = self._parse_expresion_shift_cpp()
            nodo = NodoExpresionBinariaCPP(op_token, nodo, nodo_der)
        return nodo

    def _parse_expresion_shift_cpp(self): 
        # print(f"[DEBUG CPP Parser] _parse_expresion_shift_cpp. Token: {self.token_actual}") # DEBUG
        nodo = self._parse_expresion_aditiva_cpp()
        while self.token_actual and \
              self.token_actual.tipo == TT_OPERADOR_BITWISE and \
              self.token_actual.lexema in ['<<', '>>']:
            operador_token = self._consumir(TT_OPERADOR_BITWISE)
            nodo_derecho = self._parse_expresion_aditiva_cpp()
            nodo = NodoExpresionBinariaCPP(operador_token, nodo, nodo_derecho)
        return nodo
        
    def _parse_expresion_aditiva_cpp(self): 
        # print(f"[DEBUG CPP Parser] _parse_expresion_aditiva_cpp. Token: {self.token_actual}") # DEBUG
        nodo = self._parse_expresion_multiplicativa_cpp()
        while self.token_actual and \
              self.token_actual.tipo == TT_OPERADOR_ARITMETICO and \
              self.token_actual.lexema in ['+', '-']:
            operador_token = self._consumir(TT_OPERADOR_ARITMETICO)
            nodo_derecho = self._parse_expresion_multiplicativa_cpp()
            nodo = NodoExpresionBinariaCPP(operador_token, nodo, nodo_derecho)
        return nodo

    def _parse_expresion_multiplicativa_cpp(self): 
        # print(f"[DEBUG CPP Parser] _parse_expresion_multiplicativa_cpp. Token: {self.token_actual}") # DEBUG
        nodo = self._parse_expresion_prefijo_unario_cpp() 
        while self.token_actual and \
              self.token_actual.tipo == TT_OPERADOR_ARITMETICO and \
              self.token_actual.lexema in ['*', '/', '%']: 
            operador_token = self._consumir(TT_OPERADOR_ARITMETICO) 
            nodo_derecho = self._parse_expresion_prefijo_unario_cpp()
            nodo = NodoExpresionBinariaCPP(operador_token, nodo, nodo_derecho)
        return nodo

    def _parse_expresion_prefijo_unario_cpp(self):
        # print(f"[DEBUG CPP Parser] _parse_expresion_prefijo_unario_cpp. Token: {self.token_actual}") # DEBUG
        if self.token_actual and (
            (self.token_actual.tipo == TT_OPERADOR_ARITMETICO and self.token_actual.lexema in ['++', '--', '+', '-']) or \
            (self.token_actual.tipo == TT_OPERADOR_LOGICO and self.token_actual.lexema == '!') or \
            (self.token_actual.tipo == TT_OPERADOR_BITWISE and self.token_actual.lexema == '~') or \
            (self.token_actual.tipo == TT_ASTERISCO and self.token_actual.lexema == '*') or 
            (self.token_actual.tipo == TT_OPERADOR_BITWISE and self.token_actual.lexema == '&') or 
            (self.token_actual.tipo == TT_PALABRA_CLAVE and self.token_actual.lexema in ['sizeof', 'new', 'delete'])
            ):
            op_token = self._consumir(self.token_actual.tipo) 
            operando_nodo = self._parse_expresion_prefijo_unario_cpp() 
            # print(f"INFO (ParserCPP): Operador unario PREFIJO '{op_token.lexema}' parseado.")
            return operando_nodo 
        return self._parse_expresion_postfija_cpp()

    def _parse_expresion_postfija_cpp(self): 
        # print(f"[DEBUG CPP Parser] _parse_expresion_postfija_cpp. Token: {self.token_actual}") # DEBUG
        nodo_expr = self._parse_expresion_primaria_cpp()
        while True:
            if self.token_actual and self.token_actual.tipo == TT_PUNTO: 
                self._consumir(TT_PUNTO)
                propiedad_token = self._consumir(TT_IDENTIFICADOR) 
                nodo_expr = NodoMiembroExpresion(nodo_expr, propiedad_token, es_arrow=False) 
            elif self.token_actual and self.token_actual.tipo == TT_OPERADOR_MIEMBRO and self.token_actual.lexema == '->': 
                self._consumir(TT_OPERADOR_MIEMBRO, '->')
                propiedad_token = self._consumir(TT_IDENTIFICADOR)
                nodo_expr = NodoMiembroExpresion(nodo_expr, propiedad_token, es_arrow=True)
            elif self.token_actual and self.token_actual.tipo == TT_PARENTESIS_IZQ: 
                self._consumir(TT_PARENTESIS_IZQ)
                argumentos_nodos = []
                if self.token_actual.tipo != TT_PARENTESIS_DER:
                    while True:
                        argumentos_nodos.append(self._parse_expresion_asignacion_cpp()) 
                        if self.token_actual.tipo == TT_COMA:
                            self._consumir(TT_COMA)
                        else:
                            break
                self._consumir(TT_PARENTESIS_DER)
                nodo_expr = NodoLlamadaFuncionCPP(nodo_expr, argumentos_nodos)
            elif self.token_actual and self.token_actual.tipo == TT_CORCHETE_IZQ: 
                self._consumir(TT_CORCHETE_IZQ)
                indice_nodo = self._parse_expresion_cpp() 
                self._consumir(TT_CORCHETE_DER)
                nodo_expr = NodoMiembroExpresion(nodo_expr, indice_nodo, es_calculado=True)
            else:
                break
        return nodo_expr

    def _parse_expresion_primaria_cpp(self):
        # print(f"[DEBUG CPP Parser] _parse_expresion_primaria_cpp. Token: {self.token_actual}") # DEBUG
        if self.token_actual and self.token_actual.tipo == TT_IDENTIFICADOR:
            qname_tokens = [self._consumir(TT_IDENTIFICADOR)]
            while self.token_actual and self.token_actual.tipo == TT_OPERADOR_MIEMBRO and self.token_actual.lexema == '::':
                qname_tokens.append(self._consumir(TT_OPERADOR_MIEMBRO, "::"))
                qname_tokens.append(self._consumir(TT_IDENTIFICADOR))
            return NodoIdentificadorCPP(qname_tokens)
        elif self.token_actual and self.token_actual.tipo in [TT_LITERAL_ENTERO, TT_LITERAL_FLOTANTE, TT_LITERAL_CADENA, TT_LITERAL_CARACTER]:
            return NodoLiteralCPP(self._consumir(self.token_actual.tipo))
        elif self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE and self.token_actual.lexema in ['true', 'false', 'nullptr']:
            return NodoLiteralCPP(self._consumir(TT_PALABRA_CLAVE)) 
        elif self.token_actual and self.token_actual.tipo == TT_PARENTESIS_IZQ: 
            self._consumir(TT_PARENTESIS_IZQ)
            expr_nodo = self._parse_expresion_cpp() 
            self._consumir(TT_PARENTESIS_DER)
            return expr_nodo
        else:
            self._error_sintactico("un identificador, literal o '(' en expresión primaria")
        return None 
    
    def _consumir_hasta_delimitador_o_bloque(self, delimitadores):
        profundidad_parentesis = 0; profundidad_llaves = 0; profundidad_corchetes = 0
        while self.token_actual and self.token_actual.tipo != TT_EOF_CPP:
            if self.token_actual.tipo == TT_PARENTESIS_IZQ: profundidad_parentesis += 1
            elif self.token_actual.tipo == TT_PARENTESIS_DER: profundidad_parentesis -= 1
            elif self.token_actual.tipo == TT_LLAVE_IZQ: profundidad_llaves += 1
            elif self.token_actual.tipo == TT_LLAVE_DER: profundidad_llaves -= 1
            elif self.token_actual.tipo == TT_CORCHETE_IZQ: profundidad_corchetes += 1
            elif self.token_actual.tipo == TT_CORCHETE_DER: profundidad_corchetes -= 1
            if profundidad_parentesis == 0 and profundidad_llaves == 0 and profundidad_corchetes == 0:
                if self.token_actual.lexema in delimitadores and self.token_actual.tipo in [TT_PUNTO_Y_COMA, TT_LLAVE_IZQ, TT_PARENTESIS_IZQ]:
                    break 
            self._avanzar()
            if self.token_actual is None or self.token_actual.tipo == TT_EOF_CPP: break
            
    def _parse_lista_declaraciones_globales_hasta_llave_der(self):
        declaraciones = []
        while self.token_actual and self.token_actual.tipo != TT_LLAVE_DER and self.token_actual.tipo != TT_EOF_CPP:
            while self.token_actual and self.token_actual.tipo == TT_PUNTO_Y_COMA:
                self._consumir(TT_PUNTO_Y_COMA)
            if self.token_actual and self.token_actual.tipo != TT_LLAVE_DER and self.token_actual.tipo != TT_EOF_CPP:
                decl_nodo = self._parse_declaracion_global_o_definicion()
                if decl_nodo:
                    declaraciones.append(decl_nodo)
                elif not self.errores_sintacticos and \
                     self.token_actual and self.token_actual.tipo not in [TT_LLAVE_DER, TT_EOF_CPP]:
                     self._error_sintactico("una declaración o definición válida dentro del namespace o '}'")
        return declaraciones

    def _consumir_hasta_punto_y_coma_o_llave_apertura(self):
        while self.token_actual and self.token_actual.tipo not in [TT_PUNTO_Y_COMA, TT_LLAVE_IZQ, TT_EOF_CPP]:
            self._avanzar()
        if self.token_actual and self.token_actual.tipo == TT_PUNTO_Y_COMA:
            self._avanzar()
# Fin de la clase ParserCPP
