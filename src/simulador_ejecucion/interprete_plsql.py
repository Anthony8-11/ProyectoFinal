# src/simulador_ejecucion/interprete_plsql.py

# Importar las clases de nodos AST necesarias desde el parser_plsql.
try:
    from analizador_sintactico.parser_plsql import (
        NodoScriptPLSQL, NodoBloquePLSQL, NodoDeclaracionVariablePLSQL, NodoTipoDatoPLSQL,
        NodoSentenciaPLSQL, NodoSentenciaAsignacionPLSQL, NodoLlamadaProcedimientoPLSQL,
        NodoSentenciaLoopPLSQL, NodoSentenciaExitWhenPLSQL, NodoSentenciaIfPLSQL,
        NodoSeccionExcepcionPLSQL, NodoClausulaWhenPLSQL, NodoSentenciaForLoopPLSQL,  # <-- Import FOR loop node
        NodoExpresionPLSQL, NodoIdentificadorPLSQL, NodoLiteralPLSQL, NodoExpresionUnariaPLSQL,
        NodoExpresionBinariaPLSQL, NodoMiembroExpresionPLSQL, NodoFuncionSQL, NodoSelect,
        NodoSentenciaRaisePLSQL,  # <-- Import RAISE node
        # Asegúrate de que todos los nodos que el parser puede generar estén aquí.
    )
    # Importar tipos de token si son necesarios para la evaluación.
    from analizador_lexico.lexer_plsql import Token, TT_OPERADOR_CONCATENACION_PLSQL, \
                                               TT_OPERADOR_ARITMETICO_PLSQL, TT_OPERADOR_COMPARACION_PLSQL, \
                                               TT_OPERADOR_LOGICO_PLSQL, TT_LITERAL_CADENA_PLSQL, \
                                               TT_LITERAL_NUMERICO_PLSQL, TT_LITERAL_BOOLEANO_PLSQL, \
                                               TT_LITERAL_NULL_PLSQL
except ImportError as e_import_ast_interprete_plsql:
    print(f"ADVERTENCIA CRÍTICA (InterpretePLSQL): No se pudieron importar los nodos AST desde 'parser_plsql.py'. Error: {e_import_ast_interprete_plsql}")
    # Definir placeholders muy básicos
    class NodoScriptPLSQL: pass
    class NodoBloquePLSQL: pass
    class NodoDeclaracionVariablePLSQL: pass
    class NodoTipoDatoPLSQL: pass
    class NodoSentenciaPLSQL: pass
    class NodoSentenciaAsignacionPLSQL: pass
    class NodoLlamadaProcedimientoPLSQL: pass
    class NodoSentenciaLoopPLSQL: pass
    class NodoSentenciaExitWhenPLSQL: pass
    class NodoSentenciaIfPLSQL: pass
    class NodoSeccionExcepcionPLSQL: pass
    class NodoClausulaWhenPLSQL: pass
    class NodoSentenciaForLoopPLSQL: pass  # <-- Placeholder for FOR loop node
    class NodoExpresionPLSQL: pass
    class NodoIdentificadorPLSQL: pass
    class NodoLiteralPLSQL: pass
    class NodoExpresionBinariaPLSQL: pass 
    class NodoMiembroExpresionPLSQL: pass
    class NodoFuncionSQL: pass
    class NodoExpresionUnariaPLSQL: pass 
    class NodoSelect: pass
    class NodoSentenciaRaisePLSQL: pass  # <-- Placeholder for RAISE node
    class Token: pass
    TT_OPERADOR_CONCATENACION_PLSQL = "OP_CONCAT_PLSQL"; TT_OPERADOR_ARITMETICO_PLSQL = "OP_ARIT_PLSQL"
    TT_OPERADOR_COMPARACION_PLSQL = "OP_COMP_PLSQL"; TT_OPERADOR_LOGICO_PLSQL = "OP_LOG_PLSQL"
    TT_LITERAL_CADENA_PLSQL, TT_LITERAL_NUMERICO_PLSQL, TT_LITERAL_BOOLEANO_PLSQL, TT_LITERAL_NULL_PLSQL = "LIT_STR", "LIT_NUM", "LIT_BOOL", "LIT_NULL"


# Excepción personalizada para errores en tiempo de ejecución del intérprete de PL/SQL
class ErrorTiempoEjecucionPLSQL(RuntimeError):
    """Error general en tiempo de ejecución para el intérprete de PL/SQL."""
    pass

class ErrorRetornoPLSQL(Exception): # Para RETURN en funciones PL/SQL (si se implementan)
    def __init__(self, valor):
        super().__init__("Sentencia RETURN ejecutada")
        self.valor = valor

class AlcancePLSQL:
    """Representa un alcance (scope) en PL/SQL para almacenar variables y otros símbolos."""
    def __init__(self, padre=None, nombre_alcance="global"):
        self.simbolos = {}  # Almacena variables, constantes, cursores, tipos, etc.
        self.padre = padre
        self.nombre_alcance = nombre_alcance
        # print(f"[AlcancePLSQL DEBUG] Alcance '{self.nombre_alcance}' creado. Padre: {id(padre) if padre else 'None'}")

    def declarar(self, nombre_simbolo, valor, tipo_simbolo="variable"):
        nombre_lower = nombre_simbolo.lower() # PL/SQL es insensible a mayúsculas para identificadores
        # print(f"[AlcancePLSQL DEBUG ({self.nombre_alcance})] Declarando '{nombre_lower}' (tipo: {tipo_simbolo}) = {repr(valor)}")
        if nombre_lower in self.simbolos:
            # PL/SQL permite redeclarar en sub-bloques (shadowing), pero no en el mismo bloque.
            # Esta lógica es simplificada.
            print(f"Advertencia (AlcancePLSQL): Redeclaración del símbolo '{nombre_lower}' en el mismo alcance '{self.nombre_alcance}'.")
        self.simbolos[nombre_lower] = {'valor': valor, 'tipo_simbolo': tipo_simbolo}

    def asignar(self, nombre_simbolo, valor):
        nombre_lower = nombre_simbolo.lower()
        # print(f"[AlcancePLSQL DEBUG ({self.nombre_alcance})] Asignando a '{nombre_lower}' = {repr(valor)}")
        alcance_busqueda = self
        while alcance_busqueda:
            if nombre_lower in alcance_busqueda.simbolos and alcance_busqueda.simbolos[nombre_lower]['tipo_simbolo'] == "variable":
                alcance_busqueda.simbolos[nombre_lower]['valor'] = valor
                return
            alcance_busqueda = alcance_busqueda.padre
        raise ErrorTiempoEjecucionPLSQL(f"Variable no declarada '{nombre_simbolo}'.")

    def obtener(self, nombre_simbolo):
        nombre_lower = nombre_simbolo.lower()
        # print(f"[AlcancePLSQL DEBUG ({self.nombre_alcance})] Obteniendo '{nombre_lower}'")
        alcance_busqueda = self
        while alcance_busqueda:
            if nombre_lower in alcance_busqueda.simbolos:
                valor = alcance_busqueda.simbolos[nombre_lower]['valor']
                # Si es una función simulada, llámala
                if callable(valor):
                    return valor()
                return valor
            alcance_busqueda = alcance_busqueda.padre
        # Simulación para SQLERRM y SQLCODE
        if nombre_lower == 'sqlerrm':
            return 'Simulación: mensaje de error'
        if nombre_lower == 'sqlcode':
            return -1
        raise ErrorTiempoEjecucionPLSQL(f"Símbolo no declarado '{nombre_simbolo}'.")

class InterpretePLSQL:
    def __init__(self):
        self.alcance_global = AlcancePLSQL(nombre_alcance="script_global")
        self.alcance_actual = self.alcance_global
        self.ultimo_error_runtime_mensaje = "No hay error." # Para SQLERRM

        self.paquetes_incorporados = {
            'dbms_output': {
                'put_line': self._simular_dbms_output_put_line
            },
            'to_char': self._simular_to_char,
            'chr': self._simular_chr,
            'sqlerrm': self._simular_sqlerrm # Añadir SQLERRM como función/variable global
        }
        # Hacer que los paquetes/funciones globales estén disponibles en el alcance global
        for nombre, obj in self.paquetes_incorporados.items():
            self.alcance_global.declarar(nombre, obj, tipo_simbolo="paquete_o_funcion_incorporada")
        self.alcance_global.objetos_globales_plsql_ref = self.paquetes_incorporados # Referencia para Alcance.obtener
        self.buffer_cout = [] 

    def _simular_dbms_output_put_line(self, *args):
        """Simula DBMS_OUTPUT.PUT_LINE."""
        if args:
            print(str(args[0])) # DBMS_OUTPUT.PUT_LINE toma un argumento
        else:
            print() # PUT_LINE sin argumentos imprime una línea vacía
        return None # Los procedimientos no devuelven valor

    def _simular_to_char(self, *args):
        """Simula la función TO_CHAR (muy simplificada)."""
        if not args:
            raise ErrorTiempoEjecucionPLSQL("TO_CHAR requiere al menos un argumento.")
        # Simplemente convierte el primer argumento a cadena.
        # Una implementación real manejaría formatos de fecha, número, etc.
        return str(args[0])

    def interpretar_script(self, nodo_script):
        """Punto de entrada para la interpretación de un script PL/SQL."""
        if not isinstance(nodo_script, NodoScriptPLSQL):
            print("Error del Intérprete PL/SQL: Se esperaba un NodoScriptPLSQL.")
            return
        
        print("\n--- Iniciando Simulación de Ejecución (PL/SQL) ---")
        try:
            for elemento in nodo_script.elementos:
                if isinstance(elemento, NodoBloquePLSQL):
                    self.visitar_NodoBloquePLSQL(elemento)
                elif isinstance(elemento, NodoSelect): # Para SELECTs a nivel de script
                    self.visitar_NodoSelect(elemento) 
                # (Añadir más tipos de elementos de script si se parsean, ej. CREATE PROCEDURE)
                else:
                    print(f"Advertencia (InterpretePLSQL): Tipo de elemento de script '{type(elemento).__name__}' no manejado.")
        except ErrorTiempoEjecucionPLSQL as e_runtime:
            print(f"Error en Tiempo de Ejecución (PL/SQL): {e_runtime}")
        except ErrorRetornoPLSQL as e_return: # Si un RETURN sale de un bloque principal
            print(f"Advertencia (InterpretePLSQL): Sentencia RETURN fuera de una función: valor {e_return.valor}")
        except Exception as e_general:
            print(f"Error Inesperado durante la Interpretación de PL/SQL: {e_general}")
            import traceback
            traceback.print_exc()
        finally:
            print("--- Simulación de Ejecución Finalizada (PL/SQL) ---")

    def visitar_NodoBloquePLSQL(self, nodo_bloque):
        """Ejecuta un bloque PL/SQL (DECLARE, BEGIN, EXCEPTION, END)."""
        alcance_anterior = self.alcance_actual
        self.alcance_actual = AlcancePLSQL(padre=alcance_anterior, nombre_alcance=f"bloque_{id(nodo_bloque)}")
        self.alcance_actual.objetos_globales_plsql_ref = self.paquetes_incorporados 

        if nodo_bloque.seccion_declaracion:
            for declaracion_var_nodo in nodo_bloque.seccion_declaracion:
                self.visitar_NodoDeclaracionVariablePLSQL(declaracion_var_nodo)
        
        try:
            if nodo_bloque.seccion_ejecutable:
                for sentencia_nodo in nodo_bloque.seccion_ejecutable:
                    self._ejecutar_sentencia_plsql(sentencia_nodo)
        except ErrorTiempoEjecucionPLSQL as e_block: 
            # --- MANEJO DE ERROR MEJORADO ---
            print(f"[DEBUG InterpretePLSQL] Error capturado en bloque BEGIN: {e_block}") # Imprimir el error original
            self.ultimo_error_runtime_mensaje = str(e_block) # Guardar para SQLERRM
            # --- FIN DE MANEJO DE ERROR MEJORADO ---
            if nodo_bloque.seccion_excepcion:
                self.visitar_NodoSeccionExcepcionPLSQL(nodo_bloque.seccion_excepcion, e_block)
            else:
                raise # Re-lanzar si no hay manejador de excepciones
        except ErrorRetornoPLSQL:
            raise
        finally: # Asegurar que el alcance se restaure incluso si hay una excepción no capturada
            self.alcance_actual = alcance_anterior

    def visitar_NodoDeclaracionVariablePLSQL(self, nodo_decl_var):
        nombre_variable = nodo_decl_var.nombre_variable_token.lexema
        # El tipo de dato (nodo_decl_var.tipo_dato_nodo) es más para validación estática.
        # En la simulación, el tipo se infiere del valor inicial o es dinámico.
        valor_inicial = None
        if nodo_decl_var.valor_inicial_nodo:
            valor_inicial = self._evaluar_expresion_plsql(nodo_decl_var.valor_inicial_nodo)
        
        self.alcance_actual.declarar(nombre_variable, valor_inicial)
        # print(f"Simulación: Variable '{nombre_variable}' declarada (tipo: {nodo_decl_var.tipo_dato_nodo.nombre_tipo_str}). Valor inicial: {repr(valor_inicial)}.")

    def _ejecutar_sentencia_plsql(self, nodo_sentencia):
        """Despachador para diferentes tipos de sentencias PL/SQL."""
        # print(f"[InterpretePLSQL DEBUG] Ejecutando sentencia: {type(nodo_sentencia).__name__}")
        if isinstance(nodo_sentencia, NodoSentenciaAsignacionPLSQL):
            self.visitar_NodoSentenciaAsignacionPLSQL(nodo_sentencia)
        elif isinstance(nodo_sentencia, NodoLlamadaProcedimientoPLSQL):
            self.visitar_NodoLlamadaProcedimientoPLSQL(nodo_sentencia)
        elif isinstance(nodo_sentencia, NodoSentenciaLoopPLSQL):
            self.visitar_NodoSentenciaLoopPLSQL(nodo_sentencia)
        elif isinstance(nodo_sentencia, NodoSentenciaForLoopPLSQL):
            self.visitar_NodoSentenciaForLoopPLSQL(nodo_sentencia)
        elif isinstance(nodo_sentencia, NodoSentenciaExitWhenPLSQL):
            # Esto debería ser manejado dentro del contexto de un bucle.
            # Por ahora, si se encuentra fuera, podría ser un error o ignorado.
            print(f"Advertencia (InterpretePLSQL): EXIT WHEN fuera de un LOOP no implementado completamente.")
        elif isinstance(nodo_sentencia, NodoSentenciaIfPLSQL):
            self.visitar_NodoSentenciaIfPLSQL(nodo_sentencia)
        elif isinstance(nodo_sentencia, NodoBloquePLSQL):
            self.visitar_NodoBloquePLSQL(nodo_sentencia)
        elif isinstance(nodo_sentencia, NodoSentenciaRaisePLSQL):
            self.visitar_NodoSentenciaRaisePLSQL(nodo_sentencia)
        # (Añadir más tipos de sentencias: FOR, WHILE, RETURN, etc.)
        elif nodo_sentencia is None: # Puede ser por un ; vacío
            pass
        else:
            print(f"Advertencia (InterpretePLSQL): Ejecución para sentencia PL/SQL '{type(nodo_sentencia).__name__}' no implementada.")

    def visitar_NodoSentenciaAsignacionPLSQL(self, nodo_asignacion):
        nombre_variable = None
        if isinstance(nodo_asignacion.variable_nodo, NodoIdentificadorPLSQL):
            nombre_variable = nodo_asignacion.variable_nodo.nombre
        # (Aquí se manejaría si variable_nodo es un NodoMiembroExpresionPLSQL para record.campo := ...)
        else:
            raise ErrorTiempoEjecucionPLSQL("Lado izquierdo de asignación PL/SQL no es un identificador simple.")

        valor_expresion = self._evaluar_expresion_plsql(nodo_asignacion.expresion_nodo)
        self.alcance_actual.asignar(nombre_variable, valor_expresion)
        # print(f"Simulación: Variable '{nombre_variable}' asignada a {repr(valor_expresion)}.")
    
    def visitar_NodoLlamadaProcedimientoPLSQL(self, nodo_llamada):
        # print(f"[InterpretePLSQL DEBUG] Visitando NodoLlamadaProcedimientoPLSQL. Callee: {nodo_llamada.callee_nodo}")
        
        # Evaluar el callee para obtener el objeto función/procedimiento
        # Puede ser un identificador simple o un miembro (paquete.procedimiento)
        callee_obj = self._evaluar_expresion_plsql(nodo_llamada.callee_nodo)
        
        # Evaluar argumentos
        argumentos_evaluados = []
        if nodo_llamada.argumentos_nodos:
            for arg_nodo in nodo_llamada.argumentos_nodos:
                argumentos_evaluados.append(self._evaluar_expresion_plsql(arg_nodo))
        
        if callable(callee_obj):
            try:
                callee_obj(*argumentos_evaluados) # Llamar a la función Python simulada
            except TypeError as te:
                 # Intentar obtener el nombre del callee para un mejor mensaje de error
                nombre_callee = "desconocido"
                if isinstance(nodo_llamada.callee_nodo, NodoIdentificadorPLSQL):
                    nombre_callee = nodo_llamada.callee_nodo.nombre
                elif isinstance(nodo_llamada.callee_nodo, NodoMiembroExpresionPLSQL):
                    nombre_callee = f"{nodo_llamada.callee_nodo.objeto_nodo.nombre}.{nodo_llamada.callee_nodo.nombre_miembro}"
                raise ErrorTiempoEjecucionPLSQL(f"Error al llamar a '{nombre_callee}': {te}")
        else:
            raise ErrorTiempoEjecucionPLSQL(f"'{nodo_llamada.callee_nodo}' no es un procedimiento o función llamable.")

    def visitar_NodoSentenciaLoopPLSQL(self, nodo_loop):
        # print(f"[InterpretePLSQL DEBUG] Entrando a LOOP.")
        # Para un LOOP simple, necesitamos un EXIT WHEN para salir.
        # Un intérprete más completo manejaría un contador de iteraciones máximo para evitar bucles infinitos.
        iteraciones_max = 1000 # Límite de seguridad
        iter_count = 0
        while iter_count < iteraciones_max:
            iter_count += 1
            try:
                # Cada iteración del cuerpo del bucle podría necesitar su propio sub-alcance si se declaran variables
                # dentro de él, pero PL/SQL no tiene declaración de variables a mitad de un bloque ejecutable.
                # El alcance del bloque LOOP es el mismo que el del bloque que lo contiene.
                for sentencia_nodo in nodo_loop.cuerpo_sentencias:
                    # Manejo especial para EXIT WHEN dentro del bucle
                    if isinstance(sentencia_nodo, NodoSentenciaExitWhenPLSQL):
                        condicion_exit = self._evaluar_expresion_plsql(sentencia_nodo.condicion_nodo)
                        if bool(condicion_exit):
                            # print(f"[InterpretePLSQL DEBUG] Condición EXIT WHEN verdadera. Saliendo de LOOP.")
                            return # Salir del método visitar_NodoSentenciaLoopPLSQL
                    else:
                        self._ejecutar_sentencia_plsql(sentencia_nodo)
            except ErrorRetornoPLSQL: # RETURN dentro de un LOOP sale del subprograma
                raise 
        
        if iter_count >= iteraciones_max:
            print(f"Advertencia (InterpretePLSQL): Bucle LOOP alcanzó el límite de {iteraciones_max} iteraciones.")
        # print(f"[InterpretePLSQL DEBUG] Saliendo de LOOP.")


    def visitar_NodoSentenciaIfPLSQL(self, nodo_if):
        # print(f"[InterpretePLSQL DEBUG] Visitando NodoSentenciaIfPLSQL.")
        rama_ejecutada = False
        for condicion_nodo, cuerpo_sentencias_nodos in nodo_if.casos_if_elsif:
            valor_condicion = self._evaluar_expresion_plsql(condicion_nodo)
            if bool(valor_condicion):
                # print(f"[InterpretePLSQL DEBUG] Condición IF/ELSIF verdadera. Ejecutando rama.")
                # El cuerpo de IF/ELSIF es una lista de sentencias.
                # Se ejecutan en el alcance actual.
                for stmt_nodo in cuerpo_sentencias_nodos:
                    self._ejecutar_sentencia_plsql(stmt_nodo)
                rama_ejecutada = True
                break
        
        if not rama_ejecutada and nodo_if.cuerpo_else:
            # print(f"[InterpretePLSQL DEBUG] Ninguna condición IF/ELSIF fue verdadera. Ejecutando rama ELSE.")
            for stmt_nodo in nodo_if.cuerpo_else:
                self._ejecutar_sentencia_plsql(stmt_nodo)
        # else:
            # if not rama_ejecutada:
                # print(f"[InterpretePLSQL DEBUG] Ninguna condición IF/ELSIF fue verdadera. No hay rama ELSE.")


    def visitar_NodoSeccionExcepcionPLSQL(self, nodo_seccion_ex, excepcion_original):
        # print(f"[InterpretePLSQL DEBUG] Entrando a sección EXCEPTION. Error original: {excepcion_original}")
        manejado = False
        for clausula_when in nodo_seccion_ex.clausulas_when:
            # Por ahora, solo manejamos WHEN OTHERS de forma genérica.
            # Una implementación completa compararía el tipo de excepcion_original
            # con los nombres_excepcion_tokens de la cláusula.
            es_others = any(t.lexema.lower() == 'others' for t in clausula_when.nombres_excepcion_tokens)
            es_nombre = any(t.lexema.lower() in str(excepcion_original).lower() for t in clausula_when.nombres_excepcion_tokens)
            if es_others or es_nombre: # Si es WHEN OTHERS, siempre coincide si no se manejó antes.
                # print(f"[InterpretePLSQL DEBUG] Manejador WHEN OTHERS encontrado.")
                for stmt_nodo in clausula_when.cuerpo_sentencias_nodos:
                    self._ejecutar_sentencia_plsql(stmt_nodo)
                manejado = True
                break # OTHERS debe ser el último y solo se ejecuta uno.
            # (Aquí iría la lógica para WHEN nombre_excepcion)
        
        if not manejado:
            # print(f"[InterpretePLSQL DEBUG] Excepción no manejada por cláusulas WHEN. Re-lanzando.")
            raise excepcion_original # Re-lanzar si ninguna cláusula WHEN la manejó

    def visitar_NodoSelect(self, nodo_select):
        # Simulación muy básica de SELECT
        # print(f"[InterpretePLSQL DEBUG] Visitando NodoSelect FROM {nodo_select.tabla_from_token.lexema}")
        # Por ahora, solo imprimimos un mensaje. No ejecutamos la consulta.
        columnas_str = ", ".join([c.id_token.lexema if isinstance(c, NodoIdentificadorPLSQL) else "*" for c in nodo_select.columnas_select_nodos])
        print(f"Simulación: SELECT {columnas_str} FROM {nodo_select.tabla_from_token.lexema} (no ejecutado).")
        return None # SELECT en PL/SQL a menudo usa INTO o es un cursor.

    # --- Métodos para evaluar expresiones PL/SQL ---
    def _evaluar_expresion_plsql(self, nodo_expr):
        # print(f"[InterpretePLSQL DEBUG] Evaluando expresión: {type(nodo_expr).__name__}")
        if isinstance(nodo_expr, NodoLiteralPLSQL):
            return nodo_expr.valor
        elif isinstance(nodo_expr, NodoIdentificadorPLSQL):
            # Soporte especial para SYSDATE
            if nodo_expr.nombre.lower() == 'sysdate':
                from datetime import datetime
                return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if nodo_expr.nombre.lower() == 'sqlerrm':
                return self._simular_sqlerrm()
            return self.alcance_actual.obtener(nodo_expr.nombre)
        elif isinstance(nodo_expr, NodoExpresionBinariaPLSQL):
            val_izq = self._evaluar_expresion_plsql(nodo_expr.izquierda_nodo)
            val_der = self._evaluar_expresion_plsql(nodo_expr.derecha_nodo)
            op = nodo_expr.operador_token.lexema.lower() 
            tipo_op = nodo_expr.operador_token.tipo

            if tipo_op == TT_OPERADOR_ARITMETICO_PLSQL or op == '*': 
                if op == '+': return val_izq + val_der 
                if op == '-': return val_izq - val_der
                if op == '*': return val_izq * val_der
                if op == '/': 
                    if val_der == 0: raise ErrorTiempoEjecucionPLSQL("División por cero.")
                    return val_izq / val_der 
                if op == '**': return val_izq ** val_der
            elif tipo_op == TT_OPERADOR_CONCATENACION_PLSQL and op == '||':
                return str(val_izq) + str(val_der)
            elif tipo_op == TT_OPERADOR_COMPARACION_PLSQL:
                if op == '=': return val_izq == val_der
                if op == '!=' or op == '<>' or op == '^=': return val_izq != val_der
                if op == '<': return val_izq < val_der
                if op == '>': return val_izq > val_der
                if op == '<=': return val_izq <= val_der
                if op == '>=': return val_izq >= val_der
                if op == 'is null': return val_izq is None
                if op == 'is not null': return val_izq is not None
            elif tipo_op == TT_OPERADOR_LOGICO_PLSQL: 
                if op == 'and': return bool(val_izq) and bool(val_der)
                if op == 'or': return bool(val_izq) or bool(val_der)
            
            raise ErrorTiempoEjecucionPLSQL(f"Operador binario PL/SQL '{op}' no soportado en evaluación.")
        
        elif isinstance(nodo_expr, NodoExpresionUnariaPLSQL): 
            op = nodo_expr.operador_token.lexema.lower()
            operando_val = self._evaluar_expresion_plsql(nodo_expr.operando_nodo)
            if op == 'not':
                return not bool(operando_val)
            elif op == '-':
                return -operando_val
            elif op == '+':
                return +operando_val
            raise ErrorTiempoEjecucionPLSQL(f"Operador unario PL/SQL '{op}' no soportado.")

        elif isinstance(nodo_expr, NodoFuncionSQL): 
            nombre_func = nodo_expr.nombre_funcion_token.lexema.lower()
            args_evaluados = [self._evaluar_expresion_plsql(arg) for arg in nodo_expr.argumentos_nodos]
            
            if nombre_func == 'sysdate':
                from datetime import datetime
                return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if nombre_func in self.paquetes_incorporados and callable(self.paquetes_incorporados[nombre_func]):
                return self.paquetes_incorporados[nombre_func](*args_evaluados)
            # Soporte para funciones simuladas
            if nombre_func == 'sysdate':
                return self._simular_sysdate()
            if nombre_func == 'nvl':
                return self._simular_nvl(*args_evaluados)
            if nombre_func == 'chr':
                return self._simular_chr(*args_evaluados)
            if nombre_func == 'sqlerrm':
                return self._simular_sqlerrm()
            if nombre_func == 'raise_application_error':
                # Simula RAISE_APPLICATION_ERROR(-20001, 'mensaje')
                if len(args_evaluados) >= 2:
                    codigo = args_evaluados[0]
                    mensaje = args_evaluados[1]
                    raise ErrorTiempoEjecucionPLSQL(f"RAISE_APPLICATION_ERROR {codigo}: {mensaje}")
                else:
                    raise ErrorTiempoEjecucionPLSQL("RAISE_APPLICATION_ERROR requiere al menos dos argumentos.")
            else:
                raise ErrorTiempoEjecucionPLSQL(f"Función PL/SQL desconocida: '{nombre_func}'.")
        
        elif isinstance(nodo_expr, NodoMiembroExpresionPLSQL): 
            objeto_nombre = nodo_expr.objeto_nodo.nombre.lower()
            miembro_nombre = nodo_expr.nombre_miembro.lower()

            if objeto_nombre in self.paquetes_incorporados:
                paquete = self.paquetes_incorporados[objeto_nombre]
                if isinstance(paquete, dict) and miembro_nombre in paquete:
                    if callable(paquete[miembro_nombre]):
                        return paquete[miembro_nombre] 
                    else:
                        return paquete[miembro_nombre] 
                else:
                    raise ErrorTiempoEjecucionPLSQL(f"Miembro '{miembro_nombre}' no encontrado en paquete '{objeto_nombre}'.")
            else:
                raise ErrorTiempoEjecucionPLSQL(f"Paquete o record '{objeto_nombre}' no reconocido.")

        else:
            raise ErrorTiempoEjecucionPLSQL(f"Tipo de nodo de expresión PL/SQL '{type(nodo_expr).__name__}' no soportado para evaluación.")
        return None 
        
    # --- SUGERENCIAS IMPLEMENTADAS ---
    # 1. Simulación básica de FOR LOOP (solo rango numérico)
    def visitar_NodoSentenciaForLoopPLSQL(self, nodo_for):
        # Simula la ejecución de un bucle FOR numérico PL/SQL
        var_name = nodo_for.variable_iteracion_token.lexema
        inicio = self._evaluar_expresion_plsql(nodo_for.expresion_inicio_nodo)
        fin = self._evaluar_expresion_plsql(nodo_for.expresion_fin_nodo)
        es_reverse = nodo_for.es_reverse
        # PL/SQL: el rango es inclusivo
        if es_reverse:
            rango = range(inicio, fin - 1, -1)
        else:
            rango = range(inicio, fin + 1)
        alcance_anterior = self.alcance_actual
        self.alcance_actual = AlcancePLSQL(padre=alcance_anterior, nombre_alcance=f"for_loop_{var_name}")
        self.alcance_actual.objetos_globales_plsql_ref = self.paquetes_incorporados
        try:
            for i in rango:
                self.alcance_actual.declarar(var_name, i)
                for stmt in nodo_for.cuerpo_sentencias_nodos:
                    # Soporte para EXIT WHEN dentro del FOR
                    if hasattr(stmt, 'condicion_nodo'):
                        if stmt.__class__.__name__ == 'NodoSentenciaExitWhenPLSQL':
                            condicion_exit = self._evaluar_expresion_plsql(stmt.condicion_nodo)
                            if bool(condicion_exit):
                                return
                    self._ejecutar_sentencia_plsql(stmt)
        finally:
            self.alcance_actual = alcance_anterior

    # 2. Simulación de excepción personalizada y RAISE
    def _simular_raise(self, nombre_excepcion=None):
        if nombre_excepcion:
            raise ErrorTiempoEjecucionPLSQL(f"Excepción personalizada lanzada: {nombre_excepcion}")
        else:
            raise ErrorTiempoEjecucionPLSQL("Excepción lanzada con RAISE;")

    # 3. Simulación de función SYSDATE
    def _simular_sysdate(self):
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 4. Simulación de función NVL
    def _simular_nvl(self, valor, valor_si_null):
        return valor if valor is not None else valor_si_null

    # 5. Simulación de SELECT INTO (muy básica)
    def visitar_NodoSelectInto(self, nodo_select):
        # Solo simula SELECT ... INTO variable FROM DUAL;
        if hasattr(nodo_select, 'into_clausula_nodos') and nodo_select.into_clausula_nodos:
            for var_nodo in nodo_select.into_clausula_nodos:
                self.alcance_actual.declarar(var_nodo.id_token.lexema, 'Simulado')
        print("Simulación: SELECT INTO ejecutado (valores simulados)")

    # 6. Simulación de manejo de excepciones por nombre
    def visitar_NodoSeccionExcepcionPLSQL(self, nodo_seccion_ex, excepcion_original):
        manejado = False
        for clausula_when in nodo_seccion_ex.clausulas_when:
            es_others = any(t.lexema.lower() == 'others' for t in clausula_when.nombres_excepcion_tokens)
            es_nombre = any(t.lexema.lower() in str(excepcion_original).lower() for t in clausula_when.nombres_excepcion_tokens)
            if es_others or es_nombre:
                for stmt_nodo in clausula_when.cuerpo_sentencias_nodos:
                    self._ejecutar_sentencia_plsql(stmt_nodo)
                manejado = True
                break
        if not manejado:
            raise excepcion_original

    # 7. Simulación de función CHR
    def _simular_chr(self, n):
        return chr(int(n))

    # 8. Simulación de SQLERRM (devuelve el último error)
    def _simular_sqlerrm(self):
        return getattr(self, 'ultimo_error_runtime_mensaje', 'No hay error.')

    def visitar_NodoSentenciaRaisePLSQL(self, nodo_raise):
        # Ejecuta la sentencia RAISE (con o sin nombre de excepción)
        if hasattr(nodo_raise, 'nombre_excepcion_token') and nodo_raise.nombre_excepcion_token:
            self._simular_raise(nodo_raise.nombre_excepcion_token.lexema)
        else:
            self._simular_raise()

    # --- FIN SUGERENCIAS ---

# Fin de la clase InterpretePLSQL

# # src/simulador_ejecucion/interprete_plsql.py
# import re 

# # Importar las clases de nodos AST necesarias desde el parser_plsql.
# try:
#     from analizador_sintactico.parser_plsql import (
#         NodoScriptPLSQL, NodoBloquePLSQL, NodoDeclaracionVariablePLSQL, NodoTipoDatoPLSQL,
#         NodoSentenciaPLSQL, NodoSentenciaAsignacionPLSQL, NodoLlamadaProcedimientoPLSQL,
#         NodoSentenciaLoopPLSQL, NodoSentenciaExitWhenPLSQL, NodoSentenciaIfPLSQL,
#         NodoSeccionExcepcionPLSQL, NodoClausulaWhenPLSQL, NodoSentenciaForLoopPLSQL, # <-- AÑADIDO
#         NodoExpresionPLSQL, NodoIdentificadorPLSQL, NodoLiteralPLSQL, 
#         NodoExpresionBinariaPLSQL, NodoMiembroExpresionPLSQL, NodoFuncionSQL, NodoSelect,
#         NodoAsteriscoSQL, NodoExpresionUnariaPLSQL 
#     )
#     # Importar tipos de token si son necesarios para la evaluación.
#     from analizador_lexico.lexer_plsql import Token, TT_OPERADOR_CONCATENACION_PLSQL, \
#                                                TT_OPERADOR_ARITMETICO_PLSQL, TT_OPERADOR_COMPARACION_PLSQL, \
#                                                TT_OPERADOR_LOGICO_PLSQL, TT_LITERAL_CADENA_PLSQL, \
#                                                TT_LITERAL_NUMERICO_PLSQL, TT_LITERAL_BOOLEANO_PLSQL, \
#                                                TT_LITERAL_NULL_PLSQL, TT_ASTERISCO, IDENTIFIER_LIKE_KEYWORDS_PLSQL
# except ImportError as e_import_ast_interprete_plsql:
#     print(f"ADVERTENCIA CRÍTICA (InterpretePLSQL): No se pudieron importar los nodos AST desde 'parser_plsql.py'. Error: {e_import_ast_interprete_plsql}")
#     # Definir placeholders muy básicos
#     class NodoScriptPLSQL: pass; 
#     class NodoBloquePLSQL: pass; 
#     class NodoDeclaracionVariablePLSQL: pass
#     class NodoTipoDatoPLSQL: pass; 
#     class NodoSentenciaPLSQL: pass; 
#     class NodoSentenciaAsignacionPLSQL: pass
#     class NodoLlamadaProcedimientoPLSQL: pass; 
#     class NodoSentenciaLoopPLSQL: pass; 
#     class NodoSentenciaExitWhenPLSQL: pass
#     class NodoSentenciaIfPLSQL: pass; 
#     class NodoSeccionExcepcionPLSQL: pass; 
#     class NodoClausulaWhenPLSQL: pass
#     class NodoSentenciaForLoopPLSQL: pass # <-- AÑADIDO
#     class NodoExpresionPLSQL: pass; 
#     class NodoIdentificadorPLSQL: pass; 
#     class NodoLiteralPLSQL: pass
#     class NodoExpresionBinariaPLSQL: pass; 
#     class NodoMiembroExpresionPLSQL: pass; 
#     class NodoFuncionSQL: pass; 
#     class NodoSelect: pass
#     class NodoAsteriscoSQL: pass; 
#     class NodoExpresionUnariaPLSQL: pass 
#     class Token: pass; 
#     TT_OPERADOR_CONCATENACION_PLSQL = "OP_CONCAT_PLSQL"; TT_OPERADOR_ARITMETICO_PLSQL = "OP_ARIT_PLSQL"
#     TT_OPERADOR_COMPARACION_PLSQL = "OP_COMP_PLSQL"; TT_OPERADOR_LOGICO_PLSQL = "OP_LOG_PLSQL"
#     TT_LITERAL_CADENA_PLSQL, TT_LITERAL_NUMERICO_PLSQL, TT_LITERAL_BOOLEANO_PLSQL, TT_LITERAL_NULL_PLSQL = "LIT_STR", "LIT_NUM", "LIT_BOOL", "LIT_NULL"
#     TT_ASTERISCO = "ASTERISCO_PLSQL"; IDENTIFIER_LIKE_KEYWORDS_PLSQL = set()


# # Excepción personalizada para errores en tiempo de ejecución del intérprete de PL/SQL
# class ErrorTiempoEjecucionPLSQL(RuntimeError):
#     """Error general en tiempo de ejecución para el intérprete de PL/SQL."""
#     pass

# class ErrorRetornoPLSQL(Exception): # Para RETURN en funciones PL/SQL (si se implementan)
#     def __init__(#         super().__init__("Sentencia RETURN ejecutada")
#         self.valor = valor

# # --- Excepciones para control de bucles (si se implementan break/continue para PL/SQL) ---
# # class BreakPLSQLException(Exception): pass
# # class ContinuePLSQLException(Exception): pass

# class AlcancePLSQL:
#     """Representa un alcance (scope) en PL/SQL para almacenar variables y otros símbolos."""
#     def __init__(self, padre=None, nombre_alcance="global"):
#         self.simbolos = {}  # Almacena variables, constantes, cursores, tipos, etc.
#         self.padre = padre
#         self.nombre_alcance = nombre_alcance
#         self.objetos_globales_plsql_ref = None 

#     def declarar(self, nombre_simbolo, valor, tipo_simbolo="variable"):
#         nombre_lower = nombre_simbolo.lower() 
#         if nombre_lower in self.simbolos y tipo_simbolo != "usado_de_namespace" y self.nombre_alcance != f"for_loop_var_{nombre_lower}": # Permitir shadowing de variable de bucle FOR
#             print(f"Advertencia (AlcancePLSQL): Redeclaración del símbolo '{nombre_lower}' en el mismo alcance '{self.nombre_alcance}'.")
#         self.simbolos[nombre_lower] = {'valor': valor, 'tipo_simbolo': tipo_simbolo}

#     def asignar(self, nombre_simbolo, valor):
#         nombre_lower = nombre_simbolo.lower()
#         alcance_busqueda = self
#         while alcance_busqueda:
#             if nombre_lower in alcance_busqueda.simbolos y alcance_busqueda.simbolos[nombre_lower]['tipo_simbolo'] == "variable":
#                 alcance_busqueda.simbolos[nombre_lower]['valor'] = valor
#                 return
#             alcance_busqueda = alcance_busqueda.padre
#         raise ErrorTiempoEjecucionPLSQL(f"Variable no declarada '{nombre_simbolo}'.")

#     def obtener(self, nombre_simbolo):
#         nombre_lower = nombre_simbolo.lower()
#         alcance_busqueda = self
#         while alcance_busqueda:
#             if nombre_lower in alcance_busqueda.simbolos:
#                 return alcance_busqueda.simbolos[nombre_lower]['valor']
#             alcance_busqueda = alcance_busqueda.padre
        
#         if self.objetos_globales_plsql_ref:
#             if nombre_lower in self.objetos_globales_plsql_ref:
#                 return self.objetos_globales_plsql_ref[nombre_lower]
#             partes = nombre_lower.split('.')
#             if len(partes) == 2 y partes[0] in self.objetos_globales_plsql_ref:
#                 paquete = self.objetos_globales_plsql_ref[partes[0]]
#                 if isinstance(paquete, dict) y partes[1] in paquete:
#                     return paquete[partes[1]]
        
#         raise ErrorTiempoEjecucionPLSQL(f"Símbolo no declarado '{nombre_simbolo}'.")

# class FuncionDefinidaPLSQL: # Similar a FuncionDefinidaPython, para futura expansión
#     def __init__(self, nombre_token, parametros_nodos, cuerpo_nodo, alcance_definicion):
#         self.nombre = nombre_token.lexema
#         # self.nombres_parametros = [p.nombre_param_token.lexema para p in parametros_nodos si p.nombre_param_token]
#         self.cuerpo_nodo = cuerpo_nodo
#         self.alcance_definicion = alcance_definicion

#     def __repr__(self):
#         return f"<FuncionPLSQL: {self.nombre}>"


# class InterpretePLSQL:
#     def __init__(self):
#         self.alcance_global = AlcancePLSQL(nombre_alcance="script_global")
#         self.alcance_actual = self.alcance_global
#         self.ultimo_error_runtime_mensaje = "No hay error." 

#         self.paquetes_incorporados = {
#             'dbms_output': {
#                 'put_line': self._simular_dbms_output_put_line
#             },
#             'to_char': self._simular_to_char,
#             'chr': self._simular_chr,
#             'sqlerrm': self._simular_sqlerrm 
#         }
#         para nombre, obj en self.paquetes_incorporados.items():
#             self.alcance_global.declarar(nombre, obj, tipo_simbolo="paquete_o_funcion_incorporada")
#         self.alcance_global.objetos_globales_plsql_ref = self.paquetes_incorporados 
#         self.buffer_cout = [] 

#     def _simular_dbms_output_put_line(self, *args):
#         si args:
#             self.buffer_cout.append(str(args[0]))
#         si args y args[0] == "\n": 
#             print("".join(self.buffer_cout)) 
#             self.buffer_cout = []
#         elif args y isinstance(args[0], str) y "\n" en args[0]: 
#              partes = args[0].split("\n")
#              para i, parte en enumerate(partes):
#                  self.buffer_cout.append(parte)
#                  si i < len(partes) -1 : 
#                      print("".join(self.buffer_cout))
#                      self.buffer_cout = []
#         return None 

#     def _simular_to_char(self, *args):
#         si no args:
#             raise ErrorTiempoEjecucionPLSQL("TO_CHAR requiere al menos un argumento.")
#         return str(args[0])

#     def _simular_chr(self, *args):
#         si no args o no isinstance(args[0], int):
#             raise ErrorTiempoEjecucionPLSQL("CHR requiere un argumento numérico entero.")
#         try:
#             si args[0] == 10: return "\n"
#             elif args[0] == 13: return "\r"
#             return chr(args[0])
#         except ValueError:
#             raise ErrorTiempoEjecucionPLSQL(f"Valor inválido para la función CHR: {args[0]}")
            
#     def _simular_sqlerrm(self, *args): 
#         return self.ultimo_error_runtime_mensaje


#     def interpretar_script(self, nodo_script):
#         si no isinstance(nodo_script, NodoScriptPLSQL):
#             print("Error del Intérprete PL/SQL: Se esperaba un NodoScriptPLSQL.")
#             return
        
#         print("\n--- Iniciando Simulación de Ejecución (PL/SQL) ---")
#         try:
#             para elemento en nodo_script.elementos:
#                 si isinstance(elemento, NodoBloquePLSQL):
#                     self.visitar_NodoBloquePLSQL(elemento)
#                 elif isinstance(elemento, NodoSelect): 
#                     self.visitar_NodoSelect(elemento) 
#                 else:
#                     print(f"Advertencia (InterpretePLSQL): Tipo de elemento de script '{type(elemento).__name__}' no manejado.")
#         except ErrorTiempoEjecucionPLSQL as e_runtime:
#             print(f"Error en Tiempo de Ejecución (PL/SQL): {e_runtime}") 
#         except ErrorRetornoPLSQL as e_return: 
#             print(f"Advertencia (InterpretePLSQL): Sentencia RETURN fuera de una función: valor {e_return.valor}")
#         except Exception as e_general:
#             print(f"Error Inesperado durante la Interpretación de PL/SQL: {e_general}")
#             import traceback
#             traceback.print_exc()
#         finally:
#             si self.buffer_cout:
#                 print("".join(self.buffer_cout))
#                 self.buffer_cout = []
#             print("--- Simulación de Ejecución Finalizada (PL/SQL) ---")

#     def visitar_NodoBloquePLSQL(self, nodo_bloque):
#         alcance_anterior = self.alcance_actual
#         self.alcance_actual = AlcancePLSQL(padre=alcance_anterior, nombre_alcance=f"bloque_{id(nodo_bloque)}")
#         self.alcance_actual.objetos_globales_plsql_ref = self.paquetes_incorporados 

#         si nodo_bloque.seccion_declaracion:
#             para declaracion_var_nodo en nodo_bloque.seccion_declaracion:
#                 self.visitar_NodoDeclaracionVariablePLSQL(declaracion_var_nodo)
        
#         try:
#             si nodo_bloque.seccion_ejecutable:
#                 para sentencia_nodo en nodo_bloque.seccion_ejecutable:
#                     self._ejecutar_sentencia_plsql(sentencia_nodo)
#         except ErrorTiempoEjecucionPLSQL as e_block: 
#             # print(f"[DEBUG InterpretePLSQL] Error capturado en bloque BEGIN: {e_block}") 
#             self.ultimo_error_runtime_mensaje = str(e_block) 
#             si nodo_bloque.seccion_excepcion:
#                 self.visitar_NodoSeccionExcepcionPLSQL(nodo_bloque.seccion_excepcion, e_block)
#             else:
#                 raise 
#         except ErrorRetornoPLSQL:
#             raise
#         finally: 
#             self.alcance_actual = alcance_anterior

#     def visitar_NodoDeclaracionVariablePLSQL(self, nodo_decl_var):
#         nombre_variable = nodo_decl_var.nombre_variable_token.lexema
#         valor_inicial = None
#         si nodo_decl_var.valor_inicial_nodo:
#             valor_inicial = self._evaluar_expresion_plsql(nodo_decl_var.valor_inicial_nodo)
#         self.alcance_actual.declarar(nombre_variable, valor_inicial)

#     # --- MÉTODO _ejecutar_sentencia_plsql ACTUALIZADO ---
#     def _ejecutar_sentencia_plsql(self, nodo_sentencia):
#         si isinstance(nodo_sentencia, NodoSentenciaAsignacionPLSQL):
#             self.visitar_NodoSentenciaAsignacionPLSQL(nodo_sentencia)
#         elif isinstance(nodo_sentencia, NodoLlamadaProcedimientoPLSQL):
#             self.visitar_NodoLlamadaProcedimientoPLSQL(nodo_sentencia)
#         elif isinstance(nodo_sentencia, NodoSentenciaLoopPLSQL):
#             self.visitar_NodoSentenciaLoopPLSQL(nodo_sentencia)
#         elif isinstance(nodo_sentencia, NodoSentenciaExitWhenPLSQL):
#             raise ErrorTiempoEjecucionPLSQL("Sentencia EXIT WHEN encontrada fuera de un bucle (manejo directo no implementado aquí).")
#         elif isinstance(nodo_sentencia, NodoSentenciaIfPLSQL):
#             self.visitar_NodoSentenciaIfPLSQL(nodo_sentencia)
#         elif isinstance(nodo_sentencia, NodoSentenciaForLoopPLSQL): # <-- NUEVA LLAMADA
#             self.visitar_NodoSentenciaForLoopPLSQL(nodo_sentencia)
#         elif nodo_sentencia is None: 
#             pass
#         else:
#             print(f"Advertencia (InterpretePLSQL): Ejecución para sentencia PL/SQL '{type(nodo_sentencia).__name__}' no implementada.")
#     # --- FIN DE MÉTODO ACTUALIZADO ---

#     def visitar_NodoSentenciaAsignacionPLSQL(self, nodo_asignacion):
#         nombre_variable = None
#         si isinstance(nodo_asignacion.variable_nodo, NodoIdentificadorPLSQL):
#             nombre_variable = nodo_asignacion.variable_nodo.nombre
#         else:
#             raise ErrorTiempoEjecucionPLSQL("Lado izquierdo de asignación PL/SQL no es un identificador simple.")
#         valor_expresion = self._evaluar_expresion_plsql(nodo_asignacion.expresion_nodo)
#         self.alcance_actual.asignar(nombre_variable, valor_expresion)
    
#     def visitar_NodoLlamadaProcedimientoPLSQL(self, nodo_llamada):
#         callee_obj = self._evaluar_expresion_plsql(nodo_llamada.callee_nodo)
#         argumentos_evaluados = []
#         si nodo_llamada.argumentos_nodos:
#             para arg_nodo en nodo_llamada.argumentos_nodos:
#                 argumentos_evaluados.append(self._evaluar_expresion_plsql(arg_nodo))
#         si callable(callee_obj):
#             try:
#                 callee_obj(*argumentos_evaluados) 
#             except TypeError as te:
#                 nombre_callee = "desconocido"
#                 si isinstance(nodo_llamada.callee_nodo, NodoIdentificadorPLSQL):
#                     nombre_callee = nodo_llamada.callee_nodo.nombre
#                 elif isinstance(nodo_llamada.callee_nodo, NodoMiembroExpresionPLSQL):
#                     nombre_callee = f"{nodo_llamada.callee_nodo.objeto_nodo.nombre}.{nodo_llamada.callee_nodo.nombre_miembro}"
#                 raise ErrorTiempoEjecucionPLSQL(f"Error al llamar a '{nombre_callee}': {te}")
#         else:
#             raise ErrorTiempoEjecucionPLSQL(f"'{nodo_llamada.callee_nodo}' no es un procedimiento o función llamable.")

#     def visitar_NodoSentenciaLoopPLSQL(self, nodo_loop):
#         iteraciones_max = 1000 
#         iter_count = 0
#         try:
#             mientras iter_count < iteraciones_max:
#                 iter_count += 1
#                 para sentencia_nodo en nodo_loop.cuerpo_sentencias:
#                     si isinstance(sentencia_nodo, NodoSentenciaExitWhenPLSQL):
#                         condicion_exit = self._evaluar_expresion_plsql(sentencia_nodo.condicion_nodo)
#                         si bool(condicion_exit):
#                             return 
#                     else:
#                         self._ejecutar_sentencia_plsql(sentencia_nodo)
#         except ErrorRetornoPLSQL: 
#             raise 
#         si iter_count >= iteraciones_max:
#             print(f"Advertencia (InterpretePLSQL): Bucle LOOP alcanzó el límite de {iteraciones_max} iteraciones.")

#     def visitar_NodoSentenciaIfPLSQL(self, nodo_if):
#         rama_ejecutada = False
#         para condicion_nodo, cuerpo_sentencias_nodos en nodo_if.casos_if_elsif:
#             valor_condicion = self._evaluar_expresion_plsql(condicion_nodo)
#             si bool(valor_condicion):
#                 para stmt_nodo en cuerpo_sentencias_nodos:
#                     self._ejecutar_sentencia_plsql(stmt_nodo)
#                 rama_ejecutada = True
#                 break
#         si no rama_ejecutada y nodo_if.cuerpo_else:
#             para stmt_nodo en nodo_if.cuerpo_else:
#                 self._ejecutar_sentencia_plsql(stmt_nodo)

#     # --- NUEVO MÉTODO PARA VISITAR NodoSentenciaForLoopPLSQL ---
#     def visitar_NodoSentenciaForLoopPLSQL(self, nodo_for):
#         """Simula la ejecución de un bucle FOR numérico."""
#         # print(f"[InterpretePLSQL DEBUG] Visitando NodoSentenciaForLoopPLSQL: {nodo_for.variable_iteracion_token.lexema}")
        
#         nombre_var_iter = nodo_for.variable_iteracion_token.lexema.lower()
        
#         # Evaluar los límites del rango
#         valor_inicio = self._evaluar_expresion_plsql(nodo_for.expresion_inicio_nodo)
#         valor_fin = self._evaluar_expresion_plsql(nodo_for.expresion_fin_nodo)

#         si no (isinstance(valor_inicio, (int, float)) y isinstance(valor_fin, (int, float))):
#             raise ErrorTiempoEjecucionPLSQL("Límites del rango del bucle FOR deben ser numéricos.")

#         # Convertir a enteros para el rango (PL/SQL usa enteros para iteradores de bucle)
#         inicio = int(valor_inicio)
#         fin = int(valor_fin)

#         # La variable del bucle FOR es implícitamente declarada y es local al bucle.
#         # Creamos un nuevo alcance para el bucle.
#         alcance_anterior = self.alcance_actual
#         self.alcance_actual = AlcancePLSQL(padre=alcance_anterior, nombre_alcance=f"for_loop_{nombre_var_iter}")
#         self.alcance_actual.objetos_globales_plsql_ref = self.paquetes_incorporados


#         rango_iteracion = range(inicio, fin + 1)
#         si nodo_for.es_reverse:
#             rango_iteracion = range(inicio, fin - 1, -1) # De inicio a fin (descendente)

#         try:
#             para valor_iteracion en rango_iteracion:
#                 self.alcance_actual.declarar(nombre_var_iter, valor_iteracion) # Declarar/actualizar en cada iteración
                
#                 # Ejecutar el cuerpo del bucle
#                 para sentencia_nodo en nodo_for.cuerpo_sentencias_nodos:
#                     # Manejo de EXIT WHEN dentro del FOR
#                     si isinstance(sentencia_nodo, NodoSentenciaExitWhenPLSQL):
#                         condicion_exit = self._evaluar_expresion_plsql(sentencia_nodo.condicion_nodo)
#                         si bool(condicion_exit):
#                             # print(f"[InterpretePLSQL DEBUG] Condición EXIT WHEN verdadera en FOR. Saliendo.")
#                             self.alcance_actual = alcance_anterior # Restaurar alcance antes de salir
#                             return 
#                     else:
#                         self._ejecutar_sentencia_plsql(sentencia_nodo)
#         except ErrorRetornoPLSQL: # Un RETURN dentro del FOR sale del subprograma
#             self.alcance_actual = alcance_anterior
#             raise
#         finally: # Asegurar que el alcance se restaure
#             self.alcance_actual = alcance_anterior
        
#         # print(f"[InterpretePLSQL DEBUG] Saliendo de FOR loop: {nombre_var_iter}")
#         return None
#     # --- FIN DE NUEVO MÉTODO ---

#     def visitar_NodoSeccionExcepcionPLSQL(self, nodo_seccion_ex, excepcion_original=None):
#         manejado = False
#         para clausula_when en nodo_seccion_ex.clausulas_when:
#             es_others = any(t.lexema.lower() == 'others' para t en clausula_when.nombres_excepcion_tokens)
            
#             si es_others: 
#                 para stmt_nodo en clausula_when.cuerpo_sentencias_nodos:
#                     self._ejecutar_sentencia_plsql(stmt_nodo)
#                 manejado = True
#                 break 
#         si no manejado y excepcion_original: 
#             raise excepcion_original 

#     def visitar_NodoSelect(self, nodo_select):
#         columnas_str = ", ".join([c.id_token.lexema si isinstance(c, NodoIdentificadorPLSQL) else "*" para c en nodo_select.columnas_select_nodos])
#         tabla_str = nodo_select.tabla_from_token.lexema si nodo_select.tabla_from_token else "tabla_desconocida"
#         print(f"Simulación: SELECT {columnas_str} FROM {tabla_str} (no ejecutado).")
#         return None 

#     def _evaluar_expresion_plsql(self, nodo_expr):
#         # (Como estaba antes)
#         si isinstance(nodo_expr, NodoLiteralPLSQL):
#             si nodo_expr.literal_token.tipo == TT_LITERAL_CADENA_PLSQL y \
#                nodo_expr.literal_token.lexema.lower().startswith(('f"', "f'", 'rf"', "rf'", 'fr"', "fr'")): # Aunque no es estándar PLSQL
#                 formato_str = str(nodo_expr.valor) 
#                 def reemplazar_variable(match):
#                     nombre_variable = match.group(1).strip() 
#                     try:
#                         valor_variable = self.alcance_actual.obtener(nombre_variable)
#                         return str(valor_variable)
#                     except ErrorTiempoEjecucionPLSQL:
#                         return match.group(0) 
#                 resultado_interpolado = re.sub(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}', reemplazar_variable, formato_str)
#                 return resultado_interpolado
#             else:
#                 return nodo_expr.valor 
#         elif isinstance(nodo_expr, NodoIdentificadorPLSQL):
#             si nodo_expr.nombre.lower() == 'sqlerrm':
#                 return self._simular_sqlerrm()
#             return self.alcance_actual.obtener(nodo_expr.nombre)
#         elif isinstance(nodo_expr, NodoExpresionBinariaPLSQL):
#             val_izq = self._evaluar_expresion_plsql(nodo_expr.izquierda_nodo)
#             val_der = self._evaluar_expresion_plsql(nodo_expr.derecha_nodo)
#             op = nodo_expr.operador_token.lexema.lower() 
#             tipo_op = nodo_expr.operador_token.tipo
#             si tipo_op == TT_OPERADOR_ARITMETICO_PLSQL o op == '*': 
#                 si op == '+': return val_izq + val_der 
#                 si op == '-': return val_izq - val_der
#                 si op == '*': return val_izq * val_der
#                 si op == '/': 
#                     si val_der == 0: raise ErrorTiempoEjecucionPLSQL("División por cero.")
#                     return val_izq / val_der 
#                 si op == '**': return val_izq ** val_der
#             elif tipo_op == TT_OPERADOR_CONCATENACION_PLSQL y op == '||':
#                 return str(val_izq) + str(val_der)
#             elif tipo_op == TT_OPERADOR_COMPARACION_PLSQL:
#                 si op == '=': return val_izq == val_der
#                 si op == '!=' o op == '<>' o op == '^=': return val_izq != val_der
#                 si op == '<': return val_izq < val_der
#                 si op == '>': return val_izq > val_der
#                 si op == '<=': return val_izq <= val_der
#                 si op == '>=': return val_izq >= val_der
#                 si op == 'is null': return val_izq is None
#                 si op == 'is not null': return val_izq is not None
#             elif tipo_op == TT_OPERADOR_LOGICO_PLSQL: 
#                 si op == 'and': return bool(val_izq) y bool(val_der) 
#                 si op == 'or':  return bool(val_izq) o bool(val_der)  
#             raise ErrorTiempoEjecucionPLSQL(f"Operador binario PL/SQL '{op}' no soportado en evaluación.")
#         elif isinstance(nodo_expr, NodoExpresionUnariaPLSQL): 
#             op = nodo_expr.operador_token.lexema.lower()
#             operando_val = self._evaluar_expresion_plsql(nodo_expr.operando_nodo)
#             si op == 'not': return not bool(operando_val)
#             si op == '-': return -operando_val
#             si op == '+': return +operando_val 
#             raise ErrorTiempoEjecucionPLSQL(f"Operador unario PL/SQL '{op}' no soportado.")
#         elif isinstance(nodo_expr, NodoFuncionSQL): 
#             nombre_func = nodo_expr.nombre_funcion_token.lexema.lower()
#             args_evaluados = [self._evaluar_expresion_plsql(arg) para arg en nodo_expr.argumentos_nodos]
#             si nombre_func en self.paquetes_incorporados y callable(self.paquetes_incorporados[nombre_func]):
#                 return self.paquetes_incorporados[nombre_func](*args_evaluados)
#             else:
#                 try:
#                     func_obj = self.alcance_actual.obtener(nombre_func)
#                     si callable(func_obj): 
#                         return func_obj(*args_evaluados)
#                 except ErrorTiempoEjecucionPLSQL: pass 
#                 raise ErrorTiempoEjecucionPLSQL(f"Función PL/SQL desconocida o no implementada: '{nombre_func}'.")
#         elif isinstance(nodo_expr, NodoMiembroExpresionPLSQL): 
#             objeto_nombre = nodo_expr.objeto_nodo.nombre.lower()
#             miembro_nombre = nodo_expr.nombre_miembro.lower()
#             si objeto_nombre en self.paquetes_incorporados:
#                 paquete = self.paquetes_incorporados[objeto_nombre]
#                 si isinstance(paquete, dict) y miembro_nombre en paquete:
#                     si callable(paquete[miembro_nombre]): return paquete[miembro_nombre] 
#                     else: return paquete[miembro_nombre] 
#                 else: raise ErrorTiempoEjecucionPLSQL(f"Miembro '{miembro_nombre}' no encontrado en paquete '{objeto_nombre}'.")
#             else: raise ErrorTiempoEjecucionPLSQL(f"Paquete o record '{objeto_nombre}' no reconocido.")
#         else:
#             raise ErrorTiempoEjecucionPLSQL(f"Tipo de nodo de expresión PL/SQL '{type(nodo_expr).__name__}' no soportado para evaluación.")
#         return None 

# # Fin de la clase InterpretePLSQL
