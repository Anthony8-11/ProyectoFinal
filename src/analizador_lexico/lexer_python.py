# src/analizador_lexico/lexer_python.py
import re

# Podríamos definir una clase Token o usar diccionarios. Una clase es más estructurada.
class Token:
    def __init__(self, tipo, lexema, linea, columna, valor=None):
        self.tipo = tipo          # Tipo de token (ej: IDENTIFICADOR, NUMERO_ENTERO)
        self.lexema = lexema      # El texto actual del token (ej: "mi_variable", "123")
        self.linea = linea        # Número de línea donde aparece el token
        self.columna = columna    # Número de columna donde comienza el token
        self.valor = valor if valor is not None else lexema # Valor real (ej: 123 para "123")

    def __repr__(self):
        # Representación útil para depuración
        return f"Token({self.tipo}, '{self.lexema}', L{self.linea}:C{self.columna}" + \
               (f", V:{self.valor}" if self.valor != self.lexema else "") + ")"

# Definición de los tipos de token (los usaremos como constantes)
# Palabras reservadas (se tratarán de forma especial)
PALABRAS_RESERVADAS = {
    'and', 'as', 'assert', 'async', 'await', 'break', 'class', 'continue', 'def',
    'del', 'elif', 'else', 'except', 'False', 'finally', 'for', 'from',
    'global', 'if', 'import', 'in', 'is', 'lambda', 'None', 'nonlocal',
    'not', 'or', 'pass', 'raise', 'return', 'True', 'try', 'while', 'with', 'yield'
    # 'print' no es palabra reservada en Python 3, es una función, pero la podemos tratar como tal si queremos
}

# Tipos de token que nuestro lexer reconocerá
TT_IDENTIFICADOR = 'IDENTIFICADOR'
TT_PALABRA_RESERVADA = 'PALABRA_RESERVADA'

TT_OPERADOR = 'OPERADOR'
TT_DELIMITADOR = 'DELIMITADOR'

TT_NUMERO_ENTERO = 'NUMERO_ENTERO'
TT_NUMERO_FLOTANTE = 'NUMERO_FLOTANTE'
TT_CADENA_LITERAL = 'CADENA_LITERAL'

TT_COMENTARIO = 'COMENTARIO' # Generalmente se ignoran o se manejan de forma especial

TT_NUEVA_LINEA = 'NUEVA_LINEA' # Token para los saltos de línea explícitos
TT_INDENT = 'INDENT'           # Token para aumento de indentación
TT_DEDENT = 'DEDENT'           # Token para disminución de indentación

TT_EOF = 'EOF'                 # Fin de archivo/entrada
TT_ERROR_LEXICO = 'ERROR_LEXICO' # Token para errores
TT_ESPACIO = 'ESPACIO'         # Para espacios que no son indentación (usualmente se ignoran)




# Especificaciones de los tokens: (expresión_regular, TIPO_TOKEN)
# El orden es importante.
ESPECIFICACIONES_TOKEN = [
    # Comentarios (deben ir primero para ser descartados o manejados)
    (r'#[^\n]*',                 TT_COMENTARIO),       # Comentario de una línea

    # Nueva línea (importante para la estructura de Python y la indentación)
    (r'\n',                      TT_NUEVA_LINEA),

    # Espacios y tabs (que no son indentación al inicio de línea)
    # Los capturamos para poder ignorarlos explícitamente si no son indentación.
    # La indentación se manejará de forma separada y más compleja.
    (r'[ \t]+',                  TT_ESPACIO),

    # Literales de cadena (manejar diferentes tipos de comillas y multilínea)
    # Nota: Estos regex son simplificados y podrían no cubrir todos los casos de escape.
    (r'"""([\s\S]*?)"""',        TT_CADENA_LITERAL),  # Docstring/cadena multilínea con comillas dobles
    (r"'''([\s\S]*?)'''",        TT_CADENA_LITERAL),  # Docstring/cadena multilínea con comillas simples
    (r'"([^"\\]*(\\.[^"\\]*)*)"', TT_CADENA_LITERAL),  # Cadena con comillas dobles (maneja escapes simples)
    (r"'([^'\\]*(\\.[^'\\]*)*)'", TT_CADENA_LITERAL),  # Cadena con comillas simples (maneja escapes simples)
    # Podríamos añadir f-strings, raw strings (r""), byte strings (b"") si quisiéramos expandir.

    # Palabras reservadas y Identificadores
    # El regex para IDENTIFICADOR es más general.
    # Una forma común es capturar como IDENTIFICADOR y luego verificar si está en PALABRAS_RESERVADAS.
    (r'[a-zA-Z_]\w*',            TT_IDENTIFICADOR),   # Identificadores (incluye palabras reservadas inicialmente)

    # Números (flotantes antes que enteros para evitar coincidencias parciales)
    # Este regex para flotantes es básico, Python soporta notación científica, etc.
    (r'\d+\.\d*([eE][-+]?\d+)?',  TT_NUMERO_FLOTANTE), # Ej: 3.14, 3., 0.5, 1e-5
    (r'\.\d+([eE][-+]?\d+)?',    TT_NUMERO_FLOTANTE), # Ej: .5
    (r'\d+([eE][-+]?\d+)',       TT_NUMERO_FLOTANTE), # Ej: 1e5 (entero con exponente es flotante)
    (r'\d+',                     TT_NUMERO_ENTERO),   # Ej: 123, 0

    # Operadores (los más largos primero para evitar coincidencias parciales)
    (r'\/\/',                    TT_OPERADOR),        # División entera
    (r'\*\*',                    TT_OPERADOR),        # Potencia
    (r'==|!=|<=|>=',             TT_OPERADOR),        # Comparación
    (r'\+=|-=|\*=|/=|//=|%=|\*\*=', TT_OPERADOR),    # Asignación compuesta
    (r'[+\-*/%<>&|^~=]',         TT_OPERADOR),        # Operadores de un solo carácter

    # Delimitadores
    (r'[\(\)\[\]\{\}:,\.]',      TT_DELIMITADOR),
]

# Combinar todas las expresiones regulares en una sola gran expresión regular
# usando grupos nombrados (?P<TOKEN_TYPE>...) para identificar qué regla coincidió.
# Esto es una alternativa a iterar sobre ESPECIFICACIONES_TOKEN para cada match.
# Por ahora, seguiremos con la iteración simple sobre ESPECIFICACIONES_TOKEN.
# La lógica de indentación se manejará por separado porque no encaja bien
# en este esquema de regex simple por token.


# (Continuación, después de ESPECIFICACIONES_TOKEN)

class LexerPython:
    def __init__(self, codigo_fuente):
        self.codigo = codigo_fuente
        self.posicion_actual = 0   # Posición actual en self.codigo
        self.linea_actual = 1      # Número de línea actual (comienza en 1)
        self.columna_actual = 1    # Columna actual en la línea (comienza en 1)
        
        # Para el manejo de la indentación
        self.pila_indentacion = [0] # Pila para rastrear los niveles de indentación. Empieza con 0.
        self.esperando_indentacion_linea = True # True si estamos al inicio de una línea esperando espacios/tabs.

    def _avanzar(self, cantidad=1):
        """Avanza la posición actual en el código y actualiza línea/columna."""
        for _ in range(cantidad):
            if self.posicion_actual < len(self.codigo):
                caracter = self.codigo[self.posicion_actual]
                if caracter == '\n':
                    self.linea_actual += 1
                    self.columna_actual = 1
                    self.esperando_indentacion_linea = True # Después de una nueva línea, esperamos indentación
                else:
                    self.columna_actual += 1
                self.posicion_actual += 1
            else:
                # Ya no hay más caracteres para avanzar
                break 

    def _caracter_actual(self):
        """Devuelve el carácter en la posición actual o None si es EOF."""
        if self.posicion_actual < len(self.codigo):
            return self.codigo[self.posicion_actual]
        return None

    def _peek(self, cantidad=1):
        """Devuelve el siguiente carácter (o N caracteres) sin avanzar la posición."""
        peek_pos = self.posicion_actual + cantidad -1
        if peek_pos < len(self.codigo):
            return self.codigo[self.posicion_actual : self.posicion_actual + cantidad]
        return None

    # Los métodos para tokenizar, manejar indentación, etc., vendrán aquí.



    def _manejar_indentacion(self):
        """
        Compara la indentación actual con la pila de indentación y genera
        tokens INDENT o DEDENT según sea necesario.
        Este método se llama al inicio de una nueva línea (después de procesar \n
        y antes de cualquier otro token en esa línea, excepto espacios de indentación).
        """
        tokens_indentacion = []
        if not self.esperando_indentacion_linea:
            return tokens_indentacion # No estamos al inicio de una línea para verificar indentación

        # Contar los espacios/tabs de la indentación actual
        indentacion_actual_str = ""
        pos_temp = self.posicion_actual
        while pos_temp < len(self.codigo) and self.codigo[pos_temp] in ' \t':
            indentacion_actual_str += self.codigo[pos_temp]
            pos_temp += 1
        
        # Asumimos que los tabs se expanden a un múltiplo de 8 espacios,
        # o una política de tabs consistente (ej. 4 espacios).
        # Por simplicidad, contaremos tabs como 1 y espacios como 1,
        # pero una implementación real debería ser más robusta o forzar una política.
        # Aquí vamos a usar una conversión simple: 1 tab = 4 espacios (configurable)
        espacios_por_tab = 4 
        nivel_indentacion_actual = 0
        for char_indent in indentacion_actual_str:
            if char_indent == ' ':
                nivel_indentacion_actual += 1
            elif char_indent == '\t':
                # Ajustar al siguiente múltiplo de espacios_por_tab
                # nivel_indentacion_actual = (nivel_indentacion_actual // espacios_por_tab + 1) * espacios_por_tab
                # O más simple, pero menos preciso si se mezclan tabs y espacios de forma inconsistente:
                nivel_indentacion_actual += espacios_por_tab 
        
        # Solo procesar indentación si la línea no está vacía después de la indentación
        # o si es el final del archivo (para cerrar bloques abiertos).
        siguiente_caracter_no_espacio = None
        if pos_temp < len(self.codigo):
            siguiente_caracter_no_espacio = self.codigo[pos_temp]

        # No generar tokens de indentación para líneas completamente vacías o solo comentarios
        # a menos que sea para cerrar bloques al final del archivo.
        if siguiente_caracter_no_espacio == '\n' or (siguiente_caracter_no_espacio == '#' and self.posicion_actual == pos_temp - len(indentacion_actual_str)):
             # Si la línea está vacía o es un comentario de línea completa, no cambiamos el nivel de indentación actual
             # y consumimos los espacios de indentación.
            if indentacion_actual_str:
                self._avanzar(len(indentacion_actual_str)) # Consumir los espacios de indentación
            self.esperando_indentacion_linea = False # Ya no esperamos indentación en esta línea
            return tokens_indentacion


        # Comparamos con el último nivel de indentación en la pila
        if nivel_indentacion_actual > self.pila_indentacion[-1]:
            self.pila_indentacion.append(nivel_indentacion_actual)
            tokens_indentacion.append(Token(TT_INDENT, indentacion_actual_str, self.linea_actual, 1)) # Columna de indent es 1
            self._avanzar(len(indentacion_actual_str)) # Consumir los espacios/tabs de indentación
        elif nivel_indentacion_actual < self.pila_indentacion[-1]:
            while nivel_indentacion_actual < self.pila_indentacion[-1]:
                self.pila_indentacion.pop()
                # El lexema para DEDENT es conceptual, no hay un texto específico.
                # Usamos una cadena vacía o un marcador.
                tokens_indentacion.append(Token(TT_DEDENT, "<DEDENT>", self.linea_actual, 1)) 
                if nivel_indentacion_actual > self.pila_indentacion[-1]:
                    # Error: Nivel de indentación inconsistente (des-indentado a un nivel no previo)
                    # Este error es más bien sintáctico, pero el lexer puede detectarlo.
                    # Por ahora, lo reportamos aquí.
                    tokens_indentacion.append(Token(TT_ERROR_LEXICO, 
                                                    f"Error de des-indentación: nivel inconsistente. Esperaba {self.pila_indentacion[-1]} o menos.",
                                                    self.linea_actual, 1))
                    break # Salir del while para evitar bucles si hay error grave
            # No consumimos caracteres aquí, ya que el DEDENT es implícito.
            # La indentación actual (menor) ya fue leída para calcular nivel_indentacion_actual.
            # Nos aseguramos de que la posición actual refleje los espacios leídos.
            self._avanzar(len(indentacion_actual_str))
        else: # nivel_indentacion_actual == self.pila_indentacion[-1]
            # Misma indentación, no hacer nada, solo consumir los espacios.
            if indentacion_actual_str:
                 self._avanzar(len(indentacion_actual_str))

        self.esperando_indentacion_linea = False # Ya no esperamos indentación en esta línea (después de procesarla)
        return tokens_indentacion


    def _omitir_espacios_y_comentarios_inline(self):
        """Omite espacios en blanco (que no son indentación) y comentarios."""
        while self.posicion_actual < len(self.codigo):
            if self.codigo[self.posicion_actual] in ' \t': # Espacios que no son indentación
                self._avanzar()
            elif self.codigo[self.posicion_actual] == '#': # Comentario de línea
                # Avanzar hasta el final de la línea o del archivo
                while self.posicion_actual < len(self.codigo) and self.codigo[self.posicion_actual] != '\n':
                    self._avanzar()
                # No consumimos la NUEVA_LINEA aquí, se hará como un token separado
            else:
                break # Encontramos algo que no es espacio ni comentario inline

    def obtener_siguiente_token(self):
        """
        Obtiene el siguiente token del código fuente.
        Maneja la indentación y omite espacios y comentarios.
        """
        # Primero, si estamos al inicio de una línea, manejar la indentación
        if self.esperando_indentacion_linea:
            tokens_indent_dedent = self._manejar_indentacion()
            if tokens_indent_dedent: # Si se generaron tokens INDENT/DEDENT, devolver el primero
                # Guardar los restantes para las próximas llamadas si se generaron varios (ej. múltiples DEDENT)
                # Esto requeriría una cola interna de tokens pendientes.
                # Por ahora, simplificamos: _manejar_indentacion devuelve una lista,
                # y si hay algo, esta función debería devolverlos uno por uno.
                # Para una primera implementación, asumimos que _manejar_indentacion devuelve 0 o 1 token
                # o que el llamador maneja la lista.
                # --- Refactorización necesaria aquí para manejar múltiples tokens de indent/dedent ---
                # Por ahora, si hay, devolvemos el primero y el resto se perdería.
                # Solución simple: tener una lista de "tokens_buffer" en el lexer.
                # Si self.tokens_buffer no está vacío, pop y return.
                # Sino, calcular el siguiente.
                # _manejar_indentacion llenaría self.tokens_buffer.
                # Para este ejemplo, vamos a simplificar y asumir que devuelve máximo un token relevante a la vez
                # o que el llamador procesará la lista. Por ahora, devolveremos el primero de la lista si existe.
                # Este es un punto a mejorar.
                # Una forma simple: Si _manejar_indentacion devuelve una lista, la retornamos y el tokenizer principal
                # la procesa.
                if tokens_indent_dedent:
                    return tokens_indent_dedent # Devolvemos la lista de tokens de indent/dedent
        
        # Omitir espacios en blanco (que no son indentación) y comentarios inline
        # después de manejar la indentación.
        if not self.esperando_indentacion_linea: # Solo si no estamos esperando indentación (ya se procesó o no aplica)
             self._omitir_espacios_y_comentarios_inline()


        # Comprobar si hemos llegado al final del código
        if self.posicion_actual >= len(self.codigo):
            # Antes de EOF, asegurarse de cerrar todos los bloques de indentación abiertos
            tokens_finales_dedent = []
            if len(self.pila_indentacion) > 1: # Hay niveles de indentación abiertos (más que el global 0)
                linea_eof = self.linea_actual
                col_eof = self.columna_actual
                while len(self.pila_indentacion) > 1:
                    self.pila_indentacion.pop()
                    tokens_finales_dedent.append(Token(TT_DEDENT, "<DEDENT_EOF>", linea_eof, col_eof))
                if tokens_finales_dedent:
                    # Similar al problema anterior: cómo devolver múltiples tokens.
                    # Devolveremos la lista para que el método principal la maneje.
                    return tokens_finales_dedent
            return [Token(TT_EOF, "EOF", self.linea_actual, self.columna_actual)] # Devolver como lista


        # Intentar hacer coincidir las especificaciones de token con el código restante
        codigo_restante = self.codigo[self.posicion_actual:]
        
        for patron_regex, tipo_token in ESPECIFICACIONES_TOKEN:
            match = re.match(patron_regex, codigo_restante)
            if match:
                lexema = match.group(0) # El texto completo que coincidió
                
                # Guardar posición antes de avanzar para la creación del token
                linea_inicio_token = self.linea_actual
                columna_inicio_token = self.columna_actual

                self._avanzar(len(lexema)) # Avanzar la posición en el código fuente

                # Si es un identificador, verificar si es una palabra reservada
                if tipo_token == TT_IDENTIFICADOR and lexema in PALABRAS_RESERVADAS:
                    return [Token(TT_PALABRA_RESERVADA, lexema, linea_inicio_token, columna_inicio_token)]

                # Si es un espacio o comentario, y no los estamos guardando, podríamos querer omitirlos
                # y llamar recursivamente a obtener_siguiente_token.
                # Pero ya los manejamos en _omitir_espacios_y_comentarios_inline y
                # la indentación en _manejar_indentacion.
                # Los tokens TT_ESPACIO y TT_COMENTARIO se generan aquí si no se filtraron antes.
                # Generalmente, un lexer los omite a menos que una fase posterior los necesite.
                if tipo_token == TT_ESPACIO or tipo_token == TT_COMENTARIO:
                    # Omitir y obtener el siguiente (esto puede hacerse en el bucle principal de tokenización)
                    # Por ahora, los generaremos y el bucle principal de tokenización los ignorará.
                    # return self.obtener_siguiente_token() # Recursión para omitir (cuidado con bucles infinitos)
                    # Mejor: el bucle principal que llama a esto los filtrará.
                     return [Token(tipo_token, lexema, linea_inicio_token, columna_inicio_token)]


                # Para números, convertir el lexema a su valor numérico
                valor = lexema
                if tipo_token == TT_NUMERO_ENTERO:
                    valor = int(lexema)
                elif tipo_token == TT_NUMERO_FLOTANTE:
                    valor = float(lexema)
                elif tipo_token == TT_CADENA_LITERAL:
                    # Quitar las comillas del inicio y final para el valor, y procesar escapes si es necesario
                    # Esto es una simplificación, el manejo de escapes es más complejo.
                    if lexema.startswith('"""') or lexema.startswith("'''"):
                        valor = lexema[3:-3]
                    else:
                        valor = lexema[1:-1] 
                    # Aquí se podrían procesar secuencias de escape comunes como \n, \t, \\, \', \"
                    valor = valor.encode('utf-8').decode('unicode_escape') # Intento básico de manejar escapes

                return [Token(tipo_token, lexema, linea_inicio_token, columna_inicio_token, valor)]
        
        # Si ninguna especificación coincide, es un error léxico
        caracter_error = self.codigo[self.posicion_actual]
        linea_error = self.linea_actual
        columna_error = self.columna_actual
        self._avanzar() # Avanzar para no quedarse atascado en el error
        return [Token(TT_ERROR_LEXICO, caracter_error, linea_error, columna_error, 
                     valor=f"Carácter no reconocido: '{caracter_error}'")]
    



    def tokenizar(self):
        """
        Procesa todo el código fuente y devuelve una lista de tokens.
        Omite tokens de espacio y comentarios.
        """
        tokens_resultantes = []
        # Buffer para tokens generados por _manejar_indentacion o al final del archivo (múltiples DEDENTs)
        buffer_tokens_pendientes = []

        while True:
            nuevos_tokens = []
            if buffer_tokens_pendientes:
                # Si hay tokens en el buffer (de múltiples DEDENTs por ejemplo), procesarlos primero.
                # Aquí tomamos uno a la vez del buffer para simplificar el bucle principal,
                # pero también podríamos extender tokens_resultantes con todo el buffer.
                token_actual = buffer_tokens_pendientes.pop(0) # Tomar el primero de la lista
                nuevos_tokens.append(token_actual) 
            else:
                # Si el buffer está vacío, obtener el siguiente token (o lista de tokens) del código.
                nuevos_tokens_generados = self.obtener_siguiente_token()
                
                if nuevos_tokens_generados: # puede ser una lista
                    buffer_tokens_pendientes.extend(nuevos_tokens_generados) # Añadir todos a la cola
                    if buffer_tokens_pendientes: # Si se añadieron, tomar el primero para procesar
                        token_actual = buffer_tokens_pendientes.pop(0)
                        nuevos_tokens.append(token_actual)
                    else: # No debería pasar si nuevos_tokens_generados no estaba vacío
                        continue 
                else: # No se generaron nuevos tokens (raro, debería haber al menos EOF)
                    break


            # Procesar el token_actual obtenido (que está en nuevos_tokens[0])
            if nuevos_tokens:
                token_para_procesar = nuevos_tokens[0]

                # Ignorar espacios y comentarios, a menos que se decida lo contrario
                if token_para_procesar.tipo in [TT_ESPACIO, TT_COMENTARIO]:
                    if not buffer_tokens_pendientes and token_para_procesar.tipo == TT_EOF: # Asegurarse de no perder el EOF si es el único en el buffer
                         tokens_resultantes.append(token_para_procesar)
                         break # Salir del bucle while si es EOF
                    continue # Saltar al siguiente ciclo del while para obtener más tokens

                tokens_resultantes.append(token_para_procesar)

                if token_para_procesar.tipo == TT_EOF:
                    break # Fin de la tokenización
            else:
                # Esto no debería ocurrir si obtener_siguiente_token siempre devuelve algo
                # (al menos EOF o un error).
                # Podría indicar un problema en la lógica de obtención de tokens.
                print("Advertencia: obtener_siguiente_token devolvió una lista vacía inesperadamente.")
                break
                
        return tokens_resultantes

# Fin de la clase LexerPython