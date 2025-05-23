# src/analizador_sintactico/parser_html.py

# Importar los tipos de token desde nuestro lexer de HTML.
try:
    from analizador_lexico.lexer_html import (
        TT_ETIQUETA_APERTURA, TT_ETIQUETA_CIERRE, TT_TEXTO, TT_ATRIBUTO_NOMBRE,
        TT_ATRIBUTO_VALOR, TT_COMENTARIO_HTML, TT_DOCTYPE, TT_EOF_HTML, TT_ERROR_HTML,
        TT_MENOR_QUE, TT_MAYOR_QUE, TT_SLASH, TT_IGUAL, TT_WHITESPACE,
        TT_SLASH_MAYOR_QUE, TT_IDENTIFICADOR # Asegurar que TT_IDENTIFICADOR también se importe si se usa para nombres de atributos/etiquetas
    )
    from analizador_lexico.lexer_html import Token
except ImportError as e_import_html_parser:
    print(f"ADVERTENCIA CRÍTICA (ParserHTML): No se pudieron importar los tipos de token de LexerHTML. Error: {e_import_html_parser}")
    # Definir placeholders para que el archivo al menos cargue
    TT_ETIQUETA_APERTURA, TT_ETIQUETA_CIERRE, TT_TEXTO = "ETIQUETA_APERTURA", "ETIQUETA_CIERRE", "TEXTO"
    TT_ATRIBUTO_NOMBRE, TT_ATRIBUTO_VALOR = "ATRIBUTO_NOMBRE", "ATRIBUTO_VALOR"
    TT_COMENTARIO_HTML, TT_DOCTYPE, TT_EOF_HTML, TT_ERROR_HTML = "COMENTARIO_HTML", "DOCTYPE", "EOF_HTML", "ERROR_HTML"
    TT_MENOR_QUE, TT_MAYOR_QUE, TT_SLASH, TT_IGUAL = "MENOR_QUE", "MAYOR_QUE", "SLASH", "IGUAL"
    TT_WHITESPACE = "WHITESPACE" 
    TT_SLASH_MAYOR_QUE = "SLASH_MAYOR_QUE"
    TT_IDENTIFICADOR = "IDENTIFICADOR" # Placeholder para nombres de etiqueta/atributo si el lexer los da así
    class Token: pass

# --- Definiciones de Nodos del AST para HTML ---
class NodoAST_HTML:
    """Clase base para todos los nodos del AST de HTML."""
    def __repr__(self, indent=0):
        indent_str = "  " * indent
        attrs = {k: v for k, v in self.__dict__.items() if not k.startswith('_') and not isinstance(v, list) and not isinstance(v, NodoAST_HTML) and v is not None}
        attr_str_parts = []
        for k,v_item in attrs.items(): 
            if isinstance(v_item, Token): attr_str_parts.append(f"{k}='{v_item.lexema}'")
            elif isinstance(v_item, str): attr_str_parts.append(f"{k}='{v_item}'")
            else: attr_str_parts.append(f"{k}={v_item}")
        attr_str = ", ".join(attr_str_parts)
        
        children_repr_list = []
        for k, v_child in self.__dict__.items(): 
            if isinstance(v_child, NodoAST_HTML):
                children_repr_list.append(f"\n{v_child.__repr__(indent + 1)}")
            elif isinstance(v_child, list) and all(isinstance(item, (NodoAST_HTML, Token, str)) for item in v_child): 
                if v_child: 
                    list_items_repr = "\n".join([(item.__repr__(indent + 2) if isinstance(item, NodoAST_HTML) else (f"{indent_str}  Token({item.tipo},'{item.lexema}')" if isinstance(item, Token) else f"{indent_str}  '{item}'" )) for item in v_child])
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

class NodoDocumentoHTML(NodoAST_HTML):
    def __init__(self, hijos):
        self.hijos = hijos 

class NodoEtiquetaHTML(NodoAST_HTML):
    def __init__(self, nombre_etiqueta_str, atributos_lista, hijos_lista, es_autocierre=False):
        self.nombre_etiqueta = nombre_etiqueta_str 
        self.atributos = atributos_lista         
        self.hijos = hijos_lista                 
        self.es_autocierre = es_autocierre       

class NodoAtributoHTML(NodoAST_HTML):
    def __init__(self, nombre_token, valor_token=None): 
        self.nombre_token = nombre_token 
        self.valor_token = valor_token   

class NodoTextoHTML(NodoAST_HTML):
    def __init__(self, texto_token):
        self.texto_token = texto_token 
        self.contenido = texto_token.lexema

class NodoComentarioHTML(NodoAST_HTML):
    def __init__(self, comentario_token):
        self.comentario_token = comentario_token 
        self.contenido = comentario_token.lexema 

class NodoDoctypeHTML(NodoAST_HTML):
    def __init__(self, doctype_token):
        self.doctype_token = doctype_token 
        self.contenido = doctype_token.lexema
# --- Fin de Definiciones de Nodos del AST ---


class ParserHTML:
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
            self.token_actual = self.tokens[-1] if self.tokens and self.tokens[-1].tipo == TT_EOF_HTML else None

    def _error_sintactico(self, mensaje_esperado):
        mensaje = "Error Sintáctico Desconocido en HTML"
        if self.token_actual and self.token_actual.tipo != TT_EOF_HTML:
            mensaje = (f"Error Sintáctico HTML en L{self.token_actual.linea}:C{self.token_actual.columna}. "
                       f"Se esperaba {mensaje_esperado}, pero se encontró '{self.token_actual.lexema.strip()}' (tipo: {self.token_actual.tipo}).")
        elif self.token_actual and self.token_actual.tipo == TT_EOF_HTML:
            mensaje = (f"Error Sintáctico HTML: Final inesperado del archivo (L{self.token_actual.linea}:C{self.token_actual.columna}). "
                       f"Se esperaba {mensaje_esperado}.")
        else: 
            last_token_info = self.tokens[self.posicion_actual -1] if self.posicion_actual > 0 and self.posicion_actual <= len(self.tokens) else \
                              (self.tokens[-1] if self.tokens else None)
            linea_aprox = last_token_info.linea if last_token_info else 'desconocida'
            col_aprox = last_token_info.columna if last_token_info else 'desconocida'
            mensaje = (f"Error Sintáctico HTML: Final inesperado de la entrada (cerca de L{linea_aprox}:C{col_aprox}). "
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
        ast_documento_nodo = None
        try:
            ast_documento_nodo = self._parse_documento()
            while self.token_actual and self.token_actual.tipo == TT_WHITESPACE:
                self._avanzar()
            if not self.errores_sintacticos and self.token_actual and self.token_actual.tipo != TT_EOF_HTML:
                self._error_sintactico("el final del documento HTML (EOF)")
            
            if not self.errores_sintacticos and ast_documento_nodo:
                 print("Análisis sintáctico de HTML y construcción de AST completados exitosamente.")
            
        except SyntaxError:
            ast_documento_nodo = None 
        except Exception as e:
            print(f"Error inesperado durante el parsing de HTML: {e}")
            import traceback
            traceback.print_exc()
            ast_documento_nodo = None
        
        if self.errores_sintacticos and not ast_documento_nodo: 
             print(f"Resumen: Parsing de HTML falló con {len(self.errores_sintacticos)} error(es) sintáctico(s) detectado(s).")
        
        return ast_documento_nodo

    def _parse_documento(self):
        hijos = []
        while self.token_actual and self.token_actual.tipo != TT_EOF_HTML:
            while self.token_actual and self.token_actual.tipo == TT_WHITESPACE:
                self._avanzar()
            
            if self.token_actual and self.token_actual.tipo == TT_EOF_HTML:
                break 

            nodo = self._parse_nodo_html()
            if nodo:
                hijos.append(nodo)
            elif not self.errores_sintacticos and self.token_actual and self.token_actual.tipo != TT_EOF_HTML:
                self._error_sintactico("una etiqueta HTML, texto, comentario o DOCTYPE válido")
                break 
        return NodoDocumentoHTML(hijos)

    # --- MÉTODO _parse_nodo_html ACTUALIZADO ---
    def _parse_nodo_html(self):
        """Despachador para parsear diferentes tipos de nodos HTML."""
        if self.token_actual is None: return None

        if self.token_actual.tipo == TT_DOCTYPE:
            return NodoDoctypeHTML(self._consumir(TT_DOCTYPE))
        elif self.token_actual.tipo == TT_COMENTARIO_HTML:
            return NodoComentarioHTML(self._consumir(TT_COMENTARIO_HTML))
        elif self.token_actual.tipo == TT_ETIQUETA_APERTURA: # Usar el token específico del lexer
            return self._parse_etiqueta_html() 
        elif self.token_actual.tipo == TT_TEXTO:
            return NodoTextoHTML(self._consumir(TT_TEXTO))
        elif self.token_actual.tipo == TT_WHITESPACE: 
            self._avanzar()
            return None 
        else:
            self._error_sintactico(f"inicio de etiqueta (<nombre_etiqueta), texto, comentario o DOCTYPE. Se encontró {self.token_actual.tipo} ('{self.token_actual.lexema.strip()}')")
        return None
    # --- FIN DE MÉTODO ACTUALIZADO ---

    # --- MÉTODO _parse_etiqueta_html ACTUALIZADO ---
    def _parse_etiqueta_html(self):
        token_apertura = self._consumir(TT_ETIQUETA_APERTURA) 
        # El lexema de TT_ETIQUETA_APERTURA es '<nombre_etiqueta'
        nombre_etiqueta_str = token_apertura.lexema[1:].lower() 

        atributos = self._parse_lista_atributos()
        
        hijos = []
        es_autocierre = False
        # Etiquetas void según la especificación HTML5
        etiquetas_void_comunes = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

        if self.token_actual and self.token_actual.tipo == TT_SLASH_MAYOR_QUE: # Para />
            self._consumir(TT_SLASH_MAYOR_QUE) 
            es_autocierre = True
        elif self.token_actual and self.token_actual.tipo == TT_MAYOR_QUE:
            self._consumir(TT_MAYOR_QUE) 
            if nombre_etiqueta_str in etiquetas_void_comunes:
                es_autocierre = True
            else:
                # Parsear contenido y etiqueta de cierre
                hijos = self._parse_contenido_etiqueta(nombre_etiqueta_str)
                # Se espera </nombre_etiqueta>
                # El lexer debería dar un token TT_ETIQUETA_CIERRE (lexema: </nombre>)
                token_cierre = self._consumir(TT_ETIQUETA_CIERRE)
                nombre_cierre_extraido = token_cierre.lexema[2:-1].strip().lower() # Extraer 'nombre' de '</nombre>'
                
                if nombre_cierre_extraido != nombre_etiqueta_str:
                    self._error_sintactico(f"etiqueta de cierre para '{nombre_etiqueta_str}', pero se encontró '</{nombre_cierre_extraido}>'")
        else:
            self._error_sintactico("'>' o '/>' para cerrar la etiqueta de apertura")

        return NodoEtiquetaHTML(nombre_etiqueta_str, atributos, hijos, es_autocierre)
    # --- FIN DE MÉTODO ACTUALIZADO ---

    def _parse_lista_atributos(self):
        atributos = []
        # El lexer da TT_ATRIBUTO_NOMBRE
        while self.token_actual and self.token_actual.tipo == TT_ATRIBUTO_NOMBRE: 
            nombre_attr_token = self._consumir(TT_ATRIBUTO_NOMBRE)
            valor_attr_token = None
            if self.token_actual and self.token_actual.tipo == TT_IGUAL:
                self._consumir(TT_IGUAL)
                if self.token_actual and self.token_actual.tipo == TT_ATRIBUTO_VALOR:
                    valor_attr_token = self._consumir(TT_ATRIBUTO_VALOR)
                else:
                    self._error_sintactico("un valor de atributo entrecomillado después de '='")
            atributos.append(NodoAtributoHTML(nombre_attr_token, valor_attr_token))
        return atributos

    # --- MÉTODO _parse_contenido_etiqueta ACTUALIZADO ---
    def _parse_contenido_etiqueta(self, nombre_etiqueta_padre_lower):
        hijos = []
        while self.token_actual and self.token_actual.tipo != TT_EOF_HTML:
            # Ignorar espacios en blanco y nuevas líneas que son solo formato entre nodos hijos
            while self.token_actual and self.token_actual.tipo == TT_WHITESPACE:
                # print(f"[DEBUG ParserHTML _parse_contenido_etiqueta] Saltando WHITESPACE interno: {repr(self.token_actual.lexema)}")
                self._avanzar()

            if self.token_actual and self.token_actual.tipo == TT_EOF_HTML: break # Salir si solo queda EOF

            # Verificar si es la etiqueta de cierre del padre
            if self.token_actual and self.token_actual.tipo == TT_ETIQUETA_CIERRE:
                # El lexema de TT_ETIQUETA_CIERRE es '</nombre>'
                nombre_cierre_extraido = self.token_actual.lexema[2:-1].strip().lower()
                if nombre_cierre_extraido == nombre_etiqueta_padre_lower:
                    break # Es la etiqueta de cierre del padre, terminar de parsear contenido
            
            nodo_hijo = self._parse_nodo_html() 
            if nodo_hijo:
                hijos.append(nodo_hijo)
            elif not self.errores_sintacticos and self.token_actual and self.token_actual.tipo != TT_EOF_HTML:
                # Si _parse_nodo_html devuelve None (ej. por un whitespace ya consumido) y no es EOF,
                # y no hubo error, continuar. Si es un token inesperado, _parse_nodo_html lanzará error.
                if self.token_actual.tipo != TT_WHITESPACE: # Si no es whitespace, y no se parseó nada, es un problema
                     self._error_sintactico(f"contenido válido para la etiqueta '{nombre_etiqueta_padre_lower}' o la etiqueta de cierre </{nombre_etiqueta_padre_lower}>")
                     break
        return hijos
    # --- FIN DE MÉTODO ACTUALIZADO ---

    def _consumir_hasta_fin_sentencia_o_go(self): 
        pass 

# Fin de la clase ParserHTML
