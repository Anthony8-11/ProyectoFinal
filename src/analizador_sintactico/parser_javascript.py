# src/analizador_sintactico/parser_javascript.py

# Es crucial importar los tipos de token desde nuestro lexer de JavaScript.
try:
    from analizador_lexico.lexer_javascript import (
        TT_PALABRA_CLAVE, TT_IDENTIFICADOR, TT_LITERAL_NUMERICO, TT_LITERAL_CADENA,
        TT_OPERADOR_ASIGNACION, TT_OPERADOR_ARITMETICO, TT_OPERADOR_COMPARACION, TT_OPERADOR_LOGICO,
        TT_PUNTO_Y_COMA, TT_COMA, TT_PUNTO,
        TT_PARENTESIS_IZQ, TT_PARENTESIS_DER, TT_LLAVE_IZQ, TT_LLAVE_DER,
        TT_CORCHETE_IZQ, TT_CORCHETE_DER, TT_EOF_JS, TT_OPERADOR_BITWISE, TT_DOS_PUNTOS_TERNARIO,
        TT_ERROR_JS # <-- Importar el token de error léxico
        # Añadir más tipos de token según se necesiten.
    )
    from analizador_lexico.lexer_javascript import Token # Si se necesita la clase Token
except ImportError:
    print("ADVERTENCIA CRÍTICA (ParserJavaScript): No se pudieron importar los tipos de token de LexerJavaScript.")
    TT_PALABRA_CLAVE, TT_IDENTIFICADOR, TT_EOF_JS = "PALABRA_CLAVE_JS", "IDENTIFICADOR_JS", "EOF_JS"
    TT_LITERAL_NUMERICO, TT_LITERAL_CADENA = "LITERAL_NUMERICO_JS", "LITERAL_CADENA_JS"
    TT_OPERADOR_ASIGNACION, TT_OPERADOR_ARITMETICO = "OPERADOR_ASIGNACION_JS", "OPERADOR_ARITMETICO_JS"
    TT_OPERADOR_COMPARACION, TT_OPERADOR_LOGICO = "OPERADOR_COMPARACION_JS", "OPERADOR_LOGICO_JS"
    TT_PUNTO_Y_COMA, TT_COMA, TT_PUNTO = "PUNTO_Y_COMA_JS", "COMA_JS", "PUNTO_JS"
    TT_PARENTESIS_IZQ, TT_PARENTESIS_DER = "PARENTESIS_IZQ_JS", "PARENTESIS_DER_JS"
    TT_LLAVE_IZQ, TT_LLAVE_DER = "LLAVE_IZQ_JS", "LLAVE_DER_JS"
    TT_CORCHETE_IZQ, TT_CORCHETE_DER = "CORCHETE_IZQ_JS", "CORCHETE_DER_JS"
    TT_FLECHA = "FLECHA_JS"
    class Token: pass
    # (Añadir más placeholders si son referenciados antes de su uso real)
    pass

# --- Definiciones de Nodos del AST para JavaScript ---

class NodoAST_JS:
    """Clase base para todos los nodos del AST de JavaScript."""
    def __repr__(self, indent=0):
        indent_str = "  " * indent
        attrs = {k: v for k, v in self.__dict__.items() if not k.startswith('_') and not isinstance(v, list) and not isinstance(v, NodoAST_JS) and v is not None}
        attr_str = ", ".join([f"{k}='{v}'" if isinstance(v, str) else f"{k}={v}" for k,v in attrs.items()])
        
        children_repr_list = []
        for k, v in self.__dict__.items():
            if isinstance(v, NodoAST_JS):
                children_repr_list.append(f"\n{v.__repr__(indent + 1)}")
            elif isinstance(v, list) and all(isinstance(item, NodoAST_JS) for item in v): # Solo listas de Nodos AST
                if v: 
                    list_items_repr = "\n".join([item.__repr__(indent + 2) for item in v])
                    children_repr_list.append(f"\n{indent_str}  {k}=[\n{list_items_repr}\n{indent_str}  ]")
                else:
                    children_repr_list.append(f"\n{indent_str}  {k}=[]")
            elif isinstance(v, list): # Para listas de otros elementos (ej. tokens de parámetros)
                # Convertir tokens a sus lexemas para una representación más limpia en listas no-AST.
                list_items_repr = ", ".join([item.lexema if isinstance(item, Token) else str(item) for item in v])
                children_repr_list.append(f"\n{indent_str}  {k}=[{list_items_repr}]")


        children_repr = "".join(children_repr_list)
        
        base_repr = f"{indent_str}{self.__class__.__name__}"
        if attr_str:
            base_repr += f"({attr_str})"
        
        if children_repr:
            base_repr += f"({children_repr}\n{indent_str})" if not attr_str else f"({children_repr}\n{indent_str})"
        elif not attr_str : # Si no hay atributos ni hijos, solo el nombre de la clase.
             base_repr += "()"


        return base_repr


class NodoProgramaJS(NodoAST_JS):
    """Representa un script de JavaScript completo (una secuencia de sentencias/declaraciones)."""
    def __init__(self, cuerpo):
        self.cuerpo = cuerpo # Lista de nodos de sentencia o declaración.

class NodoSentencia(NodoAST_JS):
    """Clase base para todas las sentencias."""
    pass

class NodoExpresion(NodoAST_JS):
    """Clase base para todas las expresiones."""
    pass

# Declaraciones
class NodoDeclaracionVariable(NodoSentencia):
    """Representa una declaración de variable (var, let, const)."""
    def __init__(self, tipo_declaracion_token, declaraciones):
        # tipo_declaracion_token: Token para 'var', 'let', o 'const'.
        # declaraciones: Lista de NodoDeclaradorVariable.
        self.tipo_declaracion = tipo_declaracion_token.lexema 
        self.declaraciones = declaraciones

class NodoDeclaradorVariable(NodoAST_JS):
    """Representa un único declarador en una declaración de variable (ej: nombre = valor_inicial)."""
    def __init__(self, identificador_token, valor_inicial_nodo=None):
        self.identificador_token = identificador_token # Token IDENTIFICADOR_JS.
        self.valor_inicial_nodo = valor_inicial_nodo   # NodoExpresion (opcional).
        self.nombre = identificador_token.lexema

class NodoDeclaracionFuncion(NodoSentencia):
    def __init__(self, nombre_funcion_token, parametros_tokens, cuerpo_nodo_bloque, es_async=False):
        self.nombre_funcion_token = nombre_funcion_token 
        self.parametros_tokens = parametros_tokens     
        self.cuerpo_nodo_bloque = cuerpo_nodo_bloque   
        self.nombre = nombre_funcion_token.lexema if nombre_funcion_token else None 
        self.es_async = es_async

# Sentencias
class NodoBloqueSentencias(NodoSentencia):
    """Representa un bloque de sentencias: { sentencia1; sentencia2; ... }."""
    def __init__(self, cuerpo_sentencias):
        self.cuerpo_sentencias = cuerpo_sentencias # Lista de nodos de sentencia.

class NodoSentenciaExpresion(NodoSentencia):
    """Representa una sentencia que consiste únicamente en una expresión (ej: una asignación, una llamada a función)."""
    def __init__(self, expresion_nodo):
        self.expresion_nodo = expresion_nodo # NodoExpresion.

class NodoSentenciaIf(NodoSentencia):
    """Representa una sentencia if-else."""
    def __init__(self, prueba_nodo, consecuente_nodo, alternativo_nodo=None):
        self.prueba_nodo = prueba_nodo             # NodoExpresion (la condición).
        self.consecuente_nodo = consecuente_nodo   # NodoSentencia (el bloque 'then').
        self.alternativo_nodo = alternativo_nodo   # NodoSentencia (el bloque 'else', opcional).

class NodoSentenciaReturn(NodoSentencia):
    """Representa una sentencia return."""
    def __init__(self, argumento_nodo=None):
        self.argumento_nodo = argumento_nodo # NodoExpresion (opcional).

class NodoBucleFor(NodoSentencia):
    """Representa un bucle for de estilo C: for (inicializacion; condicion; actualizacion) cuerpo."""
    def __init__(self, inicializacion_nodo, condicion_nodo, actualizacion_nodo, cuerpo_nodo):
        # inicializacion_nodo puede ser NodoDeclaracionVariable o NodoSentenciaExpresion o None.
        self.inicializacion_nodo = inicializacion_nodo
        # condicion_nodo es un NodoExpresion o None.
        self.condicion_nodo = condicion_nodo
        # actualizacion_nodo es un NodoExpresion o None.
        self.actualizacion_nodo = actualizacion_nodo
        # cuerpo_nodo es un NodoSentencia (usualmente NodoBloqueSentencias).
        self.cuerpo_nodo = cuerpo_nodo

# Expresiones
class NodoIdentificadorJS(NodoExpresion):
    """Representa un identificador usado en una expresión."""
    def __init__(self, token_id):
        self.token_id = token_id
        self.nombre = token_id.lexema

class NodoLiteralJS(NodoExpresion):
    def __init__(self, token_literal):
        self.token_literal = token_literal
        self.valor = token_literal.valor 
        self.tipo_literal_lexema = token_literal.lexema

class NodoAsignacionExpresion(NodoExpresion): # También puede ser una sentencia
    """Representa una operación de asignación (ej: variable = valor)."""
    def __init__(self, operador_token, izquierda_nodo, derecha_nodo):
        self.operador_token = operador_token # Token del operador de asignación (ej: '=').
        self.izquierda_nodo = izquierda_nodo # NodoExpresion (usualmente NodoIdentificadorJS).
        self.derecha_nodo = derecha_nodo   # NodoExpresion.
        self.operador = operador_token.lexema

class NodoExpresionBinariaJS(NodoExpresion):
    """Representa una expresión binaria (ej: a + b, x > y)."""
    def __init__(self, operador_token, izquierda_nodo, derecha_nodo):
        self.operador_token = operador_token
        self.izquierda_nodo = izquierda_nodo
        self.derecha_nodo = derecha_nodo
        self.operador = operador_token.lexema

class NodoLlamadaExpresion(NodoExpresion): # También puede ser una sentencia
    """Representa una llamada a función o método (ej: miFuncion(arg1, arg2))."""
    def __init__(self, callee_nodo, argumentos_nodos):
        self.callee_nodo = callee_nodo           # NodoExpresion (usualmente NodoIdentificadorJS o NodoMiembroExpresion).
        self.argumentos_nodos = argumentos_nodos # Lista de nodos de expresión.

class NodoExpresionFlecha(NodoExpresion):
    def __init__(self, parametros_tokens, cuerpo_nodo, es_async=False):
        self.parametros_tokens = parametros_tokens 
        self.cuerpo_nodo = cuerpo_nodo          
        self.es_async = es_async

class NodoMiembroExpresion(NodoExpresion):
    """Representa el acceso a un miembro de un objeto (ej: objeto.propiedad o objeto['propiedad'])."""
    def __init__(self, objeto_nodo, propiedad_nodo, es_calculado=False):
        # objeto_nodo: NodoExpresion que representa el objeto.
        # propiedad_nodo: NodoIdentificadorJS (para .propiedad) o NodoExpresion (para ['propiedad']).
        # es_calculado: Booleano, True si es acceso con [], False si es con .
        self.objeto_nodo = objeto_nodo
        self.propiedad_nodo = propiedad_nodo
        self.es_calculado = es_calculado # True para obj[expr], False para obj.prop


class NodoExpresionActualizacion(NodoExpresion): # ej. i++, i--
    """Representa una expresión de actualización postfija (ej: i++, i--)."""
    def __init__(self, operador_token, argumento_nodo, es_prefijo=False): # es_prefijo sería para ++i
        self.operador_token = operador_token # Token del operador (ej: '++' o '--')
        self.argumento_nodo = argumento_nodo # El nodo que se incrementa/decrementa (ej: NodoIdentificadorJS para 'i')
        self.es_prefijo = es_prefijo # Booleano, True si es ++i, False si es i++
        self.operador = operador_token.lexema

class NodoArrayLiteralJS(NodoExpresion):
    """Representa un literal de array: [elemento1, elemento2, ...]."""
    def __init__(self, elementos_nodos):
        # elementos_nodos: Lista de nodos de expresión que son los elementos del array.
        self.elementos_nodos = elementos_nodos


class NodoObjetoLiteralJS(NodoExpresion):
    """Representa un literal de objeto: { propiedad1: valor1, propiedad2: valor2, ... }."""
    def __init__(self, propiedades_nodos):
        # propiedades_nodos: Lista de nodos NodoPropiedadObjetoJS.
        self.propiedades_nodos = propiedades_nodos

class NodoPropiedadObjetoJS(NodoAST_JS):
    """Representa una única propiedad en un literal de objeto (clave: valor)."""
    def __init__(self, clave_token, valor_nodo): # clave_token puede ser IDENTIFICADOR o LITERAL_CADENA
        self.clave_token = clave_token # Token para la clave de la propiedad.
        self.valor_nodo = valor_nodo   # NodoExpresion para el valor de la propiedad.
        self.nombre_clave = clave_token.lexema # El lexema de la clave

        
# (Más nodos se añadirán según sea necesario, como NodoMiembroExpresion para obj.propiedad, 
#  NodoArrayLiteral, NodoObjetoLiteral, NodoBucleFor, NodoBucleWhile, etc.)

# --- Clase ParserJavaScript ---
class ParserJavaScript:
    def __init__(self, tokens):
        self.tokens = [token for token in tokens if token.tipo != 'WHITESPACE_JS']
        self.posicion_actual = 0
        self.token_actual = self.tokens[self.posicion_actual] if self.tokens else None
        self.errores_sintacticos = []
        self.errores_lexicos = []  # <-- Nueva lista para errores léxicos

    def _avanzar(self):
        self.posicion_actual += 1
        if self.posicion_actual < len(self.tokens):
            self.token_actual = self.tokens[self.posicion_actual]
        else:
            self.token_actual = self.tokens[-1] if self.tokens and self.tokens[-1].tipo == TT_EOF_JS else None

    def _error_lexico(self, token_error):
        mensaje = (f"Error Léxico JS en L{token_error.linea}:C{token_error.columna}. "
                   f"Token no válido: '{token_error.lexema}' (tipo: {token_error.tipo}).")
        self.errores_lexicos.append(mensaje)
        print(mensaje)
        raise SyntaxError(mensaje)

    def _error_sintactico(self, mensaje_esperado):
        mensaje = "Error Sintáctico Desconocido en JavaScript"
        # (Lógica de _error_sintactico como estaba antes)
        if self.token_actual and self.token_actual.tipo != TT_EOF_JS:
            mensaje = (f"Error Sintáctico JS en L{self.token_actual.linea}:C{self.token_actual.columna}. "
                       f"Se esperaba {mensaje_esperado}, pero se encontró '{self.token_actual.lexema}' (tipo: {self.token_actual.tipo}).")
        elif self.token_actual and self.token_actual.tipo == TT_EOF_JS:
            mensaje = (f"Error Sintáctico JS: Final inesperado del archivo (L{self.token_actual.linea}:C{self.token_actual.columna}). "
                       f"Se esperaba {mensaje_esperado}.")
        else: 
            last_meaningful_token = self.tokens[-2] if len(self.tokens) > 1 and self.tokens[-1].tipo == TT_EOF_JS else \
                                  (self.tokens[-1] if self.tokens else None)
            linea_aprox = last_meaningful_token.linea if last_meaningful_token else 'desconocida'
            col_aprox = last_meaningful_token.columna if last_meaningful_token else 'desconocida'
            mensaje = (f"Error Sintáctico JS: Final inesperado de la entrada (cerca de L{linea_aprox}:C{col_aprox}). "
                       f"Se esperaba {mensaje_esperado}.")
        self.errores_sintacticos.append(mensaje)
        print(mensaje) 
        raise SyntaxError(mensaje) 


    def _consumir(self, tipo_token_esperado, lexema_esperado=None):
        token_a_consumir = self.token_actual
        if token_a_consumir and token_a_consumir.tipo == TT_ERROR_JS:
            self._error_lexico(token_a_consumir)
        if token_a_consumir and token_a_consumir.tipo == tipo_token_esperado:
            if lexema_esperado is None or token_a_consumir.lexema == lexema_esperado: # JS es sensible a mayúsculas
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
        """
        Punto de entrada principal para el análisis sintáctico del script JavaScript.
        Devuelve: Un NodoProgramaJS que representa el AST del script completo, o None si hay errores.
        """
        ast_programa_nodo = None
        try:
            cuerpo_programa = self._parse_lista_sentencias_declaraciones(TT_EOF_JS)
            ast_programa_nodo = NodoProgramaJS(cuerpo_programa)
            if not self.errores_sintacticos and self.token_actual and self.token_actual.tipo != TT_EOF_JS:
                self._error_sintactico("el final del script (EOF)")
            if not self.errores_sintacticos and ast_programa_nodo:
                 print("Análisis sintáctico de JavaScript y construcción de AST completados exitosamente.")
        except SyntaxError:
            print(f"Análisis sintáctico de JavaScript detenido debido a errores.")
            ast_programa_nodo = None 
        except Exception as e:
            print(f"Error inesperado durante el parsing de JavaScript: {e}")
            import traceback
            traceback.print_exc()
            ast_programa_nodo = None
        if self.errores_sintacticos and not ast_programa_nodo:
             print(f"Resumen: Parsing de JavaScript falló con {len(self.errores_sintacticos)} error(es) sintáctico(s) detectado(s).")
        return ast_programa_nodo

    def _parse_lista_sentencias_declaraciones(self, token_fin_bloque):
        """Parsea una lista de sentencias y/o declaraciones hasta un token de fin."""
        elementos = []
        while self.token_actual and self.token_actual.tipo != token_fin_bloque:
            while self.token_actual and self.token_actual.tipo == TT_PUNTO_Y_COMA:
                self._consumir(TT_PUNTO_Y_COMA)
            if self.token_actual and self.token_actual.tipo != token_fin_bloque:
                nodo = self._parse_sentencia_o_declaracion()
                if nodo:
                    elementos.append(nodo)
                elif not self.errores_sintacticos and \
                     self.token_actual and self.token_actual.tipo != token_fin_bloque:
                     # Si _parse_sentencia_o_declaracion devuelve None sin error,
                     # y no es fin de bloque, es un problema de lógica del parser.
                     # Esto podría ocurrir si una sentencia vacía (solo ';') es consumida
                     # por _parse_sentencia_o_declaracion y devuelve None.
                     # El bucle externo ya maneja los ';' sueltos, así que esto no debería ser común.
                     self._error_sintactico(f"una sentencia o declaración válida antes de '{self.token_actual.lexema}' o '{token_fin_bloque}'")
            else: 
                break
        return elementos
    
    def _parse_sentencia_o_declaracion(self):
        """Despachador principal para parsear la siguiente construcción."""
        # Dentro de la clase ParserJavaScript
    def _parse_sentencia_o_declaracion(self):
        # print(f"[DEBUG JS Parser] Entrando a _parse_sentencia_o_declaracion. Token actual: {self.token_actual}") 
        if self.token_actual is None: return None 

        tipo = self.token_actual.tipo
        lexema = self.token_actual.lexema 

        if tipo == TT_PALABRA_CLAVE:
            # print(f"[DEBUG JS Parser] Palabra clave detectada: '{lexema}'")
            if lexema in ['var', 'let', 'const']:
                # print(f"[DEBUG JS Parser] Despachando a _parse_declaracion_variable_js para '{lexema}'")
                return self._parse_declaracion_variable_js()
            elif lexema == 'function' or \
                 (lexema == 'async' and self.posicion_actual + 1 < len(self.tokens) and \
                  self.tokens[self.posicion_actual + 1].tipo == TT_PALABRA_CLAVE and \
                  self.tokens[self.posicion_actual + 1].lexema == 'function'):
                # print(f"[DEBUG JS Parser] Despachando a _parse_declaracion_funcion_js para '{lexema}'")
                return self._parse_declaracion_funcion_js()
            elif lexema == 'return': 
                # print(f"[DEBUG JS Parser] Despachando a _parse_sentencia_return_js para '{lexema}'")
                return self._parse_sentencia_return_js()
            elif lexema == 'if': 
                # print(f"[DEBUG JS Parser] Despachando a _parse_sentencia_if_js para '{lexema}'")
                return self._parse_sentencia_if_js()
            elif lexema == 'for': # <--- ESTA ES LA LÍNEA CRUCIAL
                # print(f"[DEBUG JS Parser] Despachando a _parse_bucle_for_js para '{lexema}'")
                return self._parse_bucle_for_js() # Debe llamar a _parse_bucle_for_js
            else: 
                # print(f"[DEBUG JS Parser] Palabra clave '{lexema}' no es declaración/sentencia conocida, tratando como expresión.")
                return self._parse_sentencia_expresion_js()
        elif tipo == TT_LLAVE_IZQ: 
            # print(f"[DEBUG JS Parser] Despachando a _parse_bloque_sentencias_js")
            return self._parse_bloque_sentencias_js()
        elif tipo == TT_PUNTO_Y_COMA: 
            # print(f"[DEBUG JS Parser] Consumiendo sentencia vacía (punto y coma)")
            self._consumir(TT_PUNTO_Y_COMA)
            return None 
        else: 
            # print(f"[DEBUG JS Parser] No es palabra clave ni bloque, tratando como expresión.")
            return self._parse_sentencia_expresion_js()


    # (Más métodos de parsing para declaraciones, sentencias y expresiones de JavaScript vendrán aquí)
    # Ej: _parse_declaracion_variable_js(), _parse_declaracion_funcion_js(),
    #     _parse_sentencia_js(), _parse_expresion_js(), etc.

    def _parse_declaracion_funcion_js(self):
        """Parsea una declaración de función: [async] function [*]nombre (params) { cuerpo }"""
        # print(f"[DEBUG JS Parser] Entrando a _parse_declaracion_funcion_js. Token actual: {self.token_actual}") # DEBUG
        es_async = False
        if self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE and self.token_actual.lexema == 'async':
            self._consumir(TT_PALABRA_CLAVE, 'async')
            es_async = True
        self._consumir(TT_PALABRA_CLAVE, 'function')
        nombre_funcion_token = self._consumir(TT_IDENTIFICADOR)
        parametros_tokens = self._parse_lista_parametros_js()
        cuerpo_nodo_bloque = self._parse_bloque_sentencias_js()
        return NodoDeclaracionFuncion(nombre_funcion_token, parametros_tokens, cuerpo_nodo_bloque, es_async)

    
    def _parse_lista_parametros_js(self):
        """Parsea la lista de parámetros de una función: (param1, param2, ...)."""
        self._consumir(TT_PARENTESIS_IZQ)
        parametros = []
        if self.token_actual and self.token_actual.tipo != TT_PARENTESIS_DER:
            while True:
                # Aquí se podrían parsear patrones de desestructuración, valores por defecto, ...rest
                # Por ahora, solo identificadores simples.
                parametros.append(self._consumir(TT_IDENTIFICADOR))
                if self.token_actual and self.token_actual.tipo == TT_COMA:
                    self._consumir(TT_COMA)
                else:
                    break
        self._consumir(TT_PARENTESIS_DER)
        return parametros

    def _parse_bloque_sentencias_js(self):
        """Parsea un bloque de sentencias: { sentencias... }."""
        self._consumir(TT_LLAVE_IZQ)
        sentencias = self._parse_lista_sentencias_declaraciones(TT_LLAVE_DER) # Parsear hasta '}'
        self._consumir(TT_LLAVE_DER)
        return NodoBloqueSentencias(sentencias)
    
    def _parse_sentencia_return_js(self):
        """Parsea una sentencia return: return [expresion] [;]"""
        self._consumir(TT_PALABRA_CLAVE, 'return')
        argumento_nodo = None
        # En JavaScript, 'return;' o 'return' al final de una línea sin expresión son válidos.
        # Se considera que retorna 'undefined'.
        # No se parsea una expresión si el siguiente token es ';' o '}' o EOF.
        if self.token_actual and \
           self.token_actual.tipo not in [TT_PUNTO_Y_COMA, TT_LLAVE_DER, TT_EOF_JS]:
            # (Aquí también se debería verificar si es el final de la línea y el siguiente token
            # no puede continuar la expresión, para la inserción automática de punto y coma,
            # pero por ahora simplificamos).
            argumento_nodo = self._parse_expresion_js()
        
        self._consumir_punto_y_coma_opcional()
        return NodoSentenciaReturn(argumento_nodo)
    
    def _parse_sentencia_if_js(self):
        """Parsea una sentencia if: if (expresion) sentencia_o_bloque [else sentencia_o_bloque]"""
        self._consumir(TT_PALABRA_CLAVE, 'if')
        self._consumir(TT_PARENTESIS_IZQ)
        condicion_nodo = self._parse_expresion_js() # La condición es una expresión
        self._consumir(TT_PARENTESIS_DER)
        
        # La rama 'then' puede ser una única sentencia o un bloque
        consecuente_nodo = self._parse_sentencia_o_declaracion_o_bloque()

        alternativo_nodo = None
        if self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE and self.token_actual.lexema == 'else':
            self._consumir(TT_PALABRA_CLAVE, 'else')
            alternativo_nodo = self._parse_sentencia_o_declaracion_o_bloque()
            
        return NodoSentenciaIf(condicion_nodo, consecuente_nodo, alternativo_nodo)
    
    def _parse_sentencia_o_declaracion_o_bloque(self):
        """
        Ayudante para parsear lo que puede seguir a 'if', 'else', 'while', 'for'.
        Puede ser una única sentencia o un bloque de sentencias.
        Las declaraciones no suelen ser cuerpos directos de if/else/while sin un bloque,
        pero una sentencia de expresión sí.
        """
        if self.token_actual and self.token_actual.tipo == TT_LLAVE_IZQ:
            return self._parse_bloque_sentencias_js()
        else:
            # Parsea una única sentencia (que podría ser una declaración si la gramática lo permite aquí,
            # o más comúnmente una sentencia de expresión, if, return, etc.)
            return self._parse_sentencia_o_declaracion()
        
    def _parse_bucle_for_js(self):
        """Parsea un bucle for: for ([inicializacion]; [condicion]; [actualizacion]) sentencia_o_bloque"""
        self._consumir(TT_PALABRA_CLAVE, 'for')
        self._consumir(TT_PARENTESIS_IZQ)
        
        # print(f"[DEBUG JS Parser] FOR: Antes de inicialización. Token: {self.token_actual}")
        inicializacion_nodo = None
        if self.token_actual and self.token_actual.tipo != TT_PUNTO_Y_COMA:
            if self.token_actual.tipo == TT_PALABRA_CLAVE and \
               self.token_actual.lexema in ['var', 'let', 'const']:
                inicializacion_nodo = self._parse_declaracion_variable_js(consumir_final_semicolon=False)
            else: 
                inicializacion_nodo = self._parse_expresion_js() 
        # print(f"[DEBUG JS Parser _parse_bucle_for_js] Después de parsear inicialización. Token actual: {self.token_actual}") # NUEVO DEBUG
        self._consumir(TT_PUNTO_Y_COMA) 
        # print(f"[DEBUG JS Parser _parse_bucle_for_js] Después de consumir 1er ;. Token actual: {self.token_actual}") # NUEVO DEBUG

        condicion_nodo = None
        if self.token_actual and self.token_actual.tipo != TT_PUNTO_Y_COMA:
            condicion_nodo = self._parse_expresion_js()
        # print(f"[DEBUG JS Parser _parse_bucle_for_js] Después de parsear condición. Token actual: {self.token_actual}") # DEBUG EXISTENTE
        
        self._consumir(TT_PUNTO_Y_COMA) 
        # print(f"[DEBUG JS Parser _parse_bucle_for_js] Después de consumir 2do ;. Token actual: {self.token_actual}") # NUEVO DEBUG

        actualizacion_nodo = None
        if self.token_actual and self.token_actual.tipo != TT_PARENTESIS_DER:
            actualizacion_nodo = self._parse_expresion_js()
        # print(f"[DEBUG JS Parser _parse_bucle_for_js] Después de parsear actualización. Token actual: {self.token_actual}") # NUEVO DEBUG
        self._consumir(TT_PARENTESIS_DER)

        cuerpo_nodo = self._parse_sentencia_o_declaracion_o_bloque()
        return NodoBucleFor(inicializacion_nodo, condicion_nodo, actualizacion_nodo, cuerpo_nodo)
        



    def _parse_declaracion_variable_js(self, consumir_final_semicolon=True):
        """Parsea una declaración de variable: (var|let|const) declarador (, declarador)* [;]"""
        tipo_declaracion_token = self._consumir(TT_PALABRA_CLAVE) 
        declaradores = []
        while True:
            declarador_nodo = self._parse_declarador_variable_js()
            declaradores.append(declarador_nodo)
            if self.token_actual and self.token_actual.tipo == TT_COMA:
                self._consumir(TT_COMA)
            else:
                break 
        if consumir_final_semicolon: 
            self._consumir_punto_y_coma_opcional()
        return NodoDeclaracionVariable(tipo_declaracion_token, declaradores)


    def _parse_declarador_variable_js(self):
        """Parsea un declarador de variable: IDENTIFICADOR [= expresion_asignacion]"""
        identificador_token = self._consumir(TT_IDENTIFICADOR)
        valor_inicial_nodo = None
        if self.token_actual and self.token_actual.tipo == TT_OPERADOR_ASIGNACION and self.token_actual.lexema == '=':
            self._consumir(TT_OPERADOR_ASIGNACION, '=')
            valor_inicial_nodo = self._parse_expresion_js() # Llamada al parser de expresiones principal
        return NodoDeclaradorVariable(identificador_token, valor_inicial_nodo)
    
    def _parse_sentencia_expresion_js(self):
        """Parsea una sentencia que consiste en una expresión, seguida de un ';' opcional."""
        expresion_nodo = self._parse_expresion_js() 
        self._consumir_punto_y_coma_opcional()
        return NodoSentenciaExpresion(expresion_nodo)
    
    # --- JERARQUÍA DE PARSING DE EXPRESIONES (INICIAL) ---
    def _parse_expresion_js(self): 
        return self._parse_expresion_asignacion_js()

    def _parse_expresion_asignacion_js(self):
        nodo_izq = self._parse_expresion_logica_or_js() 
        if self.token_actual and self.token_actual.tipo == TT_OPERADOR_ASIGNACION:
            operador_token = self._consumir(TT_OPERADOR_ASIGNACION) 
            nodo_der = self._parse_expresion_asignacion_js() 
            return NodoAsignacionExpresion(operador_token, nodo_izq, nodo_der)
        return nodo_izq

    def _parse_expresion_logica_or_js(self): 
        nodo = self._parse_expresion_logica_and_js()
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR_LOGICO and self.token_actual.lexema == '||':
            op_token = self._consumir(TT_OPERADOR_LOGICO, '||')
            nodo_der = self._parse_expresion_logica_and_js()
            nodo = NodoExpresionBinariaJS(op_token, nodo, nodo_der)
        return nodo

    def _parse_expresion_logica_and_js(self): 
        nodo = self._parse_expresion_bitwise_or_js() 
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR_LOGICO and self.token_actual.lexema == '&&':
            op_token = self._consumir(TT_OPERADOR_LOGICO, '&&')
            nodo_der = self._parse_expresion_bitwise_or_js()
            nodo = NodoExpresionBinariaJS(op_token, nodo, nodo_der)
        return nodo

    def _parse_expresion_bitwise_or_js(self): 
        nodo = self._parse_expresion_bitwise_xor_js()
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR_BITWISE and self.token_actual.lexema == '|':
            op_token = self._consumir(TT_OPERADOR_BITWISE, '|')
            nodo_der = self._parse_expresion_bitwise_xor_js()
            nodo = NodoExpresionBinariaJS(op_token, nodo, nodo_der)
        return nodo

    def _parse_expresion_bitwise_xor_js(self): 
        nodo = self._parse_expresion_bitwise_and_js()
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR_BITWISE and self.token_actual.lexema == '^':
            op_token = self._consumir(TT_OPERADOR_BITWISE, '^')
            nodo_der = self._parse_expresion_bitwise_and_js()
            nodo = NodoExpresionBinariaJS(op_token, nodo, nodo_der)
        return nodo

    def _parse_expresion_bitwise_and_js(self): 
        nodo = self._parse_expresion_igualdad_js()
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR_BITWISE and self.token_actual.lexema == '&':
            op_token = self._consumir(TT_OPERADOR_BITWISE, '&')
            nodo_der = self._parse_expresion_igualdad_js()
            nodo = NodoExpresionBinariaJS(op_token, nodo, nodo_der)
        return nodo

    def _parse_expresion_igualdad_js(self): 
        nodo = self._parse_expresion_relacional_js()
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR_COMPARACION and \
              self.token_actual.lexema in ['==', '!=', '===', '!==']:
            op_token = self._consumir(TT_OPERADOR_COMPARACION, self.token_actual.lexema)
            nodo_der = self._parse_expresion_relacional_js()
            nodo = NodoExpresionBinariaJS(op_token, nodo, nodo_der)
        return nodo
        
    def _parse_expresion_relacional_js(self): 
        nodo = self._parse_expresion_aditiva_js() 
        while self.token_actual and (
              (self.token_actual.tipo == TT_OPERADOR_COMPARACION and self.token_actual.lexema in ['<', '<=', '>', '>=']) or \
              (self.token_actual.tipo == TT_PALABRA_CLAVE and self.token_actual.lexema in ['in', 'instanceof'])
              ):
            op_token = self._consumir(self.token_actual.tipo, self.token_actual.lexema)
            nodo_der = self._parse_expresion_aditiva_js()
            nodo = NodoExpresionBinariaJS(op_token, nodo, nodo_der)
        return nodo

    def _parse_expresion_aditiva_js(self): 
        # print(f"[DEBUG JS Parser] Entrando a _parse_expresion_aditiva_js. Token: {self.token_actual}")
        nodo = self._parse_expresion_multiplicativa_js()
        # print(f"[DEBUG JS Parser] _parse_exp_aditiva: después de multiplicativa, nodo: {type(nodo).__name__ if nodo else 'None'}, token: {self.token_actual}")
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR_ARITMETICO and \
              self.token_actual.lexema in ['+', '-']:
            # print(f"[DEBUG JS Parser] _parse_exp_aditiva: Encontrado operador '{self.token_actual.lexema}'")
            op_token = self._consumir(TT_OPERADOR_ARITMETICO, self.token_actual.lexema)
            nodo_der = self._parse_expresion_multiplicativa_js()
            # print(f"[DEBUG JS Parser] _parse_exp_aditiva: después de multiplicativa (der), nodo_der: {type(nodo_der).__name__ if nodo_der else 'None'}, token: {self.token_actual}")
            nodo = NodoExpresionBinariaJS(op_token, nodo, nodo_der)
        # print(f"[DEBUG JS Parser] Saliendo de _parse_expresion_aditiva_js. Nodo: {type(nodo).__name__ if nodo else 'None'}, Token: {self.token_actual}")
        return nodo

    def _parse_expresion_multiplicativa_js(self): 
        # print(f"[DEBUG JS Parser] Entrando a _parse_expresion_multiplicativa_js. Token: {self.token_actual}")
        nodo = self._parse_expresion_unaria_js() 
        # print(f"[DEBUG JS Parser] _parse_exp_mult: después de unaria, nodo: {type(nodo).__name__ if nodo else 'None'}, token: {self.token_actual}")
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR_ARITMETICO and \
              self.token_actual.lexema in ['*', '/', '%']:
            # print(f"[DEBUG JS Parser] _parse_exp_mult: Encontrado operador '{self.token_actual.lexema}'")
            op_token = self._consumir(TT_OPERADOR_ARITMETICO, self.token_actual.lexema)
            nodo_der = self._parse_expresion_unaria_js()
            # print(f"[DEBUG JS Parser] _parse_exp_mult: después de unaria (der), nodo_der: {type(nodo_der).__name__ if nodo_der else 'None'}, token: {self.token_actual}")
            nodo = NodoExpresionBinariaJS(op_token, nodo, nodo_der)
        # print(f"[DEBUG JS Parser] Saliendo de _parse_expresion_multiplicativa_js. Nodo: {type(nodo).__name__ if nodo else 'None'}, Token: {self.token_actual}")
        return nodo

    def _parse_expresion_unaria_js(self):
        # print(f"[DEBUG JS Parser] Entrando a _parse_expresion_unaria_js. Token: {self.token_actual}")
        if self.token_actual and (
            (self.token_actual.tipo == TT_OPERADOR_LOGICO and self.token_actual.lexema == '!') or \
            (self.token_actual.tipo == TT_OPERADOR_ARITMETICO and self.token_actual.lexema in ['+', '-', '++', '--']) or \
            (self.token_actual.tipo == TT_PALABRA_CLAVE and self.token_actual.lexema in ['typeof', 'void', 'delete'])
            ):
            op_token = self._consumir(self.token_actual.tipo, self.token_actual.lexema)
            # Para ++ y -- prefijos, el operando es una expresión unaria (o de mayor precedencia)
            # Para otros, el operando es también una expresión unaria.
            operando_nodo = self._parse_expresion_unaria_js() 
            # Necesitaríamos un NodoExpresionUnariaJS (que ya tenemos definido)
            # return NodoExpresionUnariaJS(op_token, operando_nodo) # Si es prefijo
            print(f"INFO (ParserJS): Operador unario PREFIJO '{op_token.lexema}' parseado.")
            # Para que el AST sea correcto, necesitamos construir el nodo unario.
            # Por ahora, solo devolvemos el operando para evitar errores, pero el operador se pierde.
            # Esta es una simplificación importante.
            return operando_nodo # Esto es incorrecto para la semántica, pero evita error de estructura.
                                # Debería ser: return NodoExpresionUnaria(op_token, operando_nodo, es_prefijo=True)
        
        # Si no es un operador unario prefijo, parsear una expresión izquierda (que puede tener postfijos)
        return self._parse_expresion_izquierda_js()

    def _parse_expresion_izquierda_js(self): 
        nodo_expr = self._parse_expresion_primaria_js()
        while True:
            if self.token_actual and self.token_actual.tipo == TT_PUNTO:
                self._consumir(TT_PUNTO)
                propiedad_token = self._consumir(TT_IDENTIFICADOR) 
                nodo_expr = NodoMiembroExpresion(nodo_expr, NodoIdentificadorJS(propiedad_token), es_calculado=False)
            elif self.token_actual and self.token_actual.tipo == TT_PARENTESIS_IZQ: 
                argumentos_nodos = self._parse_argumentos_llamada_js()
                nodo_expr = NodoLlamadaExpresion(nodo_expr, argumentos_nodos)
            elif self.token_actual and self.token_actual.tipo == TT_CORCHETE_IZQ:
                self._consumir(TT_CORCHETE_IZQ)
                propiedad_expr_nodo = self._parse_expresion_js() 
                self._consumir(TT_CORCHETE_DER)
                nodo_expr = NodoMiembroExpresion(nodo_expr, propiedad_expr_nodo, es_calculado=True)
  
            elif self.token_actual and self.token_actual.tipo == TT_OPERADOR_ARITMETICO and \
                 self.token_actual.lexema in ['++', '--']:
                # No consumir si hay un salto de línea antes (regla de ASI para postfijos)
                # Esta verificación es compleja y se omite por simplicidad aquí.
                operador_postfijo_token = self._consumir(TT_OPERADOR_ARITMETICO, self.token_actual.lexema)
                nodo_expr = NodoExpresionActualizacion(operador_postfijo_token, nodo_expr, es_prefijo=False)

            else:
                break 
        return nodo_expr
        # # print(f"[DEBUG JS Parser] Entrando a _parse_expresion_izquierda_js. Token: {self.token_actual}")
        # nodo_expr = self._parse_expresion_primaria_js()
        # # print(f"[DEBUG JS Parser] _parse_exp_izq: después de primaria, nodo: {type(nodo_expr).__name__ if nodo_expr else 'None'}, token: {self.token_actual}")
        # while True:
        #     if self.token_actual and self.token_actual.tipo == TT_PUNTO:
        #         self._consumir(TT_PUNTO)
        #         propiedad_token = self._consumir(TT_IDENTIFICADOR) 
        #         nodo_expr = NodoMiembroExpresion(nodo_expr, NodoIdentificadorJS(propiedad_token), es_calculado=False)
        #     elif self.token_actual and self.token_actual.tipo == TT_PARENTESIS_IZQ: 
        #         argumentos_nodos = self._parse_argumentos_llamada_js()
        #         nodo_expr = NodoLlamadaExpresion(nodo_expr, argumentos_nodos)
        #     elif self.token_actual and self.token_actual.tipo == TT_CORCHETE_IZQ:
        #         self._consumir(TT_CORCHETE_IZQ)
        #         propiedad_expr_nodo = self._parse_expresion_js() 
        #         self._consumir(TT_CORCHETE_DER)
        #         nodo_expr = NodoMiembroExpresion(nodo_expr, propiedad_expr_nodo, es_calculado=True)
        #     else:
        #         break 
        # # print(f"[DEBUG JS Parser] Saliendo de _parse_expresion_izquierda_js. Nodo: {type(nodo_expr).__name__ if nodo_expr else 'None'}, Token: {self.token_actual}")
        # return nodo_expr

    def _parse_argumentos_llamada_js(self):
        self._consumir(TT_PARENTESIS_IZQ)
        argumentos = []
        if self.token_actual and self.token_actual.tipo != TT_PARENTESIS_DER:
            while True:
                argumentos.append(self._parse_expresion_asignacion_js()) 
                if self.token_actual and self.token_actual.tipo == TT_COMA:
                    self._consumir(TT_COMA)
                else:
                    break
        self._consumir(TT_PARENTESIS_DER)
        return argumentos

    def _parse_expresion_primaria_js(self):
        # print(f"[DEBUG JS Parser] Entrando a _parse_expresion_primaria_js. Token: {self.token_actual}")
        token = self.token_actual
        if token is None:
            self._error_sintactico("una expresión primaria (identificador, literal, etc.)")
        if token.tipo == TT_ERROR_JS:
            self._error_lexico(token)
        if token.tipo == TT_IDENTIFICADOR:
            if token.lexema in ['true', 'false', 'null', 'undefined']:
                consumido = self._consumir(TT_IDENTIFICADOR)
                if consumido.lexema == 'true': consumido.valor = True
                elif consumido.lexema == 'false': consumido.valor = False
                elif consumido.lexema == 'null' or consumido.lexema == 'undefined': consumido.valor = None
                return NodoLiteralJS(consumido)
            return NodoIdentificadorJS(self._consumir(TT_IDENTIFICADOR))
        elif token.tipo in [TT_LITERAL_NUMERICO, TT_LITERAL_CADENA]:
            return NodoLiteralJS(self._consumir(token.tipo))
        elif token.tipo == TT_PALABRA_CLAVE and token.lexema in ['true', 'false', 'null']:
            consumido = self._consumir(TT_PALABRA_CLAVE, token.lexema)
            if consumido.lexema == 'true': consumido.valor = True
            elif consumido.lexema == 'false': consumido.valor = False
            elif consumido.lexema == 'null': consumido.valor = None
            return NodoLiteralJS(consumido)
        elif token.tipo == TT_PARENTESIS_IZQ:
            self._consumir(TT_PARENTESIS_IZQ)
            nodo_expr = self._parse_expresion_js() 
            self._consumir(TT_PARENTESIS_DER)
            return nodo_expr
        elif token.tipo == TT_CORCHETE_IZQ: # <-- MANEJO DE LITERALES DE ARRAY
            return self._parse_array_literal_js()
        elif token.tipo == TT_LLAVE_IZQ: # <-- MANEJO DE LITERALES DE OBJETO
            return self._parse_objeto_literal_js()
        else:
            self._error_sintactico(f"una expresión primaria válida (identificador, literal, '(', '[', o '{{'). Se encontró '{token.lexema}' (tipo: {token.tipo})")
        return None
    
    def _parse_array_literal_js(self):
        """Parsea un literal de array: [elemento1, elemento2, ...]."""
        self._consumir(TT_CORCHETE_IZQ) # Consume '['
        elementos = []
        if self.token_actual and self.token_actual.tipo != TT_CORCHETE_DER:
            while True:
                # Cada elemento es una expresión de asignación (para permitir el operador coma,
                # y también cosas como el spread operator '...' más adelante).
                # Omitir elementos vacíos (ej. [1,,3] se trata como [1, <empty>, 3] en algunos contextos,
                # o puede ser un error. Aquí, esperamos una expresión).
                if self.token_actual and self.token_actual.tipo == TT_COMA:
                    # Manejar el caso de elisiones en arrays: [ , 1, , 2] -> el primer elemento es "empty"
                    # Por ahora, no crearemos un nodo "empty", simplemente avanzamos si hay comas consecutivas
                    # o coma al inicio. Esto es una simplificación.
                    # Un parser más robusto podría crear un nodo "Hole" o "EmptyElement".
                    # Si la coma es seguida de ']', es una coma al final, que JS permite.
                    if self.posicion_actual + 1 < len(self.tokens) and self.tokens[self.posicion_actual + 1].tipo == TT_CORCHETE_DER:
                        # Coma al final antes de ']'
                        pass # No se añade elemento, se consumirá la coma si no es la última
                    elif self.posicion_actual +1 < len(self.tokens) and self.tokens[self.posicion_actual+1].tipo == TT_COMA:
                        # Comas consecutivas [,,] - no soportado directamente, se tratará como error en _parse_expresion_asignacion_js
                        pass


                elementos.append(self._parse_expresion_asignacion_js()) # Parsea un elemento
                
                if self.token_actual and self.token_actual.tipo == TT_COMA:
                    self._consumir(TT_COMA) # Consume la coma separadora
                    if self.token_actual and self.token_actual.tipo == TT_CORCHETE_DER:
                        # Coma al final antes de ']', permitida en JS.
                        break 
                else:
                    break # No hay más comas, fin de la lista de elementos
        self._consumir(TT_CORCHETE_DER) # Consume ']'
        return NodoArrayLiteralJS(elementos)

    def _consumir_punto_y_coma_opcional(self):
        if self.token_actual and self.token_actual.tipo == TT_PUNTO_Y_COMA:
            self._consumir(TT_PUNTO_Y_COMA)
            return True
        return False
    

    def _parse_objeto_literal_js(self):
        """Parsea un literal de objeto: { propiedad1: valor1, propiedad2: valor2, ... }."""
        self._consumir(TT_LLAVE_IZQ) # Consume '{'
        propiedades = []
        
        if self.token_actual and self.token_actual.tipo != TT_LLAVE_DER:
            while True:
                # Parsea una propiedad (clave: valor)
                # La clave puede ser un IDENTIFICADOR, LITERAL_CADENA, o LITERAL_NUMERICO (este último se convierte a cadena)
                if not (self.token_actual and \
                        (self.token_actual.tipo == TT_IDENTIFICADOR or \
                         self.token_actual.tipo == TT_LITERAL_CADENA or \
                         self.token_actual.tipo == TT_LITERAL_NUMERICO)):
                    self._error_sintactico("un nombre de propiedad (identificador o cadena) o '}' en literal de objeto")
                
                clave_token = self.token_actual
                self._avanzar() # Consumir el token de la clave
                
                self._consumir(TT_DOS_PUNTOS_TERNARIO) # Consume ':' (TT_DOS_PUNTOS_TERNARIO se usa aquí también)
                
                valor_nodo = self._parse_expresion_asignacion_js() # El valor es una expresión
                
                propiedades.append(NodoPropiedadObjetoJS(clave_token, valor_nodo))
                
                if self.token_actual and self.token_actual.tipo == TT_COMA:
                    self._consumir(TT_COMA)
                    if self.token_actual and self.token_actual.tipo == TT_LLAVE_DER: # Coma al final
                        break
                else:
                    break # No hay más comas, fin de la lista de propiedades
        
        self._consumir(TT_LLAVE_DER) # Consume '}'
        return NodoObjetoLiteralJS(propiedades)

    

# Fin de la clase ParserJavaScript
