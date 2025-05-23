# src/analizador_sintactico/parser_python.py

# Importar los tipos de token desde nuestro lexer de Python.
try:
    from analizador_lexico.lexer_python import (
        TT_PALABRA_CLAVE, TT_IDENTIFICADOR, TT_ENTERO, TT_FLOTANTE,
        TT_CADENA, TT_OPERADOR, TT_DELIMITADOR, TT_EOF, TT_ERROR_LEXICO,
        TT_INDENT, TT_DEDENT, TT_NUEVA_LINEA 
    )
    from analizador_lexico.lexer_python import Token
except ImportError:
    print("ADVERTENCIA CRÍTICA (ParserPython): No se pudieron importar los tipos de token de LexerPython.")
    # Definir placeholders
    TT_PALABRA_CLAVE, TT_IDENTIFICADOR, TT_EOF = "PALABRA_CLAVE", "IDENTIFICADOR_PYTHON", "EOF_PYTHON" 
    TT_ENTERO, TT_FLOTANTE, TT_CADENA = "ENTERO_PYTHON", "FLOTANTE_PYTHON", "CADENA_PYTHON"
    TT_OPERADOR, TT_DELIMITADOR = "OPERADOR_PYTHON", "DELIMITADOR_PYTHON"
    TT_ERROR_LEXICO = "ERROR_LEXICO_PYTHON"
    TT_INDENT, TT_DEDENT, TT_NUEVA_LINEA = "INDENT", "DEDENT", "NUEVA_LINEA"
    class Token: pass

# --- Definiciones de Nodos del AST para Python ---
class NodoAST_Python:
    """Clase base para todos los nodos del AST de Python."""
    def __repr__(self, indent=0):
        indent_str = "  " * indent
        attrs = {k: v for k, v in self.__dict__.items() if not k.startswith('_') and not isinstance(v, list) and not isinstance(v, NodoAST_Python) and v is not None}
        attr_str_parts = []
        for k,v_item in attrs.items(): 
            if isinstance(v_item, Token): attr_str_parts.append(f"{k}='{v_item.lexema}'")
            elif isinstance(v_item, str): attr_str_parts.append(f"{k}='{v_item}'")
            else: attr_str_parts.append(f"{k}={v_item}")
        attr_str = ", ".join(attr_str_parts)
        
        children_repr_list = []
        for k, v_child in self.__dict__.items(): 
            if isinstance(v_child, NodoAST_Python):
                children_repr_list.append(f"\n{v_child.__repr__(indent + 1)}")
            elif isinstance(v_child, list) and all(isinstance(item, (NodoAST_Python, Token)) for item in v_child): 
                if v_child: 
                    list_items_repr = "\n".join([(item.__repr__(indent + 2) if isinstance(item, NodoAST_Python) else f"{indent_str}  Token({item.tipo},'{item.lexema}')") for item in v_child])
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

class NodoModulo(NodoAST_Python):
    def __init__(self, cuerpo_sentencias):
        self.cuerpo_sentencias = cuerpo_sentencias 

class NodoSentencia(NodoAST_Python): pass
class NodoExpresion(NodoAST_Python): pass

class NodoDefinicionFuncion(NodoSentencia):
    def __init__(self, nombre_funcion_token, parametros_tokens, cuerpo_bloque_nodo):
        self.nombre_funcion_token = nombre_funcion_token
        self.parametros_tokens = parametros_tokens 
        self.cuerpo_bloque_nodo = cuerpo_bloque_nodo 

class NodoBloque(NodoAST_Python): 
    def __init__(self, sentencias):
        self.sentencias = sentencias

class NodoSentenciaExpresion(NodoSentencia):
    def __init__(self, expresion_nodo):
        self.expresion_nodo = expresion_nodo

class NodoAsignacion(NodoSentencia):
    def __init__(self, objetivo_nodo, valor_nodo):
        self.objetivo_nodo = objetivo_nodo 
        self.valor_nodo = valor_nodo     

class NodoSentenciaIf(NodoSentencia):
    def __init__(self, prueba_nodo, cuerpo_then_nodo, cuerpo_else_nodo=None):
        self.prueba_nodo = prueba_nodo
        self.cuerpo_then_nodo = cuerpo_then_nodo
        self.cuerpo_else_nodo = cuerpo_else_nodo 

class NodoSentenciaReturn(NodoSentencia):
    def __init__(self, valor_retorno_nodo=None): 
        self.valor_retorno_nodo = valor_retorno_nodo

class NodoSentenciaWhile(NodoSentencia):
    def __init__(self, condicion_nodo, cuerpo_bloque_nodo):
        self.condicion_nodo = condicion_nodo
        self.cuerpo_bloque_nodo = cuerpo_bloque_nodo

class NodoSentenciaFor(NodoSentencia):
    def __init__(self, variable_iteracion_token, expresion_iterable_nodo, cuerpo_bloque_nodo):
        self.variable_iteracion_token = variable_iteracion_token 
        self.expresion_iterable_nodo = expresion_iterable_nodo 
        self.cuerpo_bloque_nodo = cuerpo_bloque_nodo

# --- NODOS AST PARA BREAK Y CONTINUE ACTUALIZADOS ---
class NodoSentenciaBreak(NodoSentencia):
    """Representa una sentencia 'break'."""
    def __init__(self, token): # Almacena el token 'break'
        self.token = token

class NodoSentenciaContinue(NodoSentencia):
    """Representa una sentencia 'continue'."""
    def __init__(self, token): # Almacena el token 'continue'
        self.token = token
# --- FIN DE NODOS AST ACTUALIZADOS ---

class NodoLlamadaFuncion(NodoExpresion):
    def __init__(self, callee_nodo, argumentos_nodos):
        self.callee_nodo = callee_nodo         
        self.argumentos_nodos = argumentos_nodos 

class NodoIdentificador(NodoExpresion):
    def __init__(self, id_token):
        self.id_token = id_token
        self.nombre = id_token.lexema

class NodoLiteral(NodoExpresion):
    def __init__(self, literal_token):
        self.literal_token = literal_token
        self.valor = literal_token.valor 

class NodoExpresionBinaria(NodoExpresion):
    def __init__(self, izquierda_nodo, operador_token, derecha_nodo):
        self.izquierda_nodo = izquierda_nodo
        self.operador_token = operador_token
        self.derecha_nodo = derecha_nodo
        self.operador = operador_token.lexema

class NodoExpresionUnaria(NodoExpresion): 
    def __init__(self, operador_token, operando_nodo):
        self.operador_token = operador_token
        self.operando_nodo = operando_nodo
        self.operador = operador_token.lexema
# --- Fin de Definiciones de Nodos del AST ---


class ParserPython:
    def __init__(self, tokens):
        self.tokens = tokens 
        self.posicion_actual = 0
        self.token_actual = self.tokens[self.posicion_actual] if self.tokens else None
        self.errores_sintacticos = []

    def _avanzar(self):
        self.posicion_actual += 1
        if self.posicion_actual < len(self.tokens):
            self.token_actual = self.tokens[self.posicion_actual]
        else:
            self.token_actual = self.tokens[-1] if self.tokens and self.tokens[-1].tipo == TT_EOF else None

    def _error_sintactico(self, mensaje_esperado):
        mensaje = "Error Sintáctico Desconocido en Python"
        if self.token_actual and self.token_actual.tipo != TT_EOF:
            mensaje = (f"Error Sintáctico Python en L{self.token_actual.linea}:C{self.token_actual.columna}. "
                       f"Se esperaba {mensaje_esperado}, pero se encontró '{self.token_actual.lexema}' (tipo: {self.token_actual.tipo}).")
        elif self.token_actual and self.token_actual.tipo == TT_EOF:
            mensaje = (f"Error Sintáctico Python: Final inesperado del archivo (L{self.token_actual.linea}:C{self.token_actual.columna}). "
                       f"Se esperaba {mensaje_esperado}.")
        else: 
            last_token_info = self.tokens[self.posicion_actual -1] if self.posicion_actual > 0 and self.posicion_actual <= len(self.tokens) else \
                              (self.tokens[-1] if self.tokens else None)
            linea_aprox = last_token_info.linea if last_token_info else 'desconocida'
            col_aprox = last_token_info.columna if last_token_info else 'desconocida'
            mensaje = (f"Error Sintáctico Python: Final inesperado de la entrada (cerca de L{linea_aprox}:C{col_aprox}). "
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
        ast_modulo_nodo = None
        try:
            cuerpo_sentencias = self._parse_lista_sentencias_nivel_superior()
            ast_modulo_nodo = NodoModulo(cuerpo_sentencias)
            
            while self.token_actual and self.token_actual.tipo in [TT_NUEVA_LINEA, TT_DEDENT]:
                self._avanzar()

            if not self.errores_sintacticos and self.token_actual and self.token_actual.tipo != TT_EOF:
                self._error_sintactico("el final del script (EOF)")
            
            if not self.errores_sintacticos and ast_modulo_nodo:
                 print("Análisis sintáctico de Python y construcción de AST completados exitosamente.")
            
        except SyntaxError:
            ast_modulo_nodo = None 
        except Exception as e:
            print(f"Error inesperado durante el parsing de Python: {e}")
            import traceback
            traceback.print_exc()
            ast_modulo_nodo = None
        
        if self.errores_sintacticos and not ast_modulo_nodo: 
             print(f"Resumen: Parsing de Python falló con {len(self.errores_sintacticos)} error(es) sintáctico(s) detectado(s).")
        
        return ast_modulo_nodo

    def _parse_lista_sentencias_nivel_superior(self):
        sentencias = []
        while self.token_actual and self.token_actual.tipo != TT_EOF:
            if self.token_actual.tipo in [TT_NUEVA_LINEA, TT_INDENT, TT_DEDENT]: 
                self._avanzar()
                continue

            if self.token_actual and self.token_actual.tipo != TT_EOF:
                nodo_sentencia = self._parse_sentencia_python()
                if nodo_sentencia:
                    sentencias.append(nodo_sentencia)
                elif not self.errores_sintacticos and self.token_actual and self.token_actual.tipo != TT_EOF:
                    pass 
        return sentencias

    def _parse_sentencia_python(self):
        if self.token_actual is None or self.token_actual.tipo == TT_EOF:
            return None

        if self.token_actual.tipo == TT_PALABRA_CLAVE: 
            if self.token_actual.lexema == 'def':
                return self._parse_definicion_funcion()
            elif self.token_actual.lexema == 'if':
                return self._parse_sentencia_if() 
            elif self.token_actual.lexema == 'return': 
                return self._parse_sentencia_return()
            elif self.token_actual.lexema == 'while': 
                return self._parse_sentencia_while()
            elif self.token_actual.lexema == 'for':   
                return self._parse_sentencia_for()
            elif self.token_actual.lexema == 'break': 
                return self._parse_sentencia_break()
            elif self.token_actual.lexema == 'continue': 
                return self._parse_sentencia_continue()
            elif self.token_actual.lexema == 'print': 
                 return self._parse_sentencia_print_python2_o_expresion()
            else: 
                print(f"INFO (ParserPython): Parsing de sentencia con palabra clave '{self.token_actual.lexema}' no implementado aún.")
                self._consumir_hasta_nueva_linea_o_eof() 
                return None
        
        elif self.token_actual.tipo == TT_IDENTIFICADOR:
            if self.posicion_actual + 1 < len(self.tokens) and \
               self.tokens[self.posicion_actual + 1].tipo == TT_OPERADOR and \
               self.tokens[self.posicion_actual + 1].lexema == '=':
                return self._parse_sentencia_asignacion()
            else: 
                return self._parse_sentencia_expresion()
        
        elif self.token_actual.tipo == TT_NUEVA_LINEA: 
            self._consumir(TT_NUEVA_LINEA)
            return None 
        
        else: 
            return self._parse_sentencia_expresion()

    def _parse_sentencia_expresion(self):
        nodo_expr = self._parse_expresion_python()
        self._consumir_nueva_linea_o_eof()
        return NodoSentenciaExpresion(nodo_expr)

    def _parse_sentencia_asignacion(self):
        objetivo_token = self._consumir(TT_IDENTIFICADOR)
        objetivo_nodo = NodoIdentificador(objetivo_token)
        self._consumir(TT_OPERADOR, '=')
        valor_nodo = self._parse_expresion_python()
        self._consumir_nueva_linea_o_eof()
        return NodoAsignacion(objetivo_nodo, valor_nodo)

    def _parse_definicion_funcion(self):
        self._consumir(TT_PALABRA_CLAVE, 'def')
        nombre_funcion_token = self._consumir(TT_IDENTIFICADOR)
        self._consumir(TT_DELIMITADOR, '(')
        parametros_tokens = []
        if not (self.token_actual.tipo == TT_DELIMITADOR and self.token_actual.lexema == ')'):
            while True:
                parametros_tokens.append(self._consumir(TT_IDENTIFICADOR))
                if self.token_actual.tipo == TT_DELIMITADOR and self.token_actual.lexema == ',':
                    self._consumir(TT_DELIMITADOR, ',')
                else:
                    break
        self._consumir(TT_DELIMITADOR, ')')
        self._consumir(TT_DELIMITADOR, ':')
        cuerpo_bloque_nodo = self._parse_bloque_python()
        return NodoDefinicionFuncion(nombre_funcion_token, parametros_tokens, cuerpo_bloque_nodo)

    def _parse_sentencia_if(self):
        self._consumir(TT_PALABRA_CLAVE, 'if')
        condicion_if_nodo = self._parse_expresion_python()
        self._consumir(TT_DELIMITADOR, ':')
        cuerpo_if_nodo = self._parse_bloque_python()
        cuerpo_else_actual_nodo = None 
        while self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE and \
              self.token_actual.lexema == 'elif':
            self._consumir(TT_PALABRA_CLAVE, 'elif')
            condicion_elif_nodo = self._parse_expresion_python()
            self._consumir(TT_DELIMITADOR, ':')
            cuerpo_elif_nodo = self._parse_bloque_python()
            nuevo_if_para_elif = NodoSentenciaIf(condicion_elif_nodo, cuerpo_elif_nodo, None)
            if cuerpo_else_actual_nodo is None: 
                cuerpo_else_actual_nodo = nuevo_if_para_elif
            else: 
                temp_nodo_if = cuerpo_else_actual_nodo
                while isinstance(temp_nodo_if.cuerpo_else_nodo, NodoSentenciaIf): 
                    temp_nodo_if = temp_nodo_if.cuerpo_else_nodo
                temp_nodo_if.cuerpo_else_nodo = nuevo_if_para_elif
        if self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE and \
           self.token_actual.lexema == 'else':
            self._consumir(TT_PALABRA_CLAVE, 'else')
            self._consumir(TT_DELIMITADOR, ':')
            bloque_else_final = self._parse_bloque_python()
            if cuerpo_else_actual_nodo is None: 
                cuerpo_else_actual_nodo = bloque_else_final
            else: 
                temp_nodo_if = cuerpo_else_actual_nodo
                while isinstance(temp_nodo_if.cuerpo_else_nodo, NodoSentenciaIf):
                    temp_nodo_if = temp_nodo_if.cuerpo_else_nodo
                temp_nodo_if.cuerpo_else_nodo = bloque_else_final
        return NodoSentenciaIf(condicion_if_nodo, cuerpo_if_nodo, cuerpo_else_actual_nodo)

    def _parse_sentencia_return(self):
        self._consumir(TT_PALABRA_CLAVE, 'return')
        valor_retorno_nodo = None
        if self.token_actual and self.token_actual.tipo not in [TT_NUEVA_LINEA, TT_EOF]:
            valor_retorno_nodo = self._parse_expresion_python()
        self._consumir_nueva_linea_o_eof() 
        return NodoSentenciaReturn(valor_retorno_nodo)

    def _parse_sentencia_while(self):
        self._consumir(TT_PALABRA_CLAVE, 'while')
        condicion_nodo = self._parse_expresion_python()
        self._consumir(TT_DELIMITADOR, ':')
        cuerpo_bloque_nodo = self._parse_bloque_python()
        return NodoSentenciaWhile(condicion_nodo, cuerpo_bloque_nodo)

    def _parse_sentencia_for(self):
        self._consumir(TT_PALABRA_CLAVE, 'for')
        variable_iteracion_token = self._consumir(TT_IDENTIFICADOR)
        self._consumir(TT_PALABRA_CLAVE, 'in') 
        expresion_iterable_nodo = self._parse_expresion_python()
        self._consumir(TT_DELIMITADOR, ':')
        cuerpo_bloque_nodo = self._parse_bloque_python()
        return NodoSentenciaFor(variable_iteracion_token, expresion_iterable_nodo, cuerpo_bloque_nodo)

    # --- MÉTODOS _parse_sentencia_break y _parse_sentencia_continue ACTUALIZADOS ---
    def _parse_sentencia_break(self):
        """Parsea una sentencia 'break'."""
        token_break = self._consumir(TT_PALABRA_CLAVE, 'break')
        self._consumir_nueva_linea_o_eof()
        return NodoSentenciaBreak(token_break) # Pasar el token

    def _parse_sentencia_continue(self):
        """Parsea una sentencia 'continue'."""
        token_continue = self._consumir(TT_PALABRA_CLAVE, 'continue')
        self._consumir_nueva_linea_o_eof()
        return NodoSentenciaContinue(token_continue) # Pasar el token
    # --- FIN DE MÉTODOS ACTUALIZADOS ---

    def _parse_bloque_python(self):
        self._consumir(TT_NUEVA_LINEA)
        self._consumir(TT_INDENT)
        sentencias_bloque = []
        while self.token_actual and self.token_actual.tipo != TT_DEDENT and self.token_actual.tipo != TT_EOF:
            while self.token_actual and self.token_actual.tipo == TT_NUEVA_LINEA: 
                self._avanzar()
            if self.token_actual and self.token_actual.tipo != TT_DEDENT and self.token_actual.tipo != TT_EOF:
                sentencia = self._parse_sentencia_python()
                if sentencia:
                    sentencias_bloque.append(sentencia)
                elif not self.errores_sintacticos and self.token_actual and self.token_actual.tipo != TT_DEDENT:
                    pass
        if self.token_actual and self.token_actual.tipo == TT_DEDENT:
            self._consumir(TT_DEDENT)
        return NodoBloque(sentencias_bloque)

    def _consumir_nueva_linea_o_eof(self):
        if self.token_actual and self.token_actual.tipo == TT_NUEVA_LINEA:
            self._consumir(TT_NUEVA_LINEA)
        elif not self.token_actual or self.token_actual.tipo != TT_EOF:
            if self.token_actual and self.token_actual.tipo != TT_EOF : 
                 self._error_sintactico("una nueva línea o el final del archivo")

    def _consumir_hasta_nueva_linea_o_eof(self):
        while self.token_actual and self.token_actual.tipo not in [TT_NUEVA_LINEA, TT_EOF]:
            self._avanzar()
        if self.token_actual and self.token_actual.tipo == TT_NUEVA_LINEA:
            self._avanzar() 

    def _parse_expresion_python(self):
        return self._parse_expresion_logica_or_python()

    def _parse_expresion_logica_or_python(self):
        nodo = self._parse_expresion_logica_and_python()
        while self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE and self.token_actual.lexema == 'or':
            operador_token = self._consumir(TT_PALABRA_CLAVE, 'or')
            nodo_derecha = self._parse_expresion_logica_and_python()
            nodo = NodoExpresionBinaria(nodo, operador_token, nodo_derecha)
        return nodo

    def _parse_expresion_logica_and_python(self):
        nodo = self._parse_expresion_not_python()
        while self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE and self.token_actual.lexema == 'and':
            operador_token = self._consumir(TT_PALABRA_CLAVE, 'and')
            nodo_derecha = self._parse_expresion_not_python()
            nodo = NodoExpresionBinaria(nodo, operador_token, nodo_derecha)
        return nodo

    def _parse_expresion_not_python(self):
        if self.token_actual and self.token_actual.tipo == TT_PALABRA_CLAVE and self.token_actual.lexema == 'not':
            operador_token = self._consumir(TT_PALABRA_CLAVE, 'not')
            operando_nodo = self._parse_expresion_not_python() 
            return NodoExpresionUnaria(operador_token, operando_nodo)
        return self._parse_expresion_comparativa_python()

    def _parse_expresion_comparativa_python(self):
        nodo = self._parse_expresion_aditiva_python()
        ops_comparacion = ['<', '>', '==', '!=', '<=', '>=', 'in', 'is'] 
        
        while self.token_actual and \
              ((self.token_actual.tipo == TT_OPERADOR and self.token_actual.lexema in ops_comparacion) or \
               (self.token_actual.tipo == TT_PALABRA_CLAVE and self.token_actual.lexema in ['in', 'is'])):
            
            operador_token = self.token_actual
            self._avanzar() 

            if operador_token.lexema == 'not' and self.token_actual and self.token_actual.lexema == 'in':
                operador_token = Token(TT_OPERADOR, "not in", operador_token.linea, operador_token.columna) # Crear un nuevo token combinado
                self._consumir(TT_PALABRA_CLAVE, 'in') 
            elif operador_token.lexema == 'is' and self.token_actual and self.token_actual.lexema == 'not':
                operador_token = Token(TT_OPERADOR, "is not", operador_token.linea, operador_token.columna) # Crear un nuevo token combinado
                self._consumir(TT_PALABRA_CLAVE, 'not') 

            nodo_derecha = self._parse_expresion_aditiva_python()
            nodo = NodoExpresionBinaria(nodo, operador_token, nodo_derecha)
            break 
        return nodo

    def _parse_expresion_aditiva_python(self):
        nodo = self._parse_termino_multiplicativo_python() 
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR and \
              self.token_actual.lexema in ['+', '-']:
            operador_token = self._consumir(TT_OPERADOR)
            nodo_derecha = self._parse_termino_multiplicativo_python()
            nodo = NodoExpresionBinaria(nodo, operador_token, nodo_derecha)
        return nodo

    def _parse_termino_multiplicativo_python(self):
        nodo = self._parse_factor_potencia_python()
        while self.token_actual and self.token_actual.tipo == TT_OPERADOR and \
              self.token_actual.lexema in ['*', '/', '//', '%']:
            operador_token = self._consumir(TT_OPERADOR)
            nodo_derecha = self._parse_factor_potencia_python()
            nodo = NodoExpresionBinaria(nodo, operador_token, nodo_derecha)
        return nodo

    def _parse_factor_potencia_python(self):
        nodo = self._parse_expresion_unaria_python() 
        if self.token_actual and self.token_actual.tipo == TT_OPERADOR and \
           self.token_actual.lexema == '**':
            operador_token = self._consumir(TT_OPERADOR)
            nodo_derecha = self._parse_factor_potencia_python() 
            nodo = NodoExpresionBinaria(nodo, operador_token, nodo_derecha)
        return nodo

    def _parse_expresion_unaria_python(self):
        if self.token_actual and self.token_actual.tipo == TT_OPERADOR and \
           self.token_actual.lexema in ['+', '-', '~']: 
            operador_token = self._consumir(TT_OPERADOR)
            operando_nodo = self._parse_expresion_unaria_python() 
            return NodoExpresionUnaria(operador_token, operando_nodo)
        return self._parse_expresion_primaria_python()

    def _parse_expresion_primaria_python(self):
        token = self.token_actual
        if token is None: self._error_sintactico("una expresión")

        if token.tipo in [TT_ENTERO, TT_FLOTANTE, TT_CADENA]:
            return NodoLiteral(self._consumir(token.tipo))
        elif token.tipo == TT_PALABRA_CLAVE and token.lexema in ['True', 'False', 'None']:
            tk = self._consumir(TT_PALABRA_CLAVE) 
            val = None
            if tk.lexema == 'True': val = True
            elif tk.lexema == 'False': val = False
            return NodoLiteral(Token(tk.tipo, tk.lexema, tk.linea, tk.columna, val)) 
        elif token.tipo == TT_IDENTIFICADOR:
            id_token = self._consumir(TT_IDENTIFICADOR)
            if self.token_actual and self.token_actual.tipo == TT_DELIMITADOR and self.token_actual.lexema == '(':
                return self._parse_llamada_funcion_con_callee(NodoIdentificador(id_token))
            return NodoIdentificador(id_token)
        elif token.tipo == TT_DELIMITADOR and token.lexema == '(':
            self._consumir(TT_DELIMITADOR, '(')
            expr_nodo = self._parse_expresion_python()
            self._consumir(TT_DELIMITADOR, ')')
            return expr_nodo
        else:
            self._error_sintactico(f"una expresión primaria (literal, identificador, '('). Se encontró '{token.lexema}' (tipo: {token.tipo})")
        return None

    def _parse_llamada_funcion_con_callee(self, callee_nodo):
        if self.token_actual.tipo == TT_DELIMITADOR and self.token_actual.lexema == '(':
             self._consumir(TT_DELIMITADOR, '(') 
        
        argumentos_nodos = []
        if not (self.token_actual.tipo == TT_DELIMITADOR and self.token_actual.lexema == ')'):
            while True:
                argumentos_nodos.append(self._parse_expresion_python())
                if self.token_actual.tipo == TT_DELIMITADOR and self.token_actual.lexema == ',':
                    self._consumir(TT_DELIMITADOR, ',')
                else:
                    break
        self._consumir(TT_DELIMITADOR, ')')
        return NodoLlamadaFuncion(callee_nodo, argumentos_nodos)

    def _parse_sentencia_print_python2_o_expresion(self):
        print_token = self._consumir(TT_PALABRA_CLAVE, 'print') 
        
        if self.token_actual and self.token_actual.tipo == TT_DELIMITADOR and self.token_actual.lexema == '(':
            nodo_callee_print = NodoIdentificador(print_token) 
            nodo_llamada = self._parse_llamada_funcion_con_callee(nodo_callee_print)
            self._consumir_nueva_linea_o_eof()
            return NodoSentenciaExpresion(nodo_llamada)
        else:
            self._consumir_hasta_nueva_linea_o_eof()
            return None 
# Fin de la clase ParserPython
