# src/simulador_ejecucion/interprete_pascal.py

try:
    from analizador_sintactico.parser_pascal import (
        NodoPrograma, NodoBloque, NodoDeclaracionesVar, NodoDeclaracionVar,
        NodoTipo, NodoCuerpoPrograma, NodoAsignacion, NodoLlamadaProcedimiento,
        NodoIf, NodoIdentificador, NodoLiteral, NodoExpresionBinaria, NodoWhile, NodoRepeat,NodoExpresionUnaria
    )
    from analizador_lexico.lexer_pascal import TT_OPERADOR_RELACIONAL, TT_OPERADOR_ARITMETICO, TT_OPERADOR_LOGICO, TT_PALABRA_RESERVADA
except ImportError:
    print("ADVERTENCIA CRÍTICA (InterpretePascal): No se pudieron importar los nodos AST o tipos de token.")
    # Placeholders
    class NodoPrograma: pass
    class NodoBloque: pass
    class NodoDeclaracionesVar: pass
    class NodoDeclaracionVar: pass
    class NodoTipo: pass
    class NodoCuerpoPrograma: pass
    class NodoAsignacion: pass
    class NodoLlamadaProcedimiento: pass
    class NodoIf: pass
    class NodoWhile: pass
    class NodoRepeat: pass
    class NodoIdentificador: pass
    class NodoLiteral: pass
    class NodoExpresionBinaria: pass
    class NodoExpresionUnaria: pass
    TT_OPERADOR_RELACIONAL = "OPERADOR_RELACIONAL"
    TT_OPERADOR_ARITMETICO = "OPERADOR_ARITMETICO"
    TT_OPERADOR_LOGICO = "OPERADOR_LOGICO"


class InterpretePascal:
    def __init__(self, tabla_simbolos_global=None):
        self.memoria_variables = {} 
        self.tabla_simbolos_global = tabla_simbolos_global
        # print(f"[Interprete DEBUG] Intérprete inicializado. Memoria: {self.memoria_variables}")

    def interpretar(self, nodo_ast_raiz):
        if not isinstance(nodo_ast_raiz, NodoPrograma):
            print("Error del Intérprete: Se esperaba un NodoPrograma como raíz del AST.")
            return
        try:
            print("\n--- Iniciando Simulación de Ejecución (Pascal) ---")
            self.visitar_NodoPrograma(nodo_ast_raiz)
            print("--- Simulación de Ejecución Finalizada (Pascal) ---")
            # print(f"[Interprete DEBUG] Estado final de la memoria: {self.memoria_variables}")
        except RuntimeError as e_runtime:
            print(f"Error en Tiempo de Ejecución (Pascal): {e_runtime}")
        except Exception as e_general:
            print(f"Error Inesperado durante la Interpretación (Pascal): {e_general}")
            import traceback
            traceback.print_exc()

    def visitar_NodoPrograma(self, nodo):
        if nodo.bloque_nodo:
            self.visitar_NodoBloque(nodo.bloque_nodo)

    def visitar_NodoBloque(self, nodo):
        if nodo.declaraciones_var_nodo:
            pass # Las declaraciones ya se usaron para la tabla de símbolos.
        if nodo.cuerpo_nodo:
            self.visitar_NodoCuerpoPrograma(nodo.cuerpo_nodo)

    def visitar_NodoCuerpoPrograma(self, nodo):
        if nodo.lista_sentencias_nodos:
            for sentencia_nodo in nodo.lista_sentencias_nodos:
                self.ejecutar_sentencia(sentencia_nodo)

    def visitar_NodoWhile(self, nodo):
        # Ejecuta una sentencia de bucle 'while'.
        # print(f"[Interprete DEBUG] Visitando NodoWhile")
        
        # Se evalúa la condición del bucle.
        # La evaluación de la condición se hace ANTES de cada iteración.
        valor_condicion = self.evaluar_expresion(nodo.condicion_nodo)
        if not isinstance(valor_condicion, bool):
            raise RuntimeError(f"La condición de la sentencia WHILE debe ser booleana, pero se evaluó a '{valor_condicion}' (tipo: {type(valor_condicion).__name__}).")

        while valor_condicion:
            # Mientras la condición sea verdadera, se ejecuta el cuerpo del bucle.
            self.ejecutar_sentencia(nodo.cuerpo_sentencia_nodo)
            
            # Se vuelve a evaluar la condición al final de cada iteración.
            valor_condicion = self.evaluar_expresion(nodo.condicion_nodo)
            if not isinstance(valor_condicion, bool): # Re-verificar tipo después de cada evaluación
                raise RuntimeError(f"La condición de la sentencia WHILE (en iteración) debe ser booleana, se evaluó a '{valor_condicion}' (tipo: {type(valor_condicion).__name__}).")
        # print(f"[Interprete DEBUG] Saliendo de NodoWhile, condición final: {valor_condicion}")

    def visitar_NodoRepeat(self, nodo):
        # Ejecuta una sentencia de bucle 'repeat...until'.
        # La lógica es ejecutar el cuerpo del bucle al menos una vez,
        # y luego continuar ejecutándolo mientras la condición 'until' sea falsa.
        
        # print(f"[Interprete DEBUG] Visitando NodoRepeat") # Descomentar para depuración
        
        while True: # El bucle se ejecuta al menos una vez.
            # Ejecuta cada sentencia en el cuerpo del bucle.
            # El cuerpo del NodoRepeat (nodo.lista_sentencias_cuerpo) es una lista de nodos de sentencia.
            if nodo.lista_sentencias_cuerpo:
                for sentencia_nodo_cuerpo in nodo.lista_sentencias_cuerpo:
                    self.ejecutar_sentencia(sentencia_nodo_cuerpo) # Llama al despachador de sentencias.
            
            # Evalúa la condición de terminación ('until') al final de cada iteración.
            valor_condicion_until = self.evaluar_expresion(nodo.condicion_nodo)
            
            # La condición en Pascal para 'until' debe ser booleana.
            if not isinstance(valor_condicion_until, bool):
                raise RuntimeError(
                    f"La condición de la sentencia REPEAT-UNTIL debe ser booleana, "
                    f"pero se evaluó a '{valor_condicion_until}' (tipo: {type(valor_condicion_until).__name__})."
                )

            if valor_condicion_until: # El bucle termina cuando la condición 'until' es VERDADERA.
                break # Sale del bucle 'while True'.
        
        # print(f"[Interprete DEBUG] Saliendo de NodoRepeat, condición final de 'until': {valor_condicion_until}") # Descomentar para depuración


    def ejecutar_sentencia(self, nodo_sentencia):
        if isinstance(nodo_sentencia, NodoAsignacion):
            self.visitar_NodoAsignacion(nodo_sentencia)
        elif isinstance(nodo_sentencia, NodoLlamadaProcedimiento):
            self.visitar_NodoLlamadaProcedimiento(nodo_sentencia)
        elif isinstance(nodo_sentencia, NodoIf):
            self.visitar_NodoIf(nodo_sentencia)
        elif isinstance(nodo_sentencia, NodoCuerpoPrograma): 
            self.visitar_NodoCuerpoPrograma(nodo_sentencia)
        elif isinstance(nodo_sentencia, NodoWhile): 
            self.visitar_NodoWhile(nodo_sentencia)
        elif isinstance(nodo_sentencia, NodoRepeat): 
            self.visitar_NodoRepeat(nodo_sentencia)
        else:
            raise RuntimeError(f"Tipo de nodo de sentencia desconocido para ejecutar: {type(nodo_sentencia).__name__}")

    def visitar_NodoAsignacion(self, nodo):
        nombre_variable = nodo.variable_token_id.lexema
        valor_expresion = self.evaluar_expresion(nodo.expresion_nodo)
        self.memoria_variables[nombre_variable] = valor_expresion
        # print(f"[Interprete DEBUG] Variable '{nombre_variable}' asignada con valor: {repr(valor_expresion)}. Memoria: {self.memoria_variables}")

    def visitar_NodoLlamadaProcedimiento(self, nodo):
        nombre_procedimiento = nodo.nombre_proc_token.lexema.lower()
        # print(f"[Interprete DEBUG] Llamada a: {nombre_procedimiento}")

        if nombre_procedimiento == "writeln" or nombre_procedimiento == "write":
            salida_str = []
            for arg_nodo in nodo.argumentos_nodos:
                valor_arg = self.evaluar_expresion(arg_nodo)
                salida_str.append(str(valor_arg)) # Convertir todos los argumentos a cadena para imprimir
            
            if nombre_procedimiento == "writeln":
                print("".join(salida_str)) # Imprime y luego nueva línea (por defecto en print)
            else: # write
                print("".join(salida_str), end="") # Imprime sin nueva línea al final

        elif nombre_procedimiento == "readln":
            if nodo.argumentos_nodos:
                for arg_nodo_id in nodo.argumentos_nodos:
                    if not isinstance(arg_nodo_id, NodoIdentificador):
                        raise RuntimeError(f"Argumento para 'readln' debe ser una variable (identificador), se obtuvo {type(arg_nodo_id).__name__}")
                    
                    nombre_variable = arg_nodo_id.nombre
                    # Obtener tipo de la tabla de símbolos para intentar conversión
                    simbolo_info = None
                    if self.tabla_simbolos_global:
                         simbolo_info = self.tabla_simbolos_global.buscar_simbolo(nombre_variable)
                    
                    tipo_esperado = simbolo_info['tipo_dato'] if simbolo_info else 'string' # Default a string si no hay info

                    # Solicitar entrada al usuario. El prompt podría ser el nombre de la variable.
                    # En Pascal real, readln no muestra un prompt automático con el nombre de la variable.
                    # Se asume que un 'write' previo lo hizo.
                    try:
                        entrada_usuario = input() # Leer una línea de la entrada estándar
                        
                        valor_convertido = None
                        if tipo_esperado == 'integer':
                            valor_convertido = int(entrada_usuario)
                        elif tipo_esperado == 'real':
                            valor_convertido = float(entrada_usuario)
                        elif tipo_esperado == 'char':
                            if len(entrada_usuario) == 1:
                                valor_convertido = entrada_usuario
                            else:
                                raise ValueError("Se esperaba un solo carácter para el tipo char.")
                        elif tipo_esperado == 'boolean': # Pascal no lee booleanos directamente con readln estándar
                            if entrada_usuario.lower() == 'true': valor_convertido = True
                            elif entrada_usuario.lower() == 'false': valor_convertido = False
                            else: raise ValueError("Para boolean, ingrese 'true' o 'false'.")
                        else: # string u otro tipo no manejado específicamente para conversión
                            valor_convertido = entrada_usuario 
                        
                        self.memoria_variables[nombre_variable] = valor_convertido
                        # print(f"[Interprete DEBUG] readln: Variable '{nombre_variable}' asignada con valor: {repr(valor_convertido)}")
                    except ValueError as ve:
                        raise RuntimeError(f"Error de tipo al leer la entrada para '{nombre_variable}'. Se esperaba tipo '{tipo_esperado}'. Error: {ve}")
            else:
                # readln sin argumentos solo consume el resto de la línea (o espera Enter)
                input() 

        elif nombre_procedimiento == "clrscr":
            print("\n" * 20) 
            print("[SIMULACIÓN PASCAL] clrscr ejecutado (pantalla 'limpiada').")
        elif nombre_procedimiento == "readkey":
            input("[SIMULACIÓN PASCAL] readkey ejecutado. Presione Enter para continuar...")
        else:
            print(f"Advertencia del Intérprete: Llamada al procedimiento '{nombre_procedimiento}' no implementada aún.")

    def visitar_NodoIf(self, nodo):
        # print("[Interprete DEBUG] Visitando NodoIf")
        valor_condicion = self.evaluar_expresion(nodo.condicion_nodo)
        
        # En Pascal, la condición de un IF debe ser booleana.
        if not isinstance(valor_condicion, bool):
            raise RuntimeError(f"La condición de la sentencia IF debe ser booleana, pero se evaluó a '{valor_condicion}' (tipo: {type(valor_condicion).__name__}).")

        if valor_condicion: # Si la condición es Verdadera
            self.ejecutar_sentencia(nodo.then_sentencia_nodo)
        elif nodo.else_sentencia_nodo: # Si la condición es Falsa y hay una rama 'else'
            self.ejecutar_sentencia(nodo.else_sentencia_nodo)

    def evaluar_expresion(self, nodo_expresion):
        if isinstance(nodo_expresion, NodoLiteral):
            return self.evaluar_NodoLiteral(nodo_expresion)
        elif isinstance(nodo_expresion, NodoIdentificador):
            return self.evaluar_NodoIdentificador(nodo_expresion)
        elif isinstance(nodo_expresion, NodoExpresionBinaria):
            return self.evaluar_NodoExpresionBinaria(nodo_expresion)
        elif isinstance(nodo_expresion, NodoExpresionUnaria):
            return self.evaluar_NodoExpresionUnaria(nodo_expresion)
        else:
            raise RuntimeError(f"Tipo de nodo de expresión desconocido para evaluar: {type(nodo_expresion).__name__}")

    def evaluar_NodoLiteral(self, nodo):
        return nodo.valor

    def evaluar_NodoIdentificador(self, nodo):
        nombre_variable = nodo.nombre
        if nombre_variable in self.memoria_variables:
            return self.memoria_variables[nombre_variable]
        else:
            raise RuntimeError(f"Variable '{nombre_variable}' usada antes de que se le haya asignado un valor.")

    def evaluar_NodoExpresionBinaria(self, nodo):
        # Evalúa una expresión binaria (ej: operando_izq operador operando_der).
        # print(f"[Interprete DEBUG] Evaluando NodoExpresionBinaria, operador: {nodo.operador_token.lexema}")
        
        valor_izq = self.evaluar_expresion(nodo.operando_izq_nodo)
        valor_der = self.evaluar_expresion(nodo.operando_der_nodo)
        operador = nodo.operador_token.lexema.lower() # Convertir a minúsculas para 'div', 'mod'
        tipo_operador_token = nodo.operador_token.tipo

        # print(f"[Interprete DEBUG] ExpBin: {repr(valor_izq)} {operador} {repr(valor_der)}")

        if tipo_operador_token == TT_OPERADOR_RELACIONAL:
            if operador == '=':  return valor_izq == valor_der
            elif operador == '<>': return valor_izq != valor_der
            elif operador == '<':  return valor_izq < valor_der
            elif operador == '>':  return valor_izq > valor_der
            elif operador == '<=': return valor_izq <= valor_der
            elif operador == '>=': return valor_izq >= valor_der
            else:
                raise RuntimeError(f"Operador relacional desconocido: '{operador}'")
        
        elif tipo_operador_token == TT_OPERADOR_ARITMETICO:
            # Asegurarse de que los operandos sean numéricos para operaciones aritméticas.
            # Python puede sumar algunos tipos no numéricos (ej. strings), pero Pascal es más estricto.
            # Para una simulación más precisa, se harían chequeos de tipo aquí o conversiones.
            if not (isinstance(valor_izq, (int, float)) and isinstance(valor_der, (int, float))):
                # Excepción para la concatenación de cadenas con '+'
                if operador == '+' and isinstance(valor_izq, str) and isinstance(valor_der, str):
                    return valor_izq + valor_der
                # Podríamos permitir str + num convirtiendo num a str, o num + str. Pascal no lo hace directamente.
                # Para simplificar, si no son ambos números (y no es concatenación de str), es error.
                raise RuntimeError(f"Operandos para el operador aritmético '{operador}' deben ser numéricos (o cadenas para '+'). Se obtuvieron {type(valor_izq).__name__} y {type(valor_der).__name__}.")

            if operador == '+': 
                return valor_izq + valor_der
            elif operador == '-': 
                return valor_izq - valor_der
            elif operador == '*': 
                return valor_izq * valor_der
            # Añadir '/' para división real, 'div' para entera, 'mod' para módulo si se implementan en el lexer/parser.
            # Ejemplo para división real:
            elif operador == '/': 
                 if valor_der == 0: raise RuntimeError("División por cero.")
                 return valor_izq / valor_der
            elif operador == 'div': # División entera.
                # 'div' requiere que ambos operandos sean enteros.
                if not (isinstance(valor_izq, int) and isinstance(valor_der, int)):
                     raise RuntimeError(f"Operandos para 'div' deben ser enteros. Se obtuvieron {type(valor_izq).__name__} y {type(valor_der).__name__}.")
                if valor_der == 0: # Evitar división por cero.
                    raise RuntimeError("División entera por cero.")
                return valor_izq // valor_der
            elif operador == 'mod': # Módulo.
                # 'mod' requiere que ambos operandos sean enteros.
                if not (isinstance(valor_izq, int) and isinstance(valor_der, int)):
                     raise RuntimeError(f"Operandos para 'mod' deben ser enteros. Se obtuvieron {type(valor_izq).__name__} y {type(valor_der).__name__}.")
                if valor_der == 0: # Evitar módulo por cero.
                    raise RuntimeError("Módulo por cero.")
                return valor_izq % valor_der
            else:
                raise RuntimeError(f"Operador aritmético desconocido o no soportado: '{operador}'")
        
        elif nodo.operador_token.tipo == TT_PALABRA_RESERVADA and operador in ['and', 'or']:
        #     # Añadir lógica para 'and', 'or', 'not' (not es unario, se manejaría en parse_factor)
            if not (isinstance(valor_izq, bool) and isinstance(valor_der, bool)):
                raise RuntimeError(f"Operandos para el operador lógico '{operador}' deben ser booleanos.")
            if operador == 'and': return valor_izq and valor_der
            elif operador == 'or': return valor_izq or valor_der
            else:
                raise RuntimeError(f"Operador lógico desconocido: '{operador}'")
        
        
        else:
            raise RuntimeError(f"Tipo de operador binario no soportado: '{operador}' (tipo token: {nodo.operador_token.tipo})")


    def evaluar_NodoExpresionUnaria(self, nodo):
        # Evalúa una expresión unaria (actualmente solo 'not').
        operador = nodo.operador_token.lexema.lower()
        valor_operando = self.evaluar_expresion(nodo.operando_nodo)

        if operador == 'not':
            if not isinstance(valor_operando, bool):
                raise RuntimeError(f"El operando para 'not' debe ser booleano, se obtuvo {type(valor_operando).__name__}.")
            return not valor_operando
        else:
            raise RuntimeError(f"Operador unario desconocido o no soportado: '{operador}'")