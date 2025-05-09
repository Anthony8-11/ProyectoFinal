# src/analizador_lexico/lexer_html.py
import re

# Reutilizamos la definición de la clase Token que ya tenemos (o podríamos definirla aquí si fuera diferente)
# Asumiremos que la clase Token de lexer_python.py es accesible o la copiamos/referenciamos.
# Por ahora, para mantener este archivo autocontenido, la redefiniré aquí de forma simplificada.
# En una estructura más grande, Token podría estar en un módulo común.
class Token:
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

# Tipos de Token para HTML
TT_DOCTYPE = 'DOCTYPE'
TT_COMMENT = 'COMMENT'

TT_TAG_OPEN_START_SLASH = 'TAG_OPEN_START_SLASH' # </
TT_TAG_OPEN_START = 'TAG_OPEN_START'         # <
TT_TAG_CLOSE_END_SLASH = 'TAG_CLOSE_END_SLASH' # />
TT_TAG_CLOSE_END = 'TAG_CLOSE_END'           # >

TT_TAG_NAME = 'TAG_NAME'
TT_ATTRIBUTE_NAME = 'ATTRIBUTE_NAME'
TT_EQUALS = 'EQUALS'
TT_ATTRIBUTE_VALUE_QUOTED_DOUBLE = 'ATTRIBUTE_VALUE_QUOTED_DOUBLE'
TT_ATTRIBUTE_VALUE_QUOTED_SINGLE = 'ATTRIBUTE_VALUE_QUOTED_SINGLE'
TT_ATTRIBUTE_VALUE_UNQUOTED = 'ATTRIBUTE_VALUE_UNQUOTED' # Menos común

TT_TEXT_CONTENT = 'TEXT_CONTENT'
TT_WHITESPACE = 'WHITESPACE' # Espacios, tabs, nuevas líneas entre tokens
TT_ERROR_HTML = 'ERROR_HTML'
TT_EOF_HTML = 'EOF_HTML' # Fin de archivo específico para HTML

# Nombres de etiquetas HTML comunes (lista no exhaustiva, solo para referencia o validación simple)
# No los usaremos como "palabras reservadas" de la misma forma que en Python,
# sino que el token TT_TAG_NAME capturará cualquier identificador válido como nombre de etiqueta.
COMMON_HTML_TAGS = {
    'html', 'head', 'title', 'meta', 'link', 'style', 'script', 'body',
    'div', 'p', 'a', 'img', 'span', 'ul', 'ol', 'li', 'table', 'tr', 'td', 'th',
    'form', 'input', 'button', 'select', 'option', 'textarea',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'br', 'hr',
    # etc.
}




# Especificaciones de los tokens para HTML.
# Estas se usarán de manera un poco diferente al lexer de Python.
# El lexer HTML a menudo necesita más lógica contextual que solo aplicar una lista de regex en orden.
# Sin embargo, definirlas ayuda a centralizar los patrones.

# Regex para componentes de etiquetas y contenido:
REGEX_TAG_NAME = r'[a-zA-Z][a-zA-Z0-9_:\-]*' # Nombres de etiqueta y atributo (simplificado)
REGEX_ATTRIBUTE_NAME = r'[a-zA-Z_:][-a-zA-Z0-9_.:]*' # Nombres de atributo un poco más permisivos

# Este es un lexer simple y no manejará scripts/estilos anidados de forma compleja ni CDATA.

class LexerHTML:
    def __init__(self, codigo_fuente):
        self.codigo = codigo_fuente
        self.posicion_actual = 0
        self.linea_actual = 1
        self.columna_actual = 1 # Columna del inicio de la línea actual
        self.columna_en_linea = 1 # Columna dentro de la línea actual

        # Pequeño buffer para el último carácter leído si necesitamos "desleerlo" (pushback)
        # No lo usaremos extensivamente, pero puede ser útil para lógica simple.
        # O mejor, usar _peek() y avanzar con cuidado.
        
        # Modo del lexer (simplificado): 'CONTENT', 'IN_TAG'
        # self.modo = 'CONTENT' # No estrictamente necesario si el bucle principal lo maneja

    def _avanzar(self, cantidad=1):
        """Avanza la posición actual en el código y actualiza línea/columna."""
        for _ in range(cantidad):
            if self.posicion_actual < len(self.codigo):
                caracter = self.codigo[self.posicion_actual]
                if caracter == '\n':
                    self.linea_actual += 1
                    self.columna_actual = 1 # Columna de inicio de la nueva línea
                    self.columna_en_linea = 1
                else:
                    self.columna_en_linea += 1
                self.posicion_actual += 1
            else:
                break

    def _caracter_actual(self):
        """Devuelve el carácter en la posición actual o None si es EOF."""
        if self.posicion_actual < len(self.codigo):
            return self.codigo[self.posicion_actual]
        return None

    def _peek(self, cantidad=1):
        """Devuelve los siguientes 'cantidad' caracteres sin avanzar."""
        if self.posicion_actual + cantidad <= len(self.codigo):
            return self.codigo[self.posicion_actual : self.posicion_actual + cantidad]
        # Si la cantidad solicitada excede el final, devuelve lo que queda
        elif self.posicion_actual < len(self.codigo):
            return self.codigo[self.posicion_actual:]
        return None

    def _crear_token(self, tipo, lexema, valor=None):
        # La columna para el token es la columna donde comenzó el lexema.
        # Esto requiere rastrear la columna de inicio del lexema actual.
        # Por ahora, usaremos self.columna_en_linea - len(lexema) como aproximación,
        # pero es mejor pasar la columna de inicio explícitamente.
        # Vamos a asumir que la columna_actual se refiere al inicio del token que estamos formando.
        # Mejor: guardar columna_inicio_token antes de consumir el lexema.
        
        # Columna se calculará antes de llamar a _crear_token
        col_inicio = self.columna_en_linea - len(lexema) +1 # Asumiendo que columna_en_linea es el final + 1
        # Esto es un poco impreciso. Se corregirá en la lógica de tokenización.
        # La idea es capturar la línea y columna ANTES de empezar a consumir el lexema.
        return Token(tipo, lexema, self.linea_actual, self.columna_actual, valor)

    # Los métodos para tokenizar el contenido HTML vendrán aquí.

    def _obtener_token_elemental(self):
        """
        Intenta obtener la siguiente unidad léxica más obvia.
        Este método es llamado por tokenizar() que maneja el contexto.
        """
        if self.posicion_actual >= len(self.codigo):
            return Token(TT_EOF_HTML, "EOF_HTML", self.linea_actual, self.columna_en_linea)

        # Guardar posición de inicio para el token actual
        linea_inicio = self.linea_actual
        col_inicio = self.columna_en_linea
        char_actual = self.codigo[self.posicion_actual]

        # 1. Comentarios y DOCTYPE (manejo completo aquí porque son unidades grandes y claras)
        if char_actual == '<' and self._peek(4) == '<!--':
            lexema = '<!--'; self._avanzar(4); contenido = ""
            while self.posicion_actual < len(self.codigo) and self._peek(3) != '-->':
                contenido += self._caracter_actual(); lexema += self._caracter_actual(); self._avanzar()
            if self._peek(3) == '-->':
                lexema += '-->'; self._avanzar(3)
                return Token(TT_COMMENT, lexema, linea_inicio, col_inicio, valor=contenido)
            return Token(TT_ERROR_HTML, "Comentario HTML sin cerrar", linea_inicio, col_inicio)
        
        if char_actual == '<' and self._peek(9).upper() == '<!DOCTYPE':
            lexema = ''; valor_interno = ''
            # Consumir '<!DOCTYPE'
            temp_lex = self._peek(9); self._avanzar(9); lexema += temp_lex
            # Consumir el resto hasta '>'
            while self.posicion_actual < len(self.codigo) and self.codigo[self.posicion_actual] != '>':
                char_loop = self.codigo[self.posicion_actual]
                lexema += char_loop
                if len(lexema) > 9: valor_interno += char_loop # Acumular valor después de <!DOCTYPE
                self._avanzar()
            if self._caracter_actual() == '>':
                lexema += '>'; self._avanzar()
                return Token(TT_DOCTYPE, lexema, linea_inicio, col_inicio, valor=valor_interno.strip())
            return Token(TT_ERROR_HTML, "DOCTYPE HTML sin cerrar", linea_inicio, col_inicio)

        # 2. Caracteres de control de etiquetas
        if char_actual == '<':
            if self._peek(2) == '</': self._avanzar(2); return Token(TT_TAG_OPEN_START_SLASH, '</', linea_inicio, col_inicio)
            self._avanzar(); return Token(TT_TAG_OPEN_START, '<', linea_inicio, col_inicio)
        if char_actual == '>': self._avanzar(); return Token(TT_TAG_CLOSE_END, '>', linea_inicio, col_inicio)
        if char_actual == '/' and self._peek(2) == '/>': self._avanzar(2); return Token(TT_TAG_CLOSE_END_SLASH, '/>', linea_inicio, col_inicio)
        if char_actual == '=': self._avanzar(); return Token(TT_EQUALS, '=', linea_inicio, col_inicio)

        # 3. Nombres de etiquetas o atributos (simplificado: cualquier secuencia alfanumérica con guiones)
        # El contexto (si es un nombre de tag o de atributo) lo determinará el parser o el bucle de tokenizar.
        match_name = re.match(REGEX_TAG_NAME, self.codigo[self.posicion_actual:]) # Usamos REGEX_TAG_NAME genéricamente
        if match_name:
            lexema = match_name.group(0); self._avanzar(len(lexema))
            # No podemos saber si es TAG_NAME o ATTRIBUTE_NAME solo con el lexer elemental,
            # el tokenizador principal le dará el tipo correcto según el contexto.
            # Por ahora, lo dejaremos como un tipo genérico o lo manejamos en tokenizar().
            # Vamos a devolverlo como un "POSIBLE_NOMBRE" y tokenizar decide.
            return Token("POSIBLE_NOMBRE", lexema, linea_inicio, col_inicio)

        # 4. Valores de atributo entre comillas
        if char_actual == '"':
            lexema_val = '"'; self._avanzar(); valor_interno = ""
            while self._caracter_actual() is not None and self._caracter_actual() != '"':
                # Simplificado: no maneja escapes complejos dentro del valor.
                valor_interno += self._caracter_actual(); lexema_val += self._caracter_actual(); self._avanzar()
            if self._caracter_actual() == '"': lexema_val += '"'; self._avanzar()
            else: return Token(TT_ERROR_HTML, "Valor de atributo (\") sin cerrar", linea_inicio, col_inicio)
            return Token(TT_ATTRIBUTE_VALUE_QUOTED_DOUBLE, lexema_val, linea_inicio, col_inicio, valor=valor_interno)

        if char_actual == "'":
            lexema_val = "'"; self._avanzar(); valor_interno = ""
            while self._caracter_actual() is not None and self._caracter_actual() != "'":
                valor_interno += self._caracter_actual(); lexema_val += self._caracter_actual(); self._avanzar()
            if self._caracter_actual() == "'": lexema_val += "'"; self._avanzar()
            else: return Token(TT_ERROR_HTML, "Valor de atributo (') sin cerrar", linea_inicio, col_inicio)
            return Token(TT_ATTRIBUTE_VALUE_QUOTED_SINGLE, lexema_val, linea_inicio, col_inicio, valor=valor_interno)
        
        # 5. Espacios en blanco
        if char_actual.isspace():
            lexema_ws = ""; 
            while self._caracter_actual() and self._caracter_actual().isspace():
                lexema_ws += self._caracter_actual(); self._avanzar()
            return Token(TT_WHITESPACE, lexema_ws, linea_inicio, col_inicio)

        # 6. Contenido de texto (lo que queda hasta el próximo '<' o espacio o fin)
        # El TEXT_CONTENT se manejará mejor en el bucle `tokenizar` cuando no se esté dentro de una etiqueta.
        # Aquí, si no es nada de lo anterior, podría ser parte de un valor de atributo sin comillas
        # o un error. Un valor sin comillas es lo más difícil de lexear correctamente sin contexto.

        # Por ahora, cualquier otra cosa hasta un delimitador o espacio.
        # Esta es la parte más débil y necesitará un bucle `tokenizar` más inteligente.
        lexema_otro = ""
        while (self._caracter_actual() and 
               not self._caracter_actual().isspace() and 
               self._caracter_actual() not in ['<', '>', '=', '/', '"', "'"]):
            lexema_otro += self._caracter_actual()
            self._avanzar()
        
        if lexema_otro: # Podría ser un valor de atributo sin comillas o texto
            # Dejamos que tokenizar() decida basado en el contexto.
            return Token("TEXTO_O_VALOR_SIN_COMILLAS", lexema_otro, linea_inicio, col_inicio)

        # Error si aún queda algo y no se consumió
        if self._caracter_actual():
            char_err = self._caracter_actual(); self._avanzar()
            return Token(TT_ERROR_HTML, f"Carácter no reconocido: '{char_err}'", linea_inicio, col_inicio)

        return Token(TT_EOF_HTML, "EOF_HTML", self.linea_actual, self.columna_en_linea) # Debería ser redundante



    def tokenizar(self):
        tokens = []
        # El estado nos dirá si estamos esperando contenido, dentro de una etiqueta, etc.
        # Estados: 'CONTENT', 'AFTER_LT', 'AFTER_LT_SLASH', 'IN_TAG_AFTER_NAME', 'AFTER_ATTR_NAME', 'AFTER_ATTR_EQUALS'
        estado = 'CONTENT' 
        
        while self.posicion_actual < len(self.codigo):
            linea_inicio_iter = self.linea_actual
            col_inicio_iter = self.columna_en_linea
            
            char_actual = self.codigo[self.posicion_actual]

            if estado == 'CONTENT':
                if char_actual == '<':
                    # Podría ser comentario, doctype, etiqueta de apertura o cierre
                    if self._peek(4) == '<!--':
                        token = self._obtener_token_elemental() # Debería consumir todo el comentario
                        tokens.append(token)
                        if token.tipo == TT_ERROR_HTML: break
                        continue
                    elif self._peek(9).upper() == '<!DOCTYPE':
                        token = self._obtener_token_elemental() # Debería consumir todo el doctype
                        tokens.append(token)
                        if token.tipo == TT_ERROR_HTML: break
                        continue
                    elif self._peek(2) == '</':
                        tokens.append(Token(TT_TAG_OPEN_START_SLASH, '</', linea_inicio_iter, col_inicio_iter))
                        self._avanzar(2)
                        estado = 'AFTER_LT_SLASH'
                        continue
                    else: # solo '<'
                        tokens.append(Token(TT_TAG_OPEN_START, '<', linea_inicio_iter, col_inicio_iter))
                        self._avanzar()
                        estado = 'AFTER_LT'
                        continue
                else: # Es texto o espacio en blanco
                    lexema_texto = ""
                    linea_texto_inicio = self.linea_actual
                    col_texto_inicio = self.columna_en_linea
                    while self.posicion_actual < len(self.codigo) and self.codigo[self.posicion_actual] != '<':
                        lexema_texto += self.codigo[self.posicion_actual]
                        self._avanzar()
                    
                    # El texto puede contener solo espacios, o texto y espacios.
                    # Dividir en tokens de texto y tokens de espacio si es necesario,
                    # o simplemente un token de texto que puede incluir espacios.
                    # Por simplicidad, si lexema_texto no es solo espacio, es TEXT_CONTENT.
                    # Si es solo espacio, es WHITESPACE.
                    if lexema_texto.strip(): # Si hay algo más que espacios
                        # Se podrían refinar para separar texto y whitespace intermedio.
                        tokens.append(Token(TT_TEXT_CONTENT, lexema_texto, linea_texto_inicio, col_texto_inicio, valor=lexema_texto))
                    elif lexema_texto: # Solo espacios
                        tokens.append(Token(TT_WHITESPACE, lexema_texto, linea_texto_inicio, col_texto_inicio))
                    continue
            
            elif estado == 'AFTER_LT' or estado == 'AFTER_LT_SLASH': # Esperando TAG_NAME
                if char_actual.isspace(): # Omitir espacios antes del nombre del tag
                    self._avanzar(); continue 
                
                match_tag_name = re.match(REGEX_TAG_NAME, self.codigo[self.posicion_actual:])
                if match_tag_name:
                    lexema_tn = match_tag_name.group(0)
                    tokens.append(Token(TT_TAG_NAME, lexema_tn, linea_inicio_iter, self.columna_en_linea))
                    self._avanzar(len(lexema_tn))
                    estado = 'IN_TAG_AFTER_NAME'
                    continue
                else:
                    tokens.append(Token(TT_ERROR_HTML, "Se esperaba nombre de etiqueta", linea_inicio_iter, self.columna_en_linea))
                    break
            
            elif estado == 'IN_TAG_AFTER_NAME': # Esperando atributo, '>', o '/>'
                if char_actual.isspace(): # Espacios entre atributos o antes de >
                    self._avanzar(); continue # Omitir por ahora, o tokenizar como WHITESPACE_IN_TAG
                
                if char_actual == '>':
                    tokens.append(Token(TT_TAG_CLOSE_END, '>', linea_inicio_iter, self.columna_en_linea))
                    self._avanzar()
                    estado = 'CONTENT'
                    continue
                elif self._peek(2) == '/>':
                    tokens.append(Token(TT_TAG_CLOSE_END_SLASH, '/>', linea_inicio_iter, self.columna_en_linea))
                    self._avanzar(2)
                    estado = 'CONTENT'
                    continue
                
                # Debe ser un nombre de atributo
                match_attr_name = re.match(REGEX_ATTRIBUTE_NAME, self.codigo[self.posicion_actual:])
                if match_attr_name:
                    lexema_an = match_attr_name.group(0)
                    tokens.append(Token(TT_ATTRIBUTE_NAME, lexema_an, linea_inicio_iter, self.columna_en_linea))
                    self._avanzar(len(lexema_an))
                    estado = 'AFTER_ATTR_NAME'
                    continue
                else:
                    tokens.append(Token(TT_ERROR_HTML, "Se esperaba atributo, '>' o '/>'", linea_inicio_iter, self.columna_en_linea))
                    break
            
            elif estado == 'AFTER_ATTR_NAME': # Esperando '=', espacio, otro atributo, '>', o '/>'
                if char_actual.isspace(): self._avanzar(); continue
                
                if char_actual == '=':
                    tokens.append(Token(TT_EQUALS, '=', linea_inicio_iter, self.columna_en_linea))
                    self._avanzar()
                    estado = 'AFTER_ATTR_EQUALS'
                    continue
                # Si no es '=', el atributo es booleano o es el siguiente atributo, o cierre de tag
                # Esta parte se simplifica, asumiendo que después de un nombre de atributo
                # o viene un '=', o es un atributo booleano y sigue otro atributo o cierre.
                # Volvemos a IN_TAG_AFTER_NAME para buscar otro atributo o cierre.
                estado = 'IN_TAG_AFTER_NAME' 
                # No consumimos el carácter, dejamos que IN_TAG_AFTER_NAME lo reevalúe.
                continue


            elif estado == 'AFTER_ATTR_EQUALS': # Esperando valor de atributo
                if char_actual.isspace(): self._avanzar(); continue

                valor_token = None
                if char_actual == '"':
                    lexema_val = '"'; self._avanzar(); valor_interno = ""
                    while self._caracter_actual() is not None and self._caracter_actual() != '"':
                        valor_interno += self._caracter_actual(); lexema_val += self._caracter_actual(); self._avanzar()
                    if self._caracter_actual() == '"': lexema_val += '"'; self._avanzar()
                    else: tokens.append(Token(TT_ERROR_HTML, "Valor (\") sin cerrar", linea_inicio_iter, col_inicio_iter)); break
                    valor_token = Token(TT_ATTRIBUTE_VALUE_QUOTED_DOUBLE, lexema_val, linea_inicio_iter, col_inicio_iter, valor=valor_interno)
                
                elif char_actual == "'":
                    lexema_val = "'"; self._avanzar(); valor_interno = ""
                    while self._caracter_actual() is not None and self._caracter_actual() != "'":
                        valor_interno += self._caracter_actual(); lexema_val += self._caracter_actual(); self._avanzar()
                    if self._caracter_actual() == "'": lexema_val += "'"; self._avanzar()
                    else: tokens.append(Token(TT_ERROR_HTML, "Valor (') sin cerrar", linea_inicio_iter, col_inicio_iter)); break
                    valor_token = Token(TT_ATTRIBUTE_VALUE_QUOTED_SINGLE, lexema_val, linea_inicio_iter, col_inicio_iter, valor=valor_interno)
                
                else: # Valor sin comillas
                    lexema_unq = ""
                    # Los valores sin comillas no pueden tener espacios, ', ", =, <, >, `
                    # Y deben ser seguidos por un espacio o > o />
                    while (self.posicion_actual < len(self.codigo) and 
                           not self.codigo[self.posicion_actual].isspace() and
                           self.codigo[self.posicion_actual] not in ['>', '/']): # Simplificado
                        lexema_unq += self.codigo[self.posicion_actual]
                        self._avanzar()
                    if lexema_unq:
                        valor_token = Token(TT_ATTRIBUTE_VALUE_UNQUOTED, lexema_unq, linea_inicio_iter, col_inicio_iter)
                    else:
                        tokens.append(Token(TT_ERROR_HTML, "Se esperaba valor de atributo", linea_inicio_iter, col_inicio_iter)); break
                
                if valor_token: tokens.append(valor_token)
                estado = 'IN_TAG_AFTER_NAME' # Volver a buscar más atributos o cierre
                continue
            
            else: # Estado desconocido o error de lógica
                tokens.append(Token(TT_ERROR_HTML, f"Estado desconocido del lexer: {estado}", self.linea_actual, self.columna_en_linea))
                self._avanzar() # Avanzar para evitar bucle infinito
                break


        tokens.append(Token(TT_EOF_HTML, "EOF_HTML", self.linea_actual, self.columna_en_linea))
        return tokens

# Fin de la clase LexerHTML