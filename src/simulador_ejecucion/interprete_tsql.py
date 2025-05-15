# src/simulador_ejecucion/interprete_tsql.py

# Importar las clases de nodos AST necesarias desde el parser_tsql.
# Es crucial que estas sean las mismas definiciones de nodos que usa el ParserTSQL.
try:
    from analizador_sintactico.parser_tsql import (
        NodoScriptSQL, NodoLoteSQL, NodoSentenciaSQL,
        NodoCreateTable, NodoDefinicionColumna, 
        NodoPrint, NodoGo, NodoInsert, NodoSelect, NodoUpdate, NodoDelete,
        NodoIdentificadorSQL, NodoLiteralSQL, NodoExpresionBinariaSQL, NodoAsteriscoSQL, NodoFuncionSQL, # Para expresiones simples
        NodoDeclareVariable, NodoSetVariable
    )
    # Podríamos necesitar tipos de token si el intérprete necesita verificar algo del token original,
    # pero generalmente operaremos sobre los nodos AST.
    # from analizador_lexico.lexer_tsql import Token # Si se necesita la clase Token
    from analizador_lexico.lexer_tsql import TT_OPERADOR_COMPARACION, TT_LITERAL_NUMERICO, TT_LITERAL_CADENA, TT_OPERADOR_ARITMETICO, TT_ASTERISCO

except ImportError:
    print("ADVERTENCIA CRÍTICA (InterpreteTSQL): No se pudieron importar los nodos AST desde parser_tsql. Error: {e_import_ast}")
    # Definir placeholders muy básicos si fallan las importaciones.
    # El intérprete no funcionará correctamente en este estado.
    class NodoScriptSQL: pass
    class NodoLoteSQL: pass
    class NodoSentenciaSQL: pass
    class NodoCreateTable: pass
    class NodoDefinicionColumna: pass
    class NodoPrint: pass
    class NodoGo: pass
    class NodoInsert: pass
    class NodoSelect: pass
    class NodoUpdate: pass
    class NodoDelete: pass 
    class NodoIdentificadorSQL: pass
    class NodoLiteralSQL: pass
    class NodoExpresionBinariaSQL: pass
    class NodoFuncionSQL: pass
    class NodoAsteriscoSQL: pass
    class NodoDeclareVariable: pass
    class NodoSetVariable: pass
    TT_OPERADOR_COMPARACION = "OPERADOR_COMPARACION"
    TT_LITERAL_NUMERICO = "LITERAL_NUMERICO"
    TT_LITERAL_CADENA = "LITERAL_CADENA"

class InterpreteTSQL:
    def __init__(self):
        """
        Inicializa el intérprete de T-SQL.
        Aquí se podrían inicializar estructuras para simular el estado de la base de datos,
        como un catálogo de tablas y variables de sesión/lote.
        """
        # Simulación del catálogo de la base de datos: un diccionario para almacenar las tablas creadas.
        # La clave será el nombre de la tabla, y el valor podría ser una lista de definiciones de columna.
        self.catalogo_tablas = {}
        
        self.datos_tablas = {} # Para almacenar filas insertadas (simulación más profunda)

        # Memoria para variables T-SQL (ej: @MiVariable).
        # Se podría manejar con alcances si implementamos lotes/procedimientos de forma más compleja.
        self.memoria_variables_tsql = {}
        
        # print("[Interprete TSQL DEBUG] Intérprete T-SQL inicializado.")

    def interpretar_script(self, nodo_script_sql):
        """
        Punto de entrada principal para iniciar la interpretación de un script T-SQL completo.
        
        Args:
            nodo_script_sql (NodoScriptSQL): El nodo raíz del AST del script T-SQL.
        """
        if not isinstance(nodo_script_sql, NodoScriptSQL):
            print("Error del Intérprete TSQL: Se esperaba un NodoScriptSQL como raíz del AST.")
            return

        try:
            print("\n--- Iniciando Simulación de Ejecución (T-SQL) ---")
            # Un script SQL puede contener múltiples lotes o directamente sentencias.
            # El NodoScriptSQL tiene una lista 'lotes_o_sentencias'.
            for elemento in nodo_script_sql.lotes_o_sentencias:
                if isinstance(elemento, NodoLoteSQL):
                    self.visitar_NodoLoteSQL(elemento)
                elif isinstance(elemento, NodoSentenciaSQL): # Si el script es una lista de sentencias directas
                    self.ejecutar_sentencia_sql(elemento)
                elif isinstance(elemento, NodoGo): # 'GO' puede estar al nivel del script
                    self.visitar_NodoGo(elemento)
                else:
                    print(f"Advertencia del Intérprete TSQL: Elemento desconocido en NodoScriptSQL: {type(elemento).__name__}")
            
            print("--- Simulación de Ejecución Finalizada (T-SQL) ---")
            # print(f"[Interprete TSQL DEBUG] Catálogo final de tablas: {self.catalogo_tablas}")
            # print(f"[Interprete TSQL DEBUG] Estado final de variables TSQL: {self.memoria_variables_tsql}")

        except RuntimeError as e_runtime:
            print(f"Error en Tiempo de Ejecución (T-SQL): {e_runtime}")
        except Exception as e_general:
            print(f"Error Inesperado durante la Interpretación (T-SQL): {e_general}")
            import traceback
            traceback.print_exc()

    def visitar_NodoLoteSQL(self, nodo_lote):
        """Visita y ejecuta las sentencias dentro de un lote SQL."""
        # print("[Interprete TSQL DEBUG] Visitando NodoLoteSQL.")
        for sentencia_nodo in nodo_lote.sentencias:
            self.ejecutar_sentencia_sql(sentencia_nodo)
        # Aquí se podría simular el fin de un lote si tuviera alguna semántica especial.

    def ejecutar_sentencia_sql(self, nodo_sentencia):
        """
        Método despachador para diferentes tipos de sentencias SQL.
        Determina el tipo de nodo de sentencia y llama al método visitante apropiado.
        """
        # print(f"[Interprete TSQL DEBUG] Ejecutando Sentencia SQL: {type(nodo_sentencia).__name__}")
        if isinstance(nodo_sentencia, NodoCreateTable):
            self.visitar_NodoCreateTable(nodo_sentencia)
        elif isinstance(nodo_sentencia, NodoPrint):
            self.visitar_NodoPrint(nodo_sentencia)
        elif isinstance(nodo_sentencia, NodoGo): # 'GO' también puede ser tratado como una "sentencia"
            self.visitar_NodoGo(nodo_sentencia)
        elif isinstance(nodo_sentencia, NodoInsert):
            self.visitar_NodoInsert(nodo_sentencia) 
        elif isinstance(nodo_sentencia, NodoSelect):
            self.visitar_NodoSelect(nodo_sentencia)
        elif isinstance(nodo_sentencia, NodoUpdate): 
            self.visitar_NodoUpdate(nodo_sentencia)
        elif isinstance(nodo_sentencia, NodoDelete): 
            self.visitar_NodoDelete(nodo_sentencia)
        elif isinstance(nodo_sentencia, NodoDeclareVariable):
            self.visitar_NodoDeclareVariable(nodo_sentencia) 
        elif isinstance(nodo_sentencia, NodoSetVariable):
            self.visitar_NodoSetVariable(nodo_sentencia) 
        else:
            print(f"Advertencia del Intérprete TSQL: Ejecución para el tipo de nodo de sentencia '{type(nodo_sentencia).__name__}' no implementada.")

    # --- Métodos para visitar sentencias específicas ---

    def visitar_NodoCreateTable(self, nodo_create_table):
        nombre_tabla = nodo_create_table.nombre_tabla_token.lexema
        # print(f"[Interprete TSQL DEBUG] Visitando NodoCreateTable para tabla: {nombre_tabla}")

        if nombre_tabla in self.catalogo_tablas:
            print(f"Advertencia del Intérprete TSQL: La tabla '{nombre_tabla}' ya existe. No se recreará (simulado).")
            return

        columnas_definidas = []
        if nodo_create_table.definiciones_columna: # Verificar si hay definiciones de columna
            for def_col_nodo in nodo_create_table.definiciones_columna:
                # --- VERIFICACIÓN Y ACCESO SEGURO AL ATRIBUTO ---
                restricciones_lexemas = []
                if hasattr(def_col_nodo, 'restricciones_tokens') and def_col_nodo.restricciones_tokens:
                    restricciones_lexemas = [r.lexema for r in def_col_nodo.restricciones_tokens]
                elif hasattr(def_col_nodo, 'restricciones') and def_col_nodo.restricciones: # Fallback por si el atributo se llama diferente
                     print(f"Advertencia (InterpreteTSQL): NodoDefinicionColumna para '{def_col_nodo.nombre_columna_token.lexema}' usa 'restricciones' en lugar de 'restricciones_tokens'.")
                     restricciones_lexemas = [r.lexema for r in def_col_nodo.restricciones]
                # --- FIN DE VERIFICACIÓN ---
                
                col_info = {
                    'nombre': def_col_nodo.nombre_columna_token.lexema,
                    'tipo': def_col_nodo.tipo_dato_token.lexema,
                    'restricciones': restricciones_lexemas
                }
                columnas_definidas.append(col_info)
        
        self.catalogo_tablas[nombre_tabla] = columnas_definidas
        self.datos_tablas[nombre_tabla] = [] # Inicializar lista vacía para los datos de la nueva tabla

        print(f"Simulación: Tabla '{nombre_tabla}' creada exitosamente con {len(columnas_definidas)} columna(s).")

    def visitar_NodoDeclareVariable(self, nodo_declare):
        """Simula la ejecución de una sentencia DECLARE @variable TIPO [= valor_inicial]."""
        nombre_variable = nodo_declare.nombre_variable_token.lexema
        # print(f"[Interprete TSQL DEBUG] Declarando variable: {nombre_variable} de tipo {nodo_declare.tipo_dato_token.lexema}")

        if nombre_variable in self.memoria_variables_tsql:
            # T-SQL permite re-declarar una variable en el mismo lote si el tipo es el mismo,
            # pero para una simulación simple, podemos ser más estrictos o permitirlo.
            # Por ahora, si ya existe, no hacemos nada o podríamos reinicializarla.
            # Si tiene un valor inicial, se sobrescribirá.
            print(f"Advertencia (Intérprete TSQL): Variable '{nombre_variable}' ya existe. Se re-evaluará su valor inicial si se provee.")

        valor_a_asignar = None # Por defecto, las variables T-SQL se inicializan a NULL
        if nodo_declare.valor_inicial_nodo:
            valor_a_asignar = self.evaluar_expresion_sql(nodo_declare.valor_inicial_nodo)
        
        self.memoria_variables_tsql[nombre_variable] = valor_a_asignar
        # print(f"[Interprete TSQL DEBUG] Variable '{nombre_variable}' inicializada a: {repr(valor_a_asignar)}. Memoria: {self.memoria_variables_tsql}")

    def visitar_NodoSetVariable(self, nodo_set):
        """Simula la ejecución de una sentencia SET @variable = expresion."""
        nombre_variable = nodo_set.nombre_variable_token.lexema
        # print(f"[Interprete TSQL DEBUG] Asignando (SET) a variable: {nombre_variable}")

        # En T-SQL, SET se usa para variables ya declaradas.
        # Aunque algunas versiones permiten SET @var = valor sin DECLARE previo (creándola implícitamente),
        # es buena práctica declararlas. Para nuestra simulación, podríamos requerir declaración previa.
        if nombre_variable not in self.memoria_variables_tsql:
            # Podríamos lanzar un error o permitir creación implícita.
            # Por ahora, permitiremos la creación implícita para simplificar,
            # pero imprimiremos una advertencia si no fue declarada (no tiene tipo conocido).
            print(f"Advertencia (Intérprete TSQL): Variable '{nombre_variable}' asignada con SET sin DECLARE previo (simulado).")
            # O: raise RuntimeError(f"Variable '{nombre_variable}' no ha sido declarada antes de SET.")

        valor_expresion = self.evaluar_expresion_sql(nodo_set.expresion_nodo)
        self.memoria_variables_tsql[nombre_variable] = valor_expresion
        # print(f"[Interprete TSQL DEBUG] Variable '{nombre_variable}' (SET) asignada con valor: {repr(valor_expresion)}. Memoria: {self.memoria_variables_tsql}")

    def visitar_NodoPrint(self, nodo_print):
        """Simula la ejecución de una sentencia PRINT."""
        # print(f"[Interprete TSQL DEBUG] Visitando NodoPrint.")
        valor_a_imprimir = self.evaluar_expresion_sql(nodo_print.expresion_nodo)
        print(str(valor_a_imprimir)) # PRINT convierte su argumento a una cadena.

    def visitar_NodoGo(self, nodo_go):
        """Simula la ejecución de un comando GO."""
        # En una simulación, GO podría no tener un efecto visible más allá de la separación de lotes
        # que el parser ya podría haber manejado al estructurar el AST.
        # Podríamos imprimir un mensaje para indicar que se procesó un lote.
        print("-- Lote de T-SQL completado (simulado por GO) --")

    def visitar_NodoInsert(self, nodo_insert):
        """Simula la ejecución de una sentencia INSERT INTO."""
        nombre_tabla = nodo_insert.nombre_tabla_token.lexema
        # print(f"[Interprete TSQL DEBUG] Visitando NodoInsert para tabla: {nombre_tabla}")

        if nombre_tabla not in self.catalogo_tablas:
            raise RuntimeError(f"La tabla '{nombre_tabla}' no existe en el catálogo.")

        definicion_tabla = self.catalogo_tablas[nombre_tabla]
        nombres_columnas_tabla = [col['nombre'] for col in definicion_tabla]

        columnas_a_insertar_tokens = nodo_insert.columnas_lista_tokens
        nombres_columnas_a_insertar = []

        if columnas_a_insertar_tokens: # Si se especificaron columnas en el INSERT
            nombres_columnas_a_insertar = [token.lexema for token in columnas_a_insertar_tokens]
            # Verificación semántica simple: ¿existen estas columnas en la tabla?
            for nombre_col_insert in nombres_columnas_a_insertar:
                if nombre_col_insert not in nombres_columnas_tabla:
                    raise RuntimeError(f"La columna '{nombre_col_insert}' no existe en la tabla '{nombre_tabla}'.")
        else: # Si no se especificaron columnas, se asumen todas las columnas de la tabla en orden.
            nombres_columnas_a_insertar = nombres_columnas_tabla
        
        # Procesar cada fila de valores en el NodoInsert (aunque el parser actual solo crea una fila)
        for fila_valores_nodos in nodo_insert.filas_valores_lista_nodos:
            if len(fila_valores_nodos) != len(nombres_columnas_a_insertar):
                raise RuntimeError(
                    f"El número de valores ({len(fila_valores_nodos)}) no coincide con el número de columnas "
                    f"especificadas o implícitas ({len(nombres_columnas_a_insertar)}) para la tabla '{nombre_tabla}'."
                )

            fila_a_insertar = {}
            for i, nodo_valor_expresion in enumerate(fila_valores_nodos):
                valor_evaluado = self.evaluar_expresion_sql(nodo_valor_expresion)
                nombre_columna_actual = nombres_columnas_a_insertar[i]
                fila_a_insertar[nombre_columna_actual] = valor_evaluado
            
            # Simular la inserción añadiendo la fila al almacenamiento de datos de la tabla.
            self.datos_tablas[nombre_tabla].append(fila_a_insertar)
            print(f"Simulación: 1 fila insertada en '{nombre_tabla}'. Valores: {fila_a_insertar}")
            # print(f"[Interprete TSQL DEBUG] Datos de '{nombre_tabla}' ahora: {self.datos_tablas[nombre_tabla]}")

    def visitar_NodoSelect(self, nodo_select):
        """Simula la ejecución de una sentencia SELECT."""
        nombre_tabla = nodo_select.tabla_from_token.lexema
        # print(f"[Interprete TSQL DEBUG] Visitando NodoSelect para tabla: {nombre_tabla}")

        if nombre_tabla not in self.catalogo_tablas:
            raise RuntimeError(f"La tabla '{nombre_tabla}' no existe en el catálogo.")
        if nombre_tabla not in self.datos_tablas:
            # Esto no debería ocurrir si CREATE TABLE inicializa self.datos_tablas[nombre_tabla] = []
            print(f"Advertencia: La tabla '{nombre_tabla}' existe en el catálogo pero no tiene datos almacenados (o la estructura de datos está vacía).")
            self.datos_tablas[nombre_tabla] = [] # Asegurar que exista la lista

        filas_fuente = self.datos_tablas[nombre_tabla]
        filas_resultado = []

        # 1. Aplicar cláusula WHERE (si existe)
        if nodo_select.where_condicion_nodo:
            for fila in filas_fuente:
                if self._evaluar_condicion_where_simple(nodo_select.where_condicion_nodo, fila):
                    filas_resultado.append(fila)
        else:
            filas_resultado = list(filas_fuente) # Usar todas las filas si no hay WHERE

        # 2. Determinar las columnas a seleccionar
        columnas_a_mostrar_nombres = []
        es_select_asterisco = any(isinstance(col_nodo, NodoAsteriscoSQL) for col_nodo in nodo_select.columnas_select_nodos)

        if es_select_asterisco:
            # Si es SELECT *, obtener todos los nombres de columna de la definición de la tabla
            if self.catalogo_tablas[nombre_tabla]:
                columnas_a_mostrar_nombres = [col_def['nombre'] for col_def in self.catalogo_tablas[nombre_tabla]]
            else: # No debería pasar si la tabla fue creada correctamente
                print(f"Advertencia: No se encontró definición de columnas para la tabla '{nombre_tabla}' en el catálogo.")
                return 
        else:
            # Si se especifican columnas, obtener sus nombres
            for col_nodo in nodo_select.columnas_select_nodos:
                if isinstance(col_nodo, NodoIdentificadorSQL):
                    columnas_a_mostrar_nombres.append(col_nodo.nombre)
                # Aquí se podrían manejar expresiones o funciones en la lista de selección más adelante
                else:
                    print(f"Advertencia: Selección de tipo de columna '{type(col_nodo).__name__}' no completamente soportada, se intentará usar lexema.")
                    if hasattr(col_nodo, 'id_token') and hasattr(col_nodo.id_token, 'lexema'):
                         columnas_a_mostrar_nombres.append(col_nodo.id_token.lexema)
                    elif hasattr(col_nodo, 'literal_token') and hasattr(col_nodo.literal_token, 'lexema'):
                         columnas_a_mostrar_nombres.append(col_nodo.literal_token.lexema)


        # 3. Imprimir los resultados
        if not columnas_a_mostrar_nombres:
            print("Advertencia: No hay columnas para mostrar en el SELECT.")
            return

        # Imprimir encabezados de columna
        print("\n--- Resultado del SELECT ---")
        print(" | ".join(columnas_a_mostrar_nombres))
        print("-" * (sum(len(col) for col in columnas_a_mostrar_nombres) + (len(columnas_a_mostrar_nombres) -1) * 3)) # Línea separadora

        if not filas_resultado:
            print("(0 filas afectadas)")
        else:
            for fila in filas_resultado:
                valores_fila = [str(fila.get(nombre_col, "NULL")) for nombre_col in columnas_a_mostrar_nombres]
                print(" | ".join(valores_fila))
        print("--------------------------\n")

    def visitar_NodoDelete(self, nodo_delete):
        """Simula la ejecución de una sentencia DELETE FROM."""
        nombre_tabla = nodo_delete.nombre_tabla_token.lexema
        # print(f"[Interprete TSQL DEBUG] Visitando NodoDelete para tabla: {nombre_tabla}")

        if nombre_tabla not in self.catalogo_tablas:
            raise RuntimeError(f"La tabla '{nombre_tabla}' no existe en el catálogo para DELETE.")
        if nombre_tabla not in self.datos_tablas or not self.datos_tablas[nombre_tabla]:
            print(f"Simulación: DELETE en '{nombre_tabla}'. La tabla está vacía. (0 filas afectadas)")
            return

        filas_originales = self.datos_tablas[nombre_tabla]
        filas_a_conservar = []
        filas_eliminadas_count = 0

        if nodo_delete.where_condicion_nodo:
            for fila in filas_originales:
                if not self._evaluar_condicion_where_simple(nodo_delete.where_condicion_nodo, fila):
                    filas_a_conservar.append(fila) # Conservar si NO cumple la condición de borrado
                else:
                    filas_eliminadas_count += 1
            self.datos_tablas[nombre_tabla] = filas_a_conservar
        else:
            # Si no hay cláusula WHERE, se eliminan todas las filas.
            filas_eliminadas_count = len(filas_originales)
            self.datos_tablas[nombre_tabla] = [] # Vaciar la lista de datos
        
        print(f"Simulación: DELETE en '{nombre_tabla}'. ({filas_eliminadas_count} fila(s) afectada(s))")

    def _evaluar_condicion_where_simple(self, condicion_nodo, fila_actual):
        """
        Evalúa una condición WHERE simple (columna OPERADOR valor).
        Args:
            condicion_nodo (NodoExpresionBinariaSQL): El nodo de la condición.
            fila_actual (dict): La fila actual de datos ({'nombre_columna': valor, ...}).
        Returns:
            bool: True si la fila cumple la condición, False en caso contrario.
        """
        if not isinstance(condicion_nodo, NodoExpresionBinariaSQL):
            raise RuntimeError("La condición WHERE debe ser una expresión binaria simple (columna OP valor).")

        # Operando izquierdo (debería ser un nombre de columna)
        if not isinstance(condicion_nodo.operando_izq_nodo, NodoIdentificadorSQL):
            raise RuntimeError("El operando izquierdo de la condición WHERE debe ser un nombre de columna.")
        
        nombre_columna_cond = condicion_nodo.operando_izq_nodo.nombre
        if nombre_columna_cond not in fila_actual:
            # Podría ser un error o simplemente la columna no existe en esta fila (menos probable para SQL estándar)
            # O la columna no existe en la tabla. El parser debería haberlo detectado si fuera posible.
            print(f"Advertencia: Columna '{nombre_columna_cond}' no encontrada en la fila para la condición WHERE.")
            return False 

        valor_columna_en_fila = fila_actual[nombre_columna_cond]
        
        # Operador de comparación
        operador = condicion_nodo.operador_token.lexema
        
        # Operando derecho (debería ser un literal)
        if not isinstance(condicion_nodo.operando_der_nodo, NodoLiteralSQL):
            # Podría ser otro identificador de columna, o una variable @var.
            # Por ahora, simplificamos a literal.
            # Si es un identificador, necesitamos evaluarlo (podría ser otra columna o una variable @)
            if isinstance(condicion_nodo.operando_der_nodo, NodoIdentificadorSQL):
                valor_comparacion = self.evaluar_NodoIdentificadorSQL(condicion_nodo.operando_der_nodo)
            else:
                raise RuntimeError("El operando derecho de la condición WHERE simple debe ser un literal o identificador.")
        else:
            valor_comparacion = condicion_nodo.operando_der_nodo.valor

        # Realizar la comparación
        # print(f"[DEBUG WHERE] Comparando: {valor_columna_en_fila} {operador} {valor_comparacion}")
        # Nota: Esta comparación es directa. En SQL real, hay reglas de conversión de tipos.
        # Python intentará comparar, lo que puede funcionar para números y cadenas.
        try:
            if operador == '=':  return valor_columna_en_fila == valor_comparacion
            elif operador == '<>': return valor_columna_en_fila != valor_comparacion
            elif operador == '!=': return valor_columna_en_fila != valor_comparacion
            elif operador == '<':  return valor_columna_en_fila < valor_comparacion
            elif operador == '>':  return valor_columna_en_fila > valor_comparacion
            elif operador == '<=': return valor_columna_en_fila <= valor_comparacion
            elif operador == '>=': return valor_columna_en_fila >= valor_comparacion
            # (Aquí se podrían añadir LIKE, BETWEEN, IN si se parsean)
            else:
                raise RuntimeError(f"Operador de comparación desconocido en WHERE: '{operador}'")
        except TypeError:
            # Ocurre si los tipos no son comparables (ej. int con str sin conversión explícita)
            print(f"Advertencia: TypeError al comparar '{valor_columna_en_fila}' ({type(valor_columna_en_fila)}) con '{valor_comparacion}' ({type(valor_comparacion)}) en WHERE.")
            return False # Considerar como no coincidente si hay error de tipo en la comparación.


    def visitar_NodoUpdate(self, nodo_update):
        """Simula la ejecución de una sentencia UPDATE."""
        nombre_tabla = nodo_update.nombre_tabla_token.lexema
        # print(f"[Interprete TSQL DEBUG] Visitando NodoUpdate para tabla: {nombre_tabla}")

        if nombre_tabla not in self.catalogo_tablas:
            raise RuntimeError(f"La tabla '{nombre_tabla}' no existe en el catálogo para UPDATE.")
        if nombre_tabla not in self.datos_tablas:
            self.datos_tablas[nombre_tabla] = [] # Asegurar que exista la lista de datos
            print(f"Advertencia: La tabla '{nombre_tabla}' no tenía datos para actualizar. (0 filas afectadas)")
            return

        filas_a_actualizar_indices = []
        if nodo_update.where_condicion_nodo:
            for i, fila in enumerate(self.datos_tablas[nombre_tabla]):
                if self._evaluar_condicion_where_simple(nodo_update.where_condicion_nodo, fila):
                    filas_a_actualizar_indices.append(i)
        else:
            # Si no hay cláusula WHERE, se actualizan todas las filas.
            filas_a_actualizar_indices = list(range(len(self.datos_tablas[nombre_tabla])))
        
        filas_afectadas = 0
        if not filas_a_actualizar_indices:
            print(f"Simulación: UPDATE en '{nombre_tabla}'. (0 filas cumplen la condición WHERE o la tabla está vacía)")
            return

        for indice_fila in filas_a_actualizar_indices:
            fila_modificable = self.datos_tablas[nombre_tabla][indice_fila] # Obtener referencia a la fila (diccionario)
            
            for col_asign_token, expr_valor_nodo in nodo_update.asignaciones_set:
                nombre_columna_set = col_asign_token.lexema
                
                # Verificar que la columna a actualizar exista en la tabla (según catálogo)
                columnas_catalogo = [col_def['nombre'] for col_def in self.catalogo_tablas[nombre_tabla]]
                if nombre_columna_set not in columnas_catalogo:
                    raise RuntimeError(f"La columna '{nombre_columna_set}' no existe en la tabla '{nombre_tabla}' para la cláusula SET.")

                # Evaluar la expresión para obtener el nuevo valor
                # Nota: Si la expresión usa nombres de columna, se evaluarán en el contexto de la fila actual.
                # Esto requeriría que evaluar_expresion_sql pueda tomar un contexto de fila.
                # Por ahora, _parse_expresion_sql_simple solo maneja literales e identificadores simples (variables @).
                # Si la expresión es 'Salario * 1.10', necesitaríamos un evaluador de expresiones más completo.
                # Simplificación: si la expresión es un identificador, se busca en la fila actual.
                
                nuevo_valor = self.evaluar_expresion_sql_con_contexto_fila(expr_valor_nodo, fila_modificable)
                
                fila_modificable[nombre_columna_set] = nuevo_valor
            filas_afectadas += 1
            # print(f"[Interprete TSQL DEBUG] Fila actualizada: {fila_modificable}")

        print(f"Simulación: UPDATE en '{nombre_tabla}'. ({filas_afectadas} fila(s) afectada(s))")

    # --- Métodos para evaluar expresiones SQL (muy simplificados por ahora) ---
    def evaluar_expresion_sql(self, nodo_expresion):
          return self.evaluar_expresion_sql_con_contexto_fila(nodo_expresion, None)

        

    def evaluar_expresion_sql_con_contexto_fila(self, nodo_expresion, fila_contexto=None):
        """
        Método despachador para evaluar expresiones SQL, opcionalmente con un contexto de fila.
        """
        # print(f"[Interprete TSQL DEBUG] Evaluando Expresión SQL: {type(nodo_expresion).__name__} con fila: {fila_contexto is not None}")
        if isinstance(nodo_expresion, NodoLiteralSQL):
            return self.evaluar_NodoLiteralSQL(nodo_expresion) # No necesita fila_contexto
        elif isinstance(nodo_expresion, NodoIdentificadorSQL):
            return self.evaluar_NodoIdentificadorSQL(nodo_expresion, fila_contexto) # Pasa fila_contexto
        elif isinstance(nodo_expresion, NodoExpresionBinariaSQL):
            return self.evaluar_NodoExpresionBinariaSQL(nodo_expresion, fila_contexto) # Pasa fila_contexto
        elif isinstance(nodo_expresion, NodoFuncionSQL):
            return self.evaluar_NodoFuncionSQL(nodo_expresion, fila_contexto) # Pasa fila_contexto
        else:
            # Fallback para expresiones no completamente soportadas en evaluación
            if hasattr(nodo_expresion, 'id_token') and hasattr(nodo_expresion.id_token, 'lexema'):
                 return nodo_expresion.id_token.lexema 
            elif hasattr(nodo_expresion, 'literal_token') and hasattr(nodo_expresion.literal_token, 'lexema'):
                 return nodo_expresion.literal_token.lexema
            raise RuntimeError(f"Tipo de nodo de expresión SQL desconocido o no soportado para evaluar: {type(nodo_expresion).__name__}")


    def evaluar_NodoLiteralSQL(self, nodo_literal):
        # El valor de un literal ya fue procesado por el lexer (ej. a número o cadena Python).
        # print(f"[Interprete TSQL DEBUG] Evaluando NodoLiteralSQL, valor: {repr(nodo_literal.valor)}")
        return nodo_literal.valor

    def evaluar_NodoIdentificadorSQL(self, nodo_identificador, fila_contexto=None):
        # Evalúa un identificador SQL (variable @var o nombre de columna en contexto de fila).
        nombre_id = nodo_identificador.nombre
        # print(f"[Interprete DEBUG] Evaluando NodoIdentificadorSQL: {nombre_id} con fila_contexto: {fila_contexto is not None}")
        
        if nombre_id.startswith('@'): 
            # Si es una variable T-SQL (ej. @MiVar), buscarla en la memoria de variables.
            if nombre_id in self.memoria_variables_tsql:
                return self.memoria_variables_tsql[nombre_id]
            else:
                # Error si la variable se usa antes de ser declarada o asignada.
                raise RuntimeError(f"Variable T-SQL '{nombre_id}' usada antes de ser declarada o asignada un valor.")
        elif fila_contexto and nombre_id in fila_contexto: 
            # Si hay un contexto de fila (ej. evaluando una condición WHERE o una expresión en SET)
            # y el identificador es un nombre de columna presente en esa fila.
            return fila_contexto[nombre_id]
        else:
            # Si no es una variable @ y no hay contexto de fila, o no está en la fila.
            # Esto podría ser un nombre de columna en un SELECT (manejado al proyectar)
            # o un identificador en un PRINT fuera de contexto de fila.
            if fila_contexto is None: 
                 # Para PRINT nombre_columna, por ejemplo.
                 print(f"Advertencia (Intérprete): Identificador '{nombre_id}' usado fuera de contexto de fila, se tratará como cadena literal.")
                 return nombre_id # Devuelve el nombre como cadena.
            else: 
                # Está en contexto de fila pero la columna no se encontró en la fila actual.
                raise RuntimeError(f"Columna '{nombre_id}' no encontrada en la fila actual del contexto.")
        

    def evaluar_NodoExpresionBinariaSQL(self, nodo_expr_bin, fila_contexto=None):
        valor_izq = self.evaluar_expresion_sql_con_contexto_fila(nodo_expr_bin.operando_izq_nodo, fila_contexto)
        valor_der = self.evaluar_expresion_sql_con_contexto_fila(nodo_expr_bin.operando_der_nodo, fila_contexto)
        operador = nodo_expr_bin.operador_token.lexema.lower()
        tipo_operador_token = nodo_expr_bin.operador_token.tipo # Obtener el TIPO del token operador

        if tipo_operador_token == TT_OPERADOR_COMPARACION:
            try:
                if operador == '=':  return valor_izq == valor_der
                elif operador == '<>': return valor_izq != valor_der
                elif operador == '!=': return valor_izq != valor_der
                elif operador == '<':  return valor_izq < valor_der
                elif operador == '>':  return valor_izq > valor_der
                elif operador == '<=': return valor_izq <= valor_der
                elif operador == '>=': return valor_izq >= valor_der
                else: raise RuntimeError(f"Operador relacional desconocido: '{operador}'")
            except TypeError: 
                print(f"Advertencia: TypeError al comparar '{valor_izq}' ({type(valor_izq)}) con '{valor_der}' ({type(valor_der)}) con op '{operador}'.")
                return False
        
        elif tipo_operador_token == TT_OPERADOR_ARITMETICO or \
             (tipo_operador_token == TT_ASTERISCO and operador == '*'): # Acepta TT_ASTERISCO si es '*'
            
            # Verificar si es concatenación de cadenas para '+'
            if operador == '+' and isinstance(valor_izq, str) and isinstance(valor_der, str):
                return valor_izq + valor_der
            
            # Para otras operaciones aritméticas, los operandos deben ser numéricos
            if not (isinstance(valor_izq, (int, float)) and isinstance(valor_der, (int, float))):
                raise RuntimeError(f"Operandos para el operador aritmético '{operador}' deben ser numéricos. Se obtuvieron {type(valor_izq).__name__} y {type(valor_der).__name__}.")

            if operador == '+': return valor_izq + valor_der
            elif operador == '-': return valor_izq - valor_der
            elif operador == '*': return valor_izq * valor_der # Multiplicación
            elif operador == '/': 
                if valor_der == 0 or valor_der == 0.0: raise RuntimeError("División por cero.")
                return valor_izq / valor_der 
            # (div y mod como estaban antes, si los tienes)
            else: raise RuntimeError(f"Operador aritmético desconocido o no soportado: '{operador}'")
       
        else:
            raise RuntimeError(f"Tipo de operador binario no soportado: '{operador}' (tipo token: {tipo_operador_token})")



    def evaluar_NodoFuncionSQL(self, nodo_funcion, fila_contexto=None): # Placeholder
        nombre_func = nodo_funcion.nombre_funcion_token.lexema.lower()
        # (Lógica para GETDATE, etc. como estaba antes)
        if nombre_func == 'getdate' or nombre_func == 'current_timestamp':
            from datetime import datetime # Importar aquí si no está global
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] # Incluir milisegundos
        elif nombre_func == 'count': # Simplificación para COUNT(*)
            if nodo_funcion.argumentos_nodos and isinstance(nodo_funcion.argumentos_nodos[0], NodoAsteriscoSQL):
                # En un contexto real, COUNT(*) operaría sobre una tabla/conjunto de resultados.
                # Aquí, no tenemos ese contexto directo. Podríamos devolver un placeholder.
                print("Advertencia: COUNT(*) no tiene un contexto de tabla directo en esta evaluación de expresión simple.")
                return 0 # Placeholder
        print(f"Advertencia: Función SQL '{nombre_func}' no implementada en el intérprete.")
        return f"{nombre_func}()"
# Fin de la clase InterpreteTSQL
