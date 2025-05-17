# src/analizador_sintactico/parser_cpp.py

# Importaciones necesarias (se añadirán a medida que se necesiten los tipos de token)
try:
    from analizador_lexico.lexer_cpp import (
        TT_PALABRA_CLAVE, TT_IDENTIFICADOR, TT_LITERAL_ENTERO, TT_LITERAL_FLOTANTE,
        TT_LITERAL_CADENA, TT_LITERAL_CARACTER, TT_DIRECTIVA_PREPROCESADOR,
        TT_OPERADOR_ASIGNACION, TT_OPERADOR_ARITMETICO, TT_OPERADOR_COMPARACION,
        TT_OPERADOR_LOGICO, TT_OPERADOR_MIEMBRO, TT_PUNTO_Y_COMA, TT_COMA,
        TT_PARENTESIS_IZQ, TT_PARENTESIS_DER, TT_LLAVE_IZQ, TT_LLAVE_DER,
        TT_EOF_CPP, TT_CORCHETE_DER, TT_CORCHETE_IZQ, TT_OPERADOR_BITWISE, TT_ASTERISCO, TT_PUNTO
        # Añadir más tipos de token según se necesiten.
    )
    from analizador_lexico.lexer_cpp import Token # Si se necesita la clase Token
except ImportError:
    print("ADVERTENCIA CRÍTICA (ParserCPP): No se pudieron importar los tipos de token de LexerCPP.")
    # Definir placeholders para que el archivo al menos cargue.
    TT_PALABRA_CLAVE, TT_IDENTIFICADOR, TT_EOF_CPP = "PALABRA_CLAVE_CPP", "IDENTIFICADOR_CPP", "EOF_CPP"
    TT_DIRECTIVA_PREPROCESADOR = "DIRECTIVA_PREPROCESADOR_CPP"
    TT_LLAVE_IZQ, TT_LLAVE_DER = "LLAVE_IZQ_CPP", "LLAVE_DER_CPP"
    TT_PUNTO_Y_COMA = "PUNTO_Y_COMA_CPP"
    
    # ... (añadir más placeholders si son referenciados antes de su uso real)
    class Token: pass # Placeholder básico
    pass

# --- Definiciones de Nodos del AST para C++ ---
# (Las clases NodoAST_CPP, NodoTraduccionUnidad, NodoDeclaracion, NodoSentencia,
#  NodoExpresion, NodoDirectivaPreprocesador, NodoUsingNamespace, NodoDefinicionFuncion,
#  NodoParametroFuncion, NodoTipoCPP, NodoBloqueSentenciasCPP, NodoDeclaracionVariableCPP,
#  NodoDeclaradorVariableCPP, NodoSentenciaExpresionCPP, NodoSentenciaReturnCPP,
#  NodoIdentificadorCPP, NodoLiteralCPP, NodoExpresionBinariaCPP, NodoLlamadaFuncionCPP
#  permanecen aquí como las definimos en el paso anterior)

class NodoAST_CPP:
    """Clase base para todos los nodos del AST de C++."""
    def __repr__(self, indent=0):
        indent_str = "  " * indent
        attrs = {k: v for k, v in self.__dict__.items() if not k.startswith('_') and not isinstance(v, list) and not isinstance(v, NodoAST_CPP) and v is not None}
        attr_str_parts = []
        for k,v in attrs.items():
            if isinstance(v, Token): attr_str_parts.append(f"{k}='{v.lexema}'")
            elif isinstance(v, str): attr_str_parts.append(f"{k}='{v}'")
            else: attr_str_parts.append(f"{k}={v}")
        attr_str = ", ".join(attr_str_parts)
        
        children_repr_list = []
        for k, v in self.__dict__.items():
            if isinstance(v, NodoAST_CPP):
                children_repr_list.append(f"\n{v.__repr__(indent + 1)}")
            elif isinstance(v, list) and all(isinstance(item, (NodoAST_CPP, Token)) for item in v): 
                if v: 
                    list_items_repr = "\n".join([(item.__repr__(indent + 2) if isinstance(item, NodoAST_CPP) else f"{indent_str}  Token({item.tipo},'{item.lexema}')") for item in v])
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
    def __init__(self, declaraciones_globales):
        self.declaraciones_globales = declaraciones_globales

class NodoDeclaracion(NodoAST_CPP): pass
class NodoSentencia(NodoAST_CPP): pass
class NodoExpresion(NodoAST_CPP): pass

class NodoDirectivaPreprocesador(NodoDeclaracion):
    def __init__(self, token_directiva):
        self.token_directiva = token_directiva
        self.directiva = ''
        self.argumentos = ''
        self.archivo_cabecera = None
        self.tipo_cabecera = None
        if isinstance(token_directiva.valor, dict):
            self.directiva = token_directiva.valor.get('directiva', '')
            self.argumentos = token_directiva.valor.get('argumentos', '')
            if 'archivo' in token_directiva.valor:
                self.archivo_cabecera = token_directiva.valor['archivo']
                self.tipo_cabecera = token_directiva.valor.get('tipo_cabecera')

class NodoUsingNamespace(NodoDeclaracion):
    """Representa 'using namespace nombre_namespace;'"""
    def __init__(self, tokens_qname_namespace): 
        # tokens_qname_namespace: Lista de tokens IDENTIFICADOR y '::' que forman el nombre calificado.
        self.tokens_qname_namespace = tokens_qname_namespace
        self.nombre_namespace_str = "".join([t.lexema for t in tokens_qname_namespace])

class NodoNamespaceDefinicion(NodoDeclaracion):
    """Representa una definición de namespace: namespace nombre { ... }"""
    def __init__(self, nombre_namespace_token, declaraciones_internas):
        self.nombre_namespace_token = nombre_namespace_token # Token IDENTIFICADOR
        self.declaraciones_internas = declaraciones_internas # Lista de nodos de declaración/definición
        self.nombre = nombre_namespace_token.lexema if nombre_namespace_token else None # Namespace anónimo

class NodoDefinicionClase(NodoDeclaracion):
    def __init__(self, token_clase_o_struct, nombre_clase_token, miembros_nodos):
        self.token_clase_o_struct = token_clase_o_struct 
        self.nombre_clase_token = nombre_clase_token     
        self.miembros_nodos = miembros_nodos             
        self.nombre = nombre_clase_token.lexema if nombre_clase_token else "ClaseAnónima"



class NodoDefinicionFuncion(NodoDeclaracion):
    def __init__(self, tipo_retorno_nodo, nombre_funcion_qname_tokens, parametros_nodos, cuerpo_nodo_bloque, es_const=False, es_extern_c=False):
        self.tipo_retorno_nodo = tipo_retorno_nodo 
        self.nombre_funcion_qname_tokens = nombre_funcion_qname_tokens 
        self.parametros_nodos = parametros_nodos     
        self.cuerpo_nodo_bloque = cuerpo_nodo_bloque   
        self.nombre = "".join([t.lexema for t in nombre_funcion_qname_tokens])
        self.es_const = es_const 
        self.es_extern_c = es_extern_c

class NodoParametroFuncion(NodoAST_CPP):
    def __init__(self, tipo_param_nodo, nombre_param_token=None, valor_defecto_nodo=None):
        self.tipo_param_nodo = tipo_param_nodo 
        self.nombre_param_token = nombre_param_token 
        self.valor_defecto_nodo = valor_defecto_nodo 

class NodoTipoCPP(NodoAST_CPP):
    def __init__(self, tokens_tipo, es_puntero=0, es_referencia=False, es_const_qualifier=False, es_volatile_qualifier=False): 
        self.tokens_tipo = tokens_tipo 
        self.es_puntero = es_puntero 
        self.es_referencia = es_referencia 
        self.es_const_qualifier = es_const_qualifier 
        self.es_volatile_qualifier = es_volatile_qualifier
        nombre_base = " ".join([t.lexema for t in tokens_tipo])
        self.nombre_tipo_str = ("const " if es_const_qualifier else "") + \
                               ("volatile " if es_volatile_qualifier else "") + \
                               nombre_base + \
                               "*"*es_puntero + \
                               ("&" if es_referencia else "")

class NodoBloqueSentenciasCPP(NodoSentencia):
    def __init__(self, sentencias):
        self.sentencias = sentencias 

class NodoDeclaracionVariableCPP(NodoSentencia): 
    def __init__(self, tipo_nodo, declaradores):
        self.tipo_nodo = tipo_nodo 
        self.declaradores = declaradores 

class NodoDeclaradorVariableCPP(NodoAST_CPP):
    def __init__(self, nombre_variable_qname_tokens, inicializador_nodo=None, es_puntero=0, es_referencia=False, es_array_dims=None):
        self.nombre_variable_qname_tokens = nombre_variable_qname_tokens # Lista de tokens para el nombre
        self.inicializador_nodo = inicializador_nodo   # NodoExpresion o None
        self.nombre = "".join([t.lexema for t in nombre_variable_qname_tokens]) # Nombre completo
        self.es_puntero = es_puntero # int, nivel de indirección de puntero específico a este declarador
        self.es_referencia = es_referencia # bool, si este declarador es una referencia
        self.es_array_dims = es_array_dims if es_array_dims is not None else [] # Lista de NodoExpresion para dimensiones

class NodoSentenciaExpresionCPP(NodoSentencia):
    def __init__(self, expresion_nodo):
        self.expresion_nodo = expresion_nodo

class NodoSentenciaReturnCPP(NodoSentencia):
    def __init__(self, expresion_nodo=None): 
        self.expresion_nodo = expresion_nodo

class NodoIdentificadorCPP(NodoExpresion):
    def __init__(self, qname_tokens): 
        self.qname_tokens = qname_tokens
        self.nombre_completo = "".join([t.lexema for t in qname_tokens])
        self.nombre_simple = qname_tokens[-1].lexema 
        self.es_calificado = len(qname_tokens) > 1 and any(t.lexema == "::" for t in qname_tokens)



class NodoLiteralCPP(NodoExpresion):
    def __init__(self, token_literal):
        self.token_literal = token_literal
        self.valor = token_literal.valor
        self.tipo_literal_original = token_literal.tipo 

class NodoExpresionBinariaCPP(NodoExpresion):
    def __init__(self, operador_token, izquierda_nodo, derecha_nodo):
        self.operador_token = operador_token
        self.izquierda_nodo = izquierda_nodo
        self.derecha_nodo = derecha_nodo
        self.operador = operador_token.lexema

class NodoLlamadaFuncionCPP(NodoExpresion): 
    def __init__(self, callee_nodo, argumentos_nodos):
        self.callee_nodo = callee_nodo 
        self.argumentos_nodos = argumentos_nodos 


class NodoSentenciaIfCPP(NodoSentencia):
    """Representa una sentencia if-else en C++."""
    def __init__(self, condicion_nodo, cuerpo_then_nodo, cuerpo_else_nodo=None):
        self.condicion_nodo = condicion_nodo     # NodoExpresion
        self.cuerpo_then_nodo = cuerpo_then_nodo # NodoSentencia (puede ser NodoBloqueSentenciasCPP)
        self.cuerpo_else_nodo = cuerpo_else_nodo # NodoSentencia (opcional)

class NodoMiembroExpresion(NodoExpresion):
    """Representa el acceso a un miembro de un objeto (ej: objeto.propiedad o objeto['propiedad'])."""
    def __init__(self, objeto_nodo, propiedad_token, es_calculado=False):
        # objeto_nodo: NodoExpresion que representa el objeto.
        # propiedad_nodo: NodoIdentificadorJS (para .propiedad) o NodoExpresion (para ['propiedad']).
        # es_calculado: Booleano, True si es acceso con [], False si es con .
        self.objeto_nodo = objeto_nodo
        self.propiedad_token = propiedad_token
        self.es_calculado = es_calculado
# --- Fin de Definiciones de Nodos del AST ---


# --- Clase ParserCPP ---
class ParserCPP:
    def __init__(self, tokens):
        """
        Inicializa el parser con la lista de tokens generada por el LexerCPP.
        Filtra los tokens de WHITESPACE_CPP ya que no son relevantes para el análisis sintáctico.
        """
        self.tokens = [token for token in tokens if token.tipo != 'WHITESPACE_CPP']
        self.posicion_actual = 0
        self.token_actual = self.tokens[self.posicion_actual] if self.tokens else None
        self.errores_sintacticos = []
        # from nucleo_compilador.tabla_simbolos import TablaSimbolos # Importar si se usa
        # self.tabla_simbolos = TablaSimbolos() # Para manejo de variables, funciones, etc.

    def _avanzar(self):
        """Avanza al siguiente token en la lista filtrada."""
        self.posicion_actual += 1
        if self.posicion_actual < len(self.tokens):
            self.token_actual = self.tokens[self.posicion_actual]
        else:
            # Si se llega al final, el token actual es el último token EOF o None.
            self.token_actual = self.tokens[-1] if self.tokens and self.tokens[-1].tipo == TT_EOF_CPP else None

    def _error_sintactico(self, mensaje_esperado):
        """Registra un error sintáctico y lanza una excepción para detener el parsing."""
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
        """
        Verifica el token actual. Si coincide, lo consume y avanza. Si no, reporta error.
        Devuelve el token consumido. C++ es sensible a mayúsculas/minúsculas para palabras clave.
        """
        token_a_consumir = self.token_actual
        if token_a_consumir and token_a_consumir.tipo == tipo_token_esperado:
            # Para C++, las palabras clave son sensibles a mayúsculas/minúsculas.
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
        return None # No se alcanza si _error_sintactico siempre lanza excepción.

    def parse(self):
        """
        Punto de entrada principal para el análisis sintáctico del código C++.
        Devuelve: Un NodoTraduccionUnidad que representa el AST, o None si hay errores.
        """
        ast_raiz = None
        try:
            ast_raiz = self._parse_traduccion_unidad()
            
            if not self.errores_sintacticos and self.token_actual and self.token_actual.tipo != TT_EOF_CPP:
                self._error_sintactico("el final de la unidad de traducción (EOF)")
            
            if not self.errores_sintacticos and ast_raiz:
                 print("Análisis sintáctico de C++ y construcción de AST completados exitosamente.")
            
        except SyntaxError:
            # El error ya fue impreso por _error_sintactico.
            print(f"Análisis sintáctico de C++ detenido debido a errores.")
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
        """
        Parsea una unidad de traducción (archivo .cpp), que es una secuencia de declaraciones globales.
        Gramática (simplificada): traduccion_unidad ::= (declaracion_global_o_definicion)*
        Devuelve: NodoTraduccionUnidad
        """
        declaraciones = []
        while self.token_actual and self.token_actual.tipo != TT_EOF_CPP:
            # Consumir puntos y comas vacíos a nivel global si los hubiera (aunque no es común en C++)
            while self.token_actual and self.token_actual.tipo == TT_PUNTO_Y_COMA:
                self._consumir(TT_PUNTO_Y_COMA)

            if self.token_actual and self.token_actual.tipo != TT_EOF_CPP:
                declaracion_nodo = self._parse_declaracion_global_o_definicion()
                if declaracion_nodo:
                    declaraciones.append(declaracion_nodo)
                elif not self.errores_sintacticos and \
                     self.token_actual and self.token_actual.tipo != TT_EOF_CPP:
                     # Si no se parseó nada y no es EOF, es un error.
                     self._error_sintactico("una declaración o definición global válida")
                # Si hay errores sintácticos, la excepción ya detuvo el flujo.
        return NodoTraduccionUnidad(declaraciones)

    def _parse_declaracion_global_o_definicion(self):
        """
        Despachador para parsear diferentes tipos de declaraciones/definiciones a nivel global.
        Ej: directivas, using namespace, definiciones de función, declaraciones de variable globales.
        Devuelve: Un nodo de declaración/definición o None.
        """
        if self.token_actual is None: return None
        # print(f"[DEBUG CPP Parser] _parse_declaracion_global. Token: {self.token_actual}")

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
            # --- LLAMADA AL MÉTODO QUE CAUSA EL ERROR ---
            elif self._es_potencial_inicio_de_declaracion_o_definicion_tipo(): 
                if self._es_definicion_funcion_probable():
                    return self._parse_definicion_funcion()
                else:
                    return self._parse_declaracion_variable_cpp_global_o_sentencia() 
            else:
                self._error_sintactico(f"una declaración o definición global válida. Palabra clave '{lexema_actual}' no esperada aquí.")
        
        # --- LLAMADA AL MÉTODO QUE CAUSA EL ERROR ---
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
    
    def _parse_declaracion_variable_cpp_global_o_sentencia(self):
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

    def _parse_namespace_definicion(self):
        self._consumir(TT_PALABRA_CLAVE, 'namespace')
        nombre_ns_token = None
        if self.token_actual and self.token_actual.tipo == TT_IDENTIFICADOR:
            nombre_ns_token = self._consumir(TT_IDENTIFICADOR)
        
        # Un namespace puede no tener nombre (anónimo) o puede ser calificado (a::b)
        # Por ahora, solo simple o anónimo.
        
        self._consumir(TT_LLAVE_IZQ)
        # El cuerpo de un namespace es una lista de declaraciones globales o definiciones
        declaraciones_internas = self._parse_lista_declaraciones_globales_hasta_llave_der()
        self._consumir(TT_LLAVE_DER)
        
        # Un namespace no termina necesariamente con punto y coma.
        return NodoNamespaceDefinicion(nombre_ns_token, declaraciones_internas)
    
    def _parse_definicion_tipo_agregado(self): 
        # (Como estaba antes, pero el cuerpo ahora llama a _parse_lista_miembros_clase)
        token_clase_o_struct = self._consumir(TT_PALABRA_CLAVE) 
        nombre_clase_token = None
        if self.token_actual and self.token_actual.tipo == TT_IDENTIFICADOR:
            nombre_clase_token = self._consumir(TT_IDENTIFICADOR)
        
        miembros_nodos = []
        if self.token_actual and self.token_actual.tipo == TT_LLAVE_IZQ:
            self._consumir(TT_LLAVE_IZQ)
            miembros_nodos = self._parse_lista_miembros_clase() # NUEVA LLAMADA
            self._consumir(TT_LLAVE_DER)
        
        self._consumir(TT_PUNTO_Y_COMA) 
        
        if nombre_clase_token: 
            return NodoDefinicionClase(token_clase_o_struct, nombre_clase_token, miembros_nodos)
        else:
            print(f"INFO (ParserCPP): Definición de tipo agregado '{token_clase_o_struct.lexema}' sin nombre o no soportada completamente.")
            return None
        
    def _parse_lista_miembros_clase(self):
        """Parsea la lista de miembros dentro de una clase/struct."""
        miembros = []
        # print(f"[DEBUG CPP Parser] Entrando a _parse_lista_miembros_clase. Token: {self.token_actual}")
        while self.token_actual and self.token_actual.tipo != TT_LLAVE_DER and self.token_actual.tipo != TT_EOF_CPP:
            # Aquí se parsearían declaraciones de variables miembro, funciones miembro,
            # especificadores de acceso (public, private, protected), using, typedefs, etc.
            # Por ahora, es un placeholder que consume tokens.
            # Un miembro típicamente termina en ';' o '}' (para funciones miembro).
            
            # Placeholder: consumir hasta el próximo ';' o '{' o '}'
            # Esto es muy simplificado y no construye el AST de los miembros.
            print(f"INFO (ParserCPP): Placeholder para miembro de clase/struct, consumiendo token: {self.token_actual}")
            # Para evitar bucles infinitos si el token no es uno esperado por _consumir_hasta_delimitador_o_bloque
            if self.token_actual.tipo in [TT_PUNTO_Y_COMA, TT_LLAVE_IZQ, TT_LLAVE_DER, TT_EOF_CPP]:
                if self.token_actual.tipo == TT_PUNTO_Y_COMA: self._avanzar() # Consumir el ;
                # Si es llave o EOF, el bucle while externo se encargará.
            else:
                self._avanzar() # Consumir el token actual para progresar

            # Si se implementara el parsing de miembros:
            # miembro_nodo = self._parse_declaracion_miembro_clase()
            # if miembro_nodo:
            #     miembros.append(miembro_nodo)
            # elif not self.errores_sintacticos:
            #     self._error_sintactico("una declaración de miembro válida o '}'")
        return miembros
    

    
    def _parse_definicion_tipo_agregado(self): # Para class, struct, union
        """Parsea una definición de class, struct, o union."""
        token_clase_o_struct = self._consumir(TT_PALABRA_CLAVE) # class, struct, o union
        nombre_clase_token = None
        if self.token_actual and self.token_actual.tipo == TT_IDENTIFICADOR:
            nombre_clase_token = self._consumir(TT_IDENTIFICADOR)
        
        miembros_nodos = []
        if self.token_actual and self.token_actual.tipo == TT_LLAVE_IZQ:
            self._consumir(TT_LLAVE_IZQ)
            # Placeholder mejorado para consumir miembros hasta '}'
            # Esto aún no crea nodos para los miembros.
            profundidad_llaves = 1
            while self.token_actual and self.token_actual.tipo != TT_EOF_CPP:
                if self.token_actual.tipo == TT_LLAVE_IZQ:
                    profundidad_llaves += 1
                    # print(f"INFO (ParserCPP): Placeholder dentro de clase/struct, anidamiento de llave aumentado a {profundidad_llaves}. Token: {self.token_actual}")
                    self._avanzar()
                elif self.token_actual.tipo == TT_LLAVE_DER:
                    profundidad_llaves -= 1
                    # print(f"INFO (ParserCPP): Placeholder dentro de clase/struct, anidamiento de llave reducido a {profundidad_llaves}. Token: {self.token_actual}")
                    if profundidad_llaves == 0: # Llave de cierre de la clase/struct
                        break 
                    self._avanzar()
                else:
                    # print(f"INFO (ParserCPP): Placeholder para miembro de clase/struct, consumiendo token: {self.token_actual}")
                    self._avanzar() 
            
            if self.token_actual and self.token_actual.tipo == TT_LLAVE_DER:
                 self._consumir(TT_LLAVE_DER)
            else: # Si EOF o algo más, es un error
                 self._error_sintactico("'}' para cerrar la definición de clase/struct")
        # else: Podría ser una declaración forward: class MiClase; (no manejado aún)
        
        self._consumir(TT_PUNTO_Y_COMA) # Clases/structs/unions terminan con ;
        
        # Solo crear nodo si hay un nombre, sino es una declaración forward o anónima no soportada
        if nombre_clase_token: 
            return NodoDefinicionClase(token_clase_o_struct, nombre_clase_token, miembros_nodos)
        else:
            # print(f"INFO (ParserCPP): Definición de tipo agregado '{token_clase_o_struct.lexema}' sin nombre o no soportada completamente.")
            return None

    def _parse_using_namespace_statement(self):
        """Parsea 'using namespace nombre_ns [:: sub_ns]* ;'"""
        self._consumir(TT_PALABRA_CLAVE, 'using')
        self._consumir(TT_PALABRA_CLAVE, 'namespace')
        qname_tokens = []
        qname_tokens.append(self._consumir(TT_IDENTIFICADOR)) 
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR_MIEMBRO and self.token_actual.lexema == '::':
            qname_tokens.append(self._consumir(TT_OPERADOR_MIEMBRO, '::'))
            qname_tokens.append(self._consumir(TT_IDENTIFICADOR))
        self._consumir(TT_PUNTO_Y_COMA)
        return NodoUsingNamespace(qname_tokens)
    
    # --- NUEVOS MÉTODOS PARA NAMESPACE Y DEFINICIÓN DE FUNCIÓN ---
    def _parse_namespace_definicion(self):
        """Parsea 'namespace [nombre] { declaraciones... }'"""
        self._consumir(TT_PALABRA_CLAVE, 'namespace')
        nombre_ns_token = None
        if self.token_actual and self.token_actual.tipo == TT_IDENTIFICADOR:
            nombre_ns_token = self._consumir(TT_IDENTIFICADOR)
        # (Aquí se podría manejar namespaces anónimos o anidados si nombre_ns_token es None
        #  o si hay '::' después del nombre)

        self._consumir(TT_LLAVE_IZQ)
        declaraciones_internas = []
        # Similar a _parse_traduccion_unidad o _parse_bloque_sentencias_cpp
        while self.token_actual and self.token_actual.tipo != TT_LLAVE_DER and self.token_actual.tipo != TT_EOF_CPP:
            while self.token_actual and self.token_actual.tipo == TT_PUNTO_Y_COMA:
                 self._consumir(TT_PUNTO_Y_COMA)
            if self.token_actual and self.token_actual.tipo != TT_LLAVE_DER and self.token_actual.tipo != TT_EOF_CPP:
                decl_nodo = self._parse_declaracion_global_o_definicion() # Recursión para declaraciones dentro del namespace
                if decl_nodo:
                    declaraciones_internas.append(decl_nodo)
                elif not self.errores_sintacticos and \
                     self.token_actual and self.token_actual.tipo not in [TT_LLAVE_DER, TT_EOF_CPP]:
                     self._error_sintactico("una declaración o definición válida dentro del namespace o '}'")
        
        self._consumir(TT_LLAVE_DER)
        return NodoNamespaceDefinicion(nombre_ns_token, declaraciones_internas)
    
    def _es_potencial_inicio_de_declaracion_o_definicion_tipo(self):
        """Verifica si el token actual podría ser el inicio de un tipo en una declaración/definición."""
        if not self.token_actual: return False
        # Palabras clave comunes que inician declaraciones/definiciones
        if self.token_actual.tipo == TT_PALABRA_CLAVE and \
           self.token_actual.lexema in ['int', 'void', 'char', 'double', 'float', 'bool', 'auto', 
                                       'class', 'struct', 'enum', 'union', 'typename', 
                                       'const', 'static', 'extern', 'typedef', 'unsigned', 
                                       'signed', 'long', 'short', 'template', 'constexpr']:
            return True
        # Un identificador podría ser un tipo definido por el usuario (typedef, class name)
        if self.token_actual.tipo == TT_IDENTIFICADOR: # Esta línea es la que se refiere el traceback
            return True 
        return False

    def _es_definicion_funcion_probable(self):
        """
        Heurística simple para intentar distinguir una definición de función
        de una declaración de variable, mirando hacia adelante.
        Busca un patrón como: TIPO IDENTIFICADOR ( ... ) { o ;
        Esto es muy simplificado y no cubre todos los casos de C++.
        """
        # print(f"[DEBUG _es_func_probable] Inicio. Token actual: {self.token_actual}") 
        pos_original = self.posicion_actual; token_original = self.token_actual
        es_probable = False
        try:
            # print(f"[DEBUG _es_func_probable] Antes de _parse_tipo_simple_cpp. Token: {self.token_actual}") 
            if not self._parse_tipo_simple_cpp(avanzar_tokens=False): 
                # print(f"[DEBUG _es_func_probable] _parse_tipo_simple_cpp (peek) devolvió False.") 
                return False 
            
            # Avanzar el parser real para simular el consumo del tipo
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
        """Parsea una definición de función (simplificada)."""
        # print(f"[DEBUG CPP Parser] Entrando a _parse_definicion_funcion. Token: {self.token_actual}")
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
            cuerpo_nodo = self._parse_bloque_sentencias_cpp() # LLAMADA ACTUALIZADA
        elif self.token_actual and self.token_actual.tipo == TT_PUNTO_Y_COMA: 
            self._consumir(TT_PUNTO_Y_COMA)
            print(f"INFO (ParserCPP): Prototipo de función '{''.join([t.lexema for t in nombre_qname_tokens])}' parseado.")
        else: self._error_sintactico("'{' para el cuerpo de la función o ';' para una declaración de función")
        return NodoDefinicionFuncion(tipo_retorno_nodo, nombre_qname_tokens, parametros_nodos, cuerpo_nodo, es_const=es_const_metodo)



    def _parse_tipo_cpp(self, permitir_void_sin_nombre=False):
        """Parsea un tipo de dato C++. Puede incluir const, unsigned, long, *, &."""
        tokens_del_tipo = []
        es_const = False
        es_volatile = False 
        
        # Consumir calificadores iniciales (const, volatile)
        while self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE:
            lex = self.token_actual.lexema
            if lex == 'const':
                tokens_del_tipo.append(self._consumir(TT_PALABRA_CLAVE, 'const'))
                es_const = True
            elif lex == 'volatile':
                tokens_del_tipo.append(self._consumir(TT_PALABRA_CLAVE, 'volatile'))
                es_volatile = True
            else:
                break 
        
        # Consumir modificadores de tipo (unsigned, signed, long, short)
        while self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE:
            lex = self.token_actual.lexema
            if lex in ['unsigned', 'signed', 'long', 'short']:
                tokens_del_tipo.append(self._consumir(TT_PALABRA_CLAVE, lex))
            else:
                break
        
        # Consumir el nombre base del tipo y calificadores ::
        if self.token_actual and (self.token_actual.tipo == TT_PALABRA_CLAVE or self.token_actual.tipo == TT_IDENTIFICADOR):
            if self.token_actual.lexema == 'void' and permitir_void_sin_nombre:
                 tokens_del_tipo.append(self._consumir(TT_PALABRA_CLAVE, 'void'))
            elif self.token_actual.lexema != 'void' or not permitir_void_sin_nombre: 
                 tokens_del_tipo.append(self._consumir(self.token_actual.tipo)) # Consume el primer token del tipo base
                 # Bucle para nombres calificados (ej. std::string, MyNamespace::MyClass)
                 while self.token_actual and self.token_actual.tipo == TT_OPERADOR_MIEMBRO and self.token_actual.lexema == '::':
                     tokens_del_tipo.append(self._consumir(TT_OPERADOR_MIEMBRO, '::'))
                     tokens_del_tipo.append(self._consumir(TT_IDENTIFICADOR)) # Espera un IDENTIFICADOR después de ::
            else: # Es 'void' pero no se permite solo (y no es void* o void&)
                if not permitir_void_sin_nombre and self.token_actual.lexema == 'void':
                    es_puntero_o_ref_void = False
                    if self.posicion_actual + 1 < len(self.tokens):
                        siguiente_token = self.tokens[self.posicion_actual + 1] 
                        if (siguiente_token.tipo == TT_OPERADOR_ARITMETICO and siguiente_token.lexema == '*') or \
                           (siguiente_token.tipo == TT_OPERADOR_BITWISE and siguiente_token.lexema == '&'):
                           es_puntero_o_ref_void = True
                    if not es_puntero_o_ref_void: 
                         self._error_sintactico("un tipo de dato válido (void solo es válido como tipo de retorno o puntero/referencia void)")
                    else: 
                         tokens_del_tipo.append(self._consumir(TT_PALABRA_CLAVE, 'void')) # Permitir void si es seguido por * o &
        
        elif not tokens_del_tipo: # Si no se consumió ningún calificador ni tipo base inicial
            self._error_sintactico("un tipo de dato válido")

        # Manejar punteros (*) y referencias (&)
        nivel_puntero = 0
        es_referencia = False
        while self.token_actual and (
              (self.token_actual.tipo == TT_OPERADOR_ARITMETICO and self.token_actual.lexema == '*') or \
              (self.token_actual.tipo == TT_ASTERISCO and self.token_actual.lexema == '*') or # Aceptar TT_ASTERISCO también
              (self.token_actual.tipo == TT_OPERADOR_BITWISE and self.token_actual.lexema == '&') ): 
            if self.token_actual.lexema == '*': 
                self._consumir(self.token_actual.tipo, '*')
                nivel_puntero += 1
            elif self.token_actual.lexema == '&':
                if es_referencia or nivel_puntero > 0: 
                    self._error_sintactico("modificador de tipo inválido después de puntero o referencia")
                self._consumir(TT_OPERADOR_BITWISE, '&'); es_referencia = True
            else: break # No debería llegar aquí si la condición del while es correcta

        # Consumir calificadores const/volatile finales (aplican al puntero/referencia o al tipo si no hay puntero/ref)
        # Esta lógica puede ser más compleja para const int * const;
        # Por ahora, un const/volatile final se asocia con el tipo general.
        if self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE:
            if self.token_actual.lexema == 'const' and not es_const : 
                tokens_del_tipo.append(self._consumir(TT_PALABRA_CLAVE, 'const')); es_const = True 
            elif self.token_actual.lexema == 'volatile' and not es_volatile: 
                tokens_del_tipo.append(self._consumir(TT_PALABRA_CLAVE, 'volatile')); es_volatile = True
        
        return NodoTipoCPP(tokens_del_tipo, es_puntero=nivel_puntero, es_referencia=es_referencia, es_const_qualifier=es_const, es_volatile_qualifier=es_volatile)

    def _parse_tipo_simple_cpp(self, avanzar_tokens=False):
        # Esta función es para "peeking" o consumo real si avanzar_tokens es True.
        # Debe manejar correctamente el estado del parser (self.posicion_actual, self.token_actual)
        # si avanzar_tokens es True, o usar copias temporales si es False.
        
        # Guardar estado actual para restaurar si avanzar_tokens es False
        original_pos = self.posicion_actual
        original_token = self.token_actual
        
        # Usar variables temporales para el "peek" si avanzar_tokens es False
        current_pos = self.posicion_actual
        current_token = self.token_actual

        def _peek_avanzar():
            nonlocal current_pos, current_token
            current_pos += 1
            if current_pos < len(self.tokens):
                current_token = self.tokens[current_pos]
            else:
                current_token = None

        def _actual_avanzar():
            self._avanzar() # Modifica el estado real del parser

        avanzar_func = _actual_avanzar if avanzar_tokens else _peek_avanzar
        get_token_func = lambda: self.token_actual if avanzar_tokens else current_token

        tipo_consumido_lexemas = []
        try:
            # Consumir calificadores opcionales (const, unsigned, etc.)
            while get_token_func() and get_token_func().tipo == TT_PALABRA_CLAVE and \
                  get_token_func().lexema in ['const', 'unsigned', 'signed', 'long', 'short', 'static', 'extern', 'volatile']:
                tipo_consumido_lexemas.append(get_token_func().lexema)
                avanzar_func()
            
            # Consumir el nombre base del tipo
            if get_token_func() and (get_token_func().tipo == TT_PALABRA_CLAVE or get_token_func().tipo == TT_IDENTIFICADOR):
                tipo_consumido_lexemas.append(get_token_func().lexema)
                avanzar_func()
            elif not tipo_consumido_lexemas:
                if not avanzar_tokens: self.posicion_actual = original_pos; self.token_actual = original_token
                return False

            # Consumir :: y otro identificador para tipos calificados
            while get_token_func() and get_token_func().tipo == TT_OPERADOR_MIEMBRO and get_token_func().lexema == '::':
                tipo_consumido_lexemas.append("::")
                avanzar_func() # Consumir ::
                if get_token_func() and get_token_func().tipo == TT_IDENTIFICADOR:
                    tipo_consumido_lexemas.append(get_token_func().lexema)
                    avanzar_func() # Consumir ID
                else: 
                    if not avanzar_tokens: self.posicion_actual = original_pos; self.token_actual = original_token
                    return False # Error de sintaxis en tipo calificado

            # Consumir * o &
            while get_token_func() and get_token_func().lexema in ['*', '&'] and \
                  ( (get_token_func().lexema == '*' and get_token_func().tipo == TT_OPERADOR_ARITMETICO) or \
                    (get_token_func().lexema == '&' and get_token_func().tipo == TT_OPERADOR_BITWISE) ):
                 tipo_consumido_lexemas.append(get_token_func().lexema)
                 avanzar_func()
            
            # print(f"[DEBUG _parse_tipo_simple_cpp] (avanzar={avanzar_tokens}) Consumido: {tipo_consumido_lexemas}, Próximo token para _es_func_probable: {get_token_func()}")
            return True
            
        except Exception: # Cualquier error durante el intento de parseo
            if not avanzar_tokens: self.posicion_actual = original_pos; self.token_actual = original_token
            return False
        finally:
            if not avanzar_tokens: # Siempre restaurar si solo estábamos mirando
                self.posicion_actual = original_pos
                self.token_actual = original_token


    def _parse_lista_parametros_funcion_cpp(self):
        """Parsea la lista de parámetros de una función: (tipo nombre, tipo, ...)."""
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
        """Parsea un bloque de sentencias C++: { sentencias... }."""
        self._consumir(TT_LLAVE_IZQ)
        sentencias = []
        # print(f"[DEBUG CPP Parser] Entrando a _parse_bloque_sentencias_cpp. Token: {self.token_actual}")
        while self.token_actual and self.token_actual.tipo != TT_LLAVE_DER and self.token_actual.tipo != TT_EOF_CPP:
            while self.token_actual and self.token_actual.tipo == TT_PUNTO_Y_COMA: # Consumir ; vacíos
                self._consumir(TT_PUNTO_Y_COMA)
            
            if self.token_actual and self.token_actual.tipo != TT_LLAVE_DER and self.token_actual.tipo != TT_EOF_CPP:
                nodo_sent = self._parse_sentencia_cpp_interna() 
                if nodo_sent:
                    sentencias.append(nodo_sent)
                elif not self.errores_sintacticos and \
                     self.token_actual and self.token_actual.tipo not in [TT_LLAVE_DER, TT_EOF_CPP]:
                     self._error_sintactico("una sentencia válida o '}'")
        
        self._consumir(TT_LLAVE_DER)
        # print(f"[DEBUG CPP Parser] Saliendo de _parse_bloque_sentencias_cpp. Token: {self.token_actual}")
        return NodoBloqueSentenciasCPP(sentencias)
    
    # --- NUEVO MÉTODO DESPACHADOR PARA SENTENCIAS DENTRO DE BLOQUES ---
    def _parse_sentencia_cpp_interna(self):
        """
        Parsea una sentencia dentro de un bloque (ej. cuerpo de función, if, etc.).
        Puede ser una declaración de variable, una sentencia de expresión, return, if, for, while, etc.
        """
        # print(f"[DEBUG CPP Parser] _parse_sentencia_cpp_interna. Token: {self.token_actual}")
        if self.token_actual is None: return None

        # Manejar directivas de preprocesador dentro de bloques
        if self.token_actual.tipo == TT_DIRECTIVA_PREPROCESADOR:
            token_directiva = self._consumir(TT_DIRECTIVA_PREPROCESADOR)
            return NodoDirectivaPreprocesador(token_directiva)

        # Heurística para distinguir declaración de variable de una expresión
        if self._es_potencial_inicio_de_declaracion_o_definicion_tipo():
            # Guardar estado para retroceder si no es una declaración de variable
            # Esta heurística es delicada en C++ debido a la ambigüedad.
            pos_guardada = self.posicion_actual
            token_guardado = self.token_actual
            es_decl_var_probable = False
            try:
                # Intentar parsear un tipo y ver si le sigue un identificador y luego un ; o = o ( o [ o ,
                # Esto es una forma de "lookahead" manual.
                self._parse_tipo_simple_cpp(avanzar_tokens=True) # Avanza self.token_actual temporalmente
                if self.token_actual and self.token_actual.tipo == TT_IDENTIFICADOR:
                    # Guardar estado después del identificador
                    pos_despues_id = self.posicion_actual
                    token_despues_id = self.token_actual
                    self._avanzar() # Avanzar más allá del identificador
                    if self.token_actual and self.token_actual.tipo in [TT_PUNTO_Y_COMA, TT_OPERADOR_ASIGNACION, TT_PARENTESIS_IZQ, TT_CORCHETE_IZQ, TT_COMA]:
                        es_decl_var_probable = True
                    # Restaurar a después del ID para otras comprobaciones si no es decl_var
                    self.posicion_actual = pos_despues_id
                    self.token_actual = token_despues_id
                # Si después del tipo no hay ID, o si después del ID no hay un token esperado para decl_var,
                # podría no ser una declaración de variable (ej. un cast seguido de operador binario).
                # Esta heurística necesita ser robusta.
            except SyntaxError:
                pass # No coincidió con el patrón de tipo o declaración
            finally:
                # Restaurar siempre el estado original del parser después del "lookahead"
                self.posicion_actual = pos_guardada 
                self.token_actual = token_guardado
            
            if es_decl_var_probable:
                return self._parse_declaracion_variable_cpp_local()

        # Si es una palabra clave de sentencia de control o return
        if self.token_actual.tipo == TT_PALABRA_CLAVE:
            lexema = self.token_actual.lexema
            if lexema == 'return':
                return self._parse_sentencia_return_cpp()
            elif lexema == 'if':
                return self._parse_sentencia_if_cpp()
            # (Añadir if, for, while, etc. aquí)
            # else: Si es otra palabra clave, podría ser el inicio de una expresión (ej. sizeof, new)
            #       o un error si no es un inicio de expresión válido.
        
        # Si no es una declaración de variable local ni una sentencia de control conocida,
        # asumimos que es una sentencia de expresión.
        # print(f"[DEBUG CPP Parser] _parse_sentencia_cpp_interna tratando como expresión. Token: {self.token_actual}")
        nodo_expr = self._parse_expresion_cpp() 
        self._consumir(TT_PUNTO_Y_COMA) # Las sentencias de expresión en C++ terminan en ;
        return NodoSentenciaExpresionCPP(nodo_expr)

    def _parse_declaracion_variable_cpp_local(self):
        """Parsea una declaración de variable local: tipo declarador_lista ;"""
        tipo_nodo = self._parse_tipo_cpp()
        declaradores = self._parse_declarador_variable_cpp_lista()
        self._consumir(TT_PUNTO_Y_COMA)
        return NodoDeclaracionVariableCPP(tipo_nodo, declaradores)

    
    def _parse_declarador_variable_cpp_lista(self):
        declaradores = []
        declaradores.append(self._parse_un_declarador_cpp())
        while self.token_actual and self.token_actual.tipo == TT_COMA:
            self._consumir(TT_COMA)
            declaradores.append(self._parse_un_declarador_cpp())
        return declaradores
    
    def _parse_un_declarador_cpp(self):
        es_puntero_decl = 0; es_referencia_decl = False
        while self.token_actual and \
              ((self.token_actual.tipo == TT_OPERADOR_ARITMETICO and self.token_actual.lexema == '*') or \
               (self.token_actual.tipo == TT_OPERADOR_BITWISE and self.token_actual.lexema == '&')):
            if self.token_actual.lexema == '*':
                self._consumir(TT_OPERADOR_ARITMETICO, '*'); es_puntero_decl += 1
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

    #------------SENTENCIAS-----------
    def _parse_sentencia_return_cpp(self):
        self._consumir(TT_PALABRA_CLAVE, 'return')
        expresion_nodo = None
        if self.token_actual and self.token_actual.tipo != TT_PUNTO_Y_COMA:
            expresion_nodo = self._parse_expresion_cpp() 
        self._consumir(TT_PUNTO_Y_COMA)
        return NodoSentenciaReturnCPP(expresion_nodo)
    
    def _parse_sentencia_if_cpp(self):
        """Parsea una sentencia if: if (expresion) sentencia_o_bloque [else sentencia_o_bloque]"""
        self._consumir(TT_PALABRA_CLAVE, 'if')
        self._consumir(TT_PARENTESIS_IZQ)
        condicion_nodo = self._parse_expresion_cpp() # La condición es una expresión
        self._consumir(TT_PARENTESIS_DER)
        
        cuerpo_then_nodo = self._parse_cuerpo_de_control_cpp()

        cuerpo_else_nodo = None
        if self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE and self.token_actual.lexema == 'else':
            self._consumir(TT_PALABRA_CLAVE, 'else')
            cuerpo_else_nodo = self._parse_cuerpo_de_control_cpp()
            
        return NodoSentenciaIfCPP(condicion_nodo, cuerpo_then_nodo, cuerpo_else_nodo)
    
    def _parse_cuerpo_de_control_cpp(self):
        """
        Parsea el cuerpo de una estructura de control (if, else, for, while).
        Puede ser una única sentencia o un bloque de sentencias.
        """
        if self.token_actual and self.token_actual.tipo == TT_LLAVE_IZQ:
            return self._parse_bloque_sentencias_cpp()
        else:
            # Parsea una única sentencia (que podría ser una declaración, expresión, return, etc.)
            # Las sentencias simples en C++ (que no son bloques) deben terminar en ';'
            # El método _parse_sentencia_cpp_interna ya se encarga de consumir el ';'
            # para sentencias de expresión y return, y _parse_declaracion_variable_cpp_local también.
            return self._parse_sentencia_cpp_interna()
    
    # --- Placeholder para el parser de expresiones C++ ---
    def _parse_expresion_cpp(self): 
        return self._parse_expresion_asignacion_cpp()

    def _parse_expresion_asignacion_cpp(self):
        nodo_izq = self._parse_expresion_logica_or_cpp() 
        if self.token_actual and self.token_actual.tipo == TT_OPERADOR_ASIGNACION:
            op_token = self._consumir(TT_OPERADOR_ASIGNACION)
            nodo_der = self._parse_expresion_asignacion_cpp() 
            return NodoExpresionBinariaCPP(op_token, nodo_izq, nodo_der) 
        return nodo_izq

    def _parse_expresion_logica_or_cpp(self):
        nodo = self._parse_expresion_logica_and_cpp()
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR_LOGICO and self.token_actual.lexema == '||':
            op_token = self._consumir(TT_OPERADOR_LOGICO)
            nodo_der = self._parse_expresion_logica_and_cpp()
            nodo = NodoExpresionBinariaCPP(op_token, nodo, nodo_der)
        return nodo

    def _parse_expresion_logica_and_cpp(self):
        nodo = self._parse_expresion_bitwise_or_cpp()
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR_LOGICO and self.token_actual.lexema == '&&':
            op_token = self._consumir(TT_OPERADOR_LOGICO)
            nodo_der = self._parse_expresion_bitwise_or_cpp()
            nodo = NodoExpresionBinariaCPP(op_token, nodo, nodo_der)
        return nodo

    def _parse_expresion_bitwise_or_cpp(self):
        nodo = self._parse_expresion_bitwise_xor_cpp()
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR_BITWISE and self.token_actual.lexema == '|':
            op_token = self._consumir(TT_OPERADOR_BITWISE)
            nodo_der = self._parse_expresion_bitwise_xor_cpp()
            nodo = NodoExpresionBinariaCPP(op_token, nodo, nodo_der)
        return nodo

    def _parse_expresion_bitwise_xor_cpp(self):
        nodo = self._parse_expresion_bitwise_and_cpp()
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR_BITWISE and self.token_actual.lexema == '^':
            op_token = self._consumir(TT_OPERADOR_BITWISE)
            nodo_der = self._parse_expresion_bitwise_and_cpp()
            nodo = NodoExpresionBinariaCPP(op_token, nodo, nodo_der)
        return nodo

    def _parse_expresion_bitwise_and_cpp(self):
        nodo = self._parse_expresion_igualdad_cpp()
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR_BITWISE and self.token_actual.lexema == '&':
            op_token = self._consumir(TT_OPERADOR_BITWISE)
            nodo_der = self._parse_expresion_igualdad_cpp()
            nodo = NodoExpresionBinariaCPP(op_token, nodo, nodo_der)
        return nodo

    def _parse_expresion_igualdad_cpp(self):
        nodo = self._parse_expresion_relacional_cpp()
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR_COMPARACION and \
              self.token_actual.lexema in ['==', '!=']:
            op_token = self._consumir(TT_OPERADOR_COMPARACION)
            nodo_der = self._parse_expresion_relacional_cpp()
            nodo = NodoExpresionBinariaCPP(op_token, nodo, nodo_der)
        return nodo

    def _parse_expresion_relacional_cpp(self):
        nodo = self._parse_expresion_shift_cpp()
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR_COMPARACION and \
              self.token_actual.lexema in ['<', '<=', '>', '>=']:
            op_token = self._consumir(TT_OPERADOR_COMPARACION)
            nodo_der = self._parse_expresion_shift_cpp()
            nodo = NodoExpresionBinariaCPP(op_token, nodo, nodo_der)
        return nodo

    def _parse_expresion_shift_cpp(self): 
        nodo = self._parse_expresion_aditiva_cpp()
        while self.token_actual and \
              self.token_actual.tipo == TT_OPERADOR_BITWISE and \
              self.token_actual.lexema in ['<<', '>>']:
            operador_token = self._consumir(TT_OPERADOR_BITWISE)
            nodo_derecho = self._parse_expresion_aditiva_cpp()
            nodo = NodoExpresionBinariaCPP(operador_token, nodo, nodo_derecho)
        return nodo
        
    def _parse_expresion_aditiva_cpp(self): 
        nodo = self._parse_expresion_multiplicativa_cpp()
        while self.token_actual and \
              self.token_actual.tipo == TT_OPERADOR_ARITMETICO and \
              self.token_actual.lexema in ['+', '-']:
            operador_token = self._consumir(TT_OPERADOR_ARITMETICO)
            nodo_derecho = self._parse_expresion_multiplicativa_cpp()
            nodo = NodoExpresionBinariaCPP(operador_token, nodo, nodo_derecho)
        return nodo

    def _parse_expresion_multiplicativa_cpp(self): 
        nodo = self._parse_expresion_prefijo_unario_cpp() 
        while self.token_actual and \
              self.token_actual.tipo == TT_OPERADOR_ARITMETICO and \
              self.token_actual.lexema in ['*', '/', '%']: # Ahora espera TT_OPERADOR_ARITMETICO para '*'
            
            operador_token = self._consumir(TT_OPERADOR_ARITMETICO) # Consume como TT_OPERADOR_ARITMETICO
           
            nodo_derecho = self._parse_expresion_prefijo_unario_cpp()
            nodo = NodoExpresionBinariaCPP(operador_token, nodo, nodo_derecho)
        return nodo

    def _parse_expresion_prefijo_unario_cpp(self):
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
            # Debería ser: return NodoExpresionUnariaCPP(op_token, operando_nodo, es_prefijo=True)
            # Por ahora, para evitar error si NodoExpresionUnariaCPP no está definido o no se usa.
            return operando_nodo 
        return self._parse_expresion_postfija_cpp()

    def _parse_expresion_postfija_cpp(self): 
        nodo_expr = self._parse_expresion_primaria_cpp()
        while True:
            if self.token_actual and self.token_actual.tipo == TT_PUNTO: # obj.propiedad
                self._consumir(TT_PUNTO)
                propiedad_token = self._consumir(TT_IDENTIFICADOR) 
                nodo_expr = NodoMiembroExpresion(nodo_expr, NodoIdentificadorCPP([propiedad_token]), es_calculado=False) # es_calculado es False para .
            elif self.token_actual and self.token_actual.tipo == TT_OPERADOR_MIEMBRO and self.token_actual.lexema == '->': # ptr->propiedad
                self._consumir(TT_OPERADOR_MIEMBRO, '->')
                propiedad_token = self._consumir(TT_IDENTIFICADOR)
                nodo_expr = NodoMiembroExpresion(nodo_expr, NodoIdentificadorCPP([propiedad_token]), es_arrow=True) # Marcar que es ->
            elif self.token_actual and self.token_actual.tipo == TT_PARENTESIS_IZQ: # func(args)
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
            elif self.token_actual and self.token_actual.tipo == TT_CORCHETE_IZQ: # array[expr]
                self._consumir(TT_CORCHETE_IZQ)
                indice_nodo = self._parse_expresion_cpp() 
                self._consumir(TT_CORCHETE_DER)
                # Para C++, obj[expr] es más como una llamada a operator[] o un acceso a array
                # Usaremos NodoMiembroExpresion con es_calculado=True
                nodo_expr = NodoMiembroExpresion(nodo_expr, indice_nodo, es_calculado=True)
            # (Añadir ++ y -- postfijos aquí si es necesario)
            else:
                break
        return nodo_expr

    def _parse_expresion_primaria_cpp(self):
        if self.token_actual and self.token_actual.tipo == TT_IDENTIFICADOR:
            qname_tokens = [self._consumir(TT_IDENTIFICADOR)]
            while self.token_actual and self.token_actual.tipo == TT_OPERADOR_MIEMBRO and self.token_actual.lexema == '::':
                qname_tokens.append(self._consumir(TT_OPERADOR_MIEMBRO, "::"))
                print(f"[DEBUG PARSER_CPP] Esperando IDENTIFICADOR después de '::'. Token actual: {self.token_actual}")
                if self.posicion_actual > 0 and self.posicion_actual + 1 < len(self.tokens):
                    print(f"[DEBUG PARSER_CPP] Contexto: ...{self.tokens[self.posicion_actual-1]} >>{self.token_actual}<< {self.tokens[self.posicion_actual+1]}...")
                
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
        """Ayudante para consumir tokens hasta encontrar un delimitador o inicio de bloque."""
        # print(f"[DEBUG CPP Parser] Consumiendo hasta {delimitadores}. Token actual: {self.token_actual}")
        profundidad_parentesis = 0
        profundidad_llaves = 0
        profundidad_corchetes = 0

        while self.token_actual and self.token_actual.tipo != TT_EOF_CPP:
            if self.token_actual.tipo == TT_PARENTESIS_IZQ: profundidad_parentesis += 1
            elif self.token_actual.tipo == TT_PARENTESIS_DER: profundidad_parentesis -= 1
            elif self.token_actual.tipo == TT_LLAVE_IZQ: profundidad_llaves += 1
            elif self.token_actual.tipo == TT_LLAVE_DER: profundidad_llaves -= 1
            elif self.token_actual.tipo == TT_CORCHETE_IZQ: profundidad_corchetes += 1
            elif self.token_actual.tipo == TT_CORCHETE_DER: profundidad_corchetes -= 1

            # Detener si estamos en el nivel superior y encontramos un delimitador deseado
            if profundidad_parentesis == 0 and profundidad_llaves == 0 and profundidad_corchetes == 0:
                if self.token_actual.lexema in delimitadores and self.token_actual.tipo in [TT_PUNTO_Y_COMA, TT_LLAVE_IZQ, TT_PARENTESIS_IZQ]:
                    # print(f"[DEBUG CPP Parser] Encontrado delimitador '{self.token_actual.lexema}' en nivel superior.")
                    break 
            
            # print(f"[DEBUG CPP Parser] Saltando token: {self.token_actual}")
            self._avanzar()
            
            # Salvaguarda si los delimitadores no están balanceados y llegamos a EOF
            if self.token_actual is None or self.token_actual.tipo == TT_EOF_CPP:
                break
        # print(f"[DEBUG CPP Parser] Fin de consumir_hasta. Token actual: {self.token_actual}")



    # (Más métodos de parsing para C++ vendrán aquí:
    #  _parse_using_declaracion, _parse_definicion_funcion, _parse_declaracion_variable_cpp,
    #  _parse_tipo_cpp, _parse_sentencia_cpp, _parse_expresion_cpp, etc.)

    def _parse_lista_declaraciones_globales_hasta_llave_der(self):
        """Parsea declaraciones dentro de un namespace hasta '}'."""
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
        """Ayudante para consumir tokens hasta ';' o '{' (para placeholders)."""
        # print(f"[DEBUG CPP Parser] Consumiendo hasta ';' o '{{'. Token actual: {self.token_actual}")
        while self.token_actual and self.token_actual.tipo not in [TT_PUNTO_Y_COMA, TT_LLAVE_IZQ, TT_EOF_CPP]:
            self._avanzar()
        if self.token_actual and self.token_actual.tipo == TT_PUNTO_Y_COMA:
            self._avanzar()
        # print(f"[DEBUG CPP Parser] Fin de consumir_hasta_';'_o_'{'. Token actual: {self.token_actual}")

    def _es_potencial_tipo(self):
        """
        Heurística simple para verificar si el token actual (IDENTIFICADOR) podría ser parte de un tipo.
        Un parser real usaría la tabla de símbolos para verificar typedefs, nombres de clase, etc.
        """
        if self.token_actual and self.token_actual.tipo == TT_IDENTIFICADOR:
            # Podría ser 'std', 'MiClase', etc.
            # Si es seguido por '::' o un nombre de variable o '(', podría ser un tipo.
            if self.posicion_actual + 1 < len(self.tokens):
                siguiente_token = self.tokens[self.posicion_actual + 1]
                if siguiente_token.tipo == TT_OPERADOR_MIEMBRO and siguiente_token.lexema == '::':
                    return True # ej. std::string
                if siguiente_token.tipo == TT_IDENTIFICADOR: # ej. MiClase variable;
                    return True
                if siguiente_token.tipo == TT_PARENTESIS_IZQ: # ej. MiFuncion();
                    return True 
                if siguiente_token.lexema in ['*', '&']: # ej. int *p; int &r;
                    return True
            return True # Asumir que podría ser un tipo simple
        return False
    

# Fin de la clase ParserCPP
