# src/analizador_semantico/semantico_tsql.py
"""
Análisis semántico para T-SQL.
Reconoce y valida todas las implementaciones soportadas por el lexer y parser:
- CREATE TABLE (definición de columnas, restricciones)
- INSERT INTO (columnas, valores)
- SELECT (columnas, FROM, WHERE)
- UPDATE (asignaciones, WHERE)
- DELETE (tabla, WHERE)
- DECLARE, SET (variables)
- PRINT
- Expresiones aritméticas, lógicas, comparación, funciones
- Validación de variables, columnas, tipos y restricciones
- Validación de uso correcto de funciones y operadores
- Validación de sentencias y expresiones soportadas
"""

from analizador_sintactico.parser_tsql import *
from analizador_lexico.lexer_tsql import *

class ErrorSemanticoTSQL(Exception):
    pass

class AnalizadorSemanticoTSQL:
    def __init__(self):
        self.errores = []
        self.tabla_variables = {}  # Variables @var
        self.tabla_tablas = {}     # Tablas y columnas

    def analizar(self, nodo_script):
        if not isinstance(nodo_script, NodoScriptSQL):
            self.errores.append("El nodo raíz no es un NodoScriptSQL.")
            return
        for elemento in nodo_script.lotes_o_sentencias:
            if isinstance(elemento, NodoLoteSQL):
                for stmt in elemento.sentencias:
                    self._analizar_sentencia(stmt)
            elif isinstance(elemento, NodoSentenciaSQL):
                self._analizar_sentencia(elemento)
            else:
                self.errores.append(f"Elemento de script no soportado: {type(elemento).__name__}")

    def _analizar_sentencia(self, nodo_stmt):
        if isinstance(nodo_stmt, NodoCreateTable):
            self._analizar_create_table(nodo_stmt)
        elif isinstance(nodo_stmt, NodoInsert):
            self._analizar_insert(nodo_stmt)
        elif isinstance(nodo_stmt, NodoSelect):
            self._analizar_select(nodo_stmt)
        elif isinstance(nodo_stmt, NodoUpdate):
            self._analizar_update(nodo_stmt)
        elif isinstance(nodo_stmt, NodoDelete):
            self._analizar_delete(nodo_stmt)
        elif isinstance(nodo_stmt, NodoDeclareVariable):
            self._analizar_declare(nodo_stmt)
        elif isinstance(nodo_stmt, NodoSetVariable):
            self._analizar_set(nodo_stmt)
        elif isinstance(nodo_stmt, NodoPrint):
            self._analizar_print(nodo_stmt)
        elif isinstance(nodo_stmt, NodoGo):
            pass
        elif nodo_stmt is None:
            pass
        else:
            self.errores.append(f"Sentencia no soportada: {type(nodo_stmt).__name__}")

    def _analizar_create_table(self, nodo):
        nombre_tabla = nodo.nombre_tabla_token.lexema.lower()
        if nombre_tabla in self.tabla_tablas:
            self.errores.append(f"Tabla '{nombre_tabla}' redeclarada.")
        columnas = {}
        for col in nodo.definiciones_columna:
            col_name = col.nombre_columna_token.lexema.lower()
            if col_name in columnas:
                self.errores.append(f"Columna '{col_name}' redeclarada en tabla '{nombre_tabla}'.")
            columnas[col_name] = col.tipo_dato_token.lexema.lower()
            # Validar restricciones conocidas y DEFAULT correctamente
            restricciones = getattr(col, 'restricciones_tokens', [])
            i = 0
            while i < len(restricciones):
                restr = restricciones[i]
                restr_lex = getattr(restr, 'lexema', str(restr)).lower()
                if restr_lex == "default":
                    # Saltar el valor por defecto (puede ser una expresión o función)
                    i += 1  # Asumimos que el siguiente token es el valor por defecto
                    # Si el parser provee un nodo de expresión para el default, aquí podrías analizarlo
                    # self._analizar_expresion(col.default_expr_nodo)  # si existe
                elif restr_lex not in ("primary", "key", "not", "null", "unique", "default", "check"):
                    self.errores.append(f"Restricción desconocida '{restr_lex}' en columna '{col_name}'.")
                i += 1
        self.tabla_tablas[nombre_tabla] = columnas

    def _analizar_insert(self, nodo):
        nombre_tabla = nodo.nombre_tabla_token.lexema.lower()
        if nombre_tabla not in self.tabla_tablas:
            self.errores.append(f"Tabla '{nombre_tabla}' no declarada antes de INSERT.")
            return
        columnas = self.tabla_tablas[nombre_tabla]
        cols_insert = [t.lexema.lower() for t in nodo.columnas_lista_tokens] if nodo.columnas_lista_tokens else list(columnas.keys())
        for col in cols_insert:
            if col not in columnas:
                self.errores.append(f"Columna '{col}' no existe en tabla '{nombre_tabla}' (INSERT).")
        for fila in nodo.filas_valores_lista_nodos:
            if len(fila) != len(cols_insert):
                self.errores.append(f"Cantidad de valores no coincide con columnas en INSERT a '{nombre_tabla}'.")
            for expr in fila:
                self._analizar_expresion(expr)

    def _analizar_select(self, nodo):
        nombre_tabla = nodo.tabla_from_token.lexema.lower()
        if nombre_tabla not in self.tabla_tablas:
            self.errores.append(f"Tabla '{nombre_tabla}' no declarada antes de SELECT.")
            return
        columnas = self.tabla_tablas[nombre_tabla]
        for col in nodo.columnas_select_nodos:
            if isinstance(col, NodoAsteriscoSQL):
                continue
            elif isinstance(col, NodoIdentificadorSQL):
                if col.nombre.lower() not in columnas:
                    self.errores.append(f"Columna '{col.nombre}' no existe en tabla '{nombre_tabla}' (SELECT).")
            else:
                self._analizar_expresion(col)
        if nodo.where_condicion_nodo:
            self._analizar_expresion(nodo.where_condicion_nodo)

    def _analizar_update(self, nodo):
        nombre_tabla = nodo.nombre_tabla_token.lexema.lower()
        if nombre_tabla not in self.tabla_tablas:
            self.errores.append(f"Tabla '{nombre_tabla}' no declarada antes de UPDATE.")
            return
        columnas = self.tabla_tablas[nombre_tabla]
        for col_token, expr in nodo.asignaciones_set:
            col_name = col_token.lexema.lower()
            if col_name not in columnas:
                self.errores.append(f"Columna '{col_name}' no existe en tabla '{nombre_tabla}' (UPDATE).")
            self._analizar_expresion(expr)
        if nodo.where_condicion_nodo:
            self._analizar_expresion(nodo.where_condicion_nodo)

    def _analizar_delete(self, nodo):
        nombre_tabla = nodo.nombre_tabla_token.lexema.lower()
        if nombre_tabla not in self.tabla_tablas:
            self.errores.append(f"Tabla '{nombre_tabla}' no declarada antes de DELETE.")
            return
        if nodo.where_condicion_nodo:
            self._analizar_expresion(nodo.where_condicion_nodo)

    def _analizar_declare(self, nodo):
        nombre = nodo.nombre_variable_token.lexema.lower()
        if nombre in self.tabla_variables:
            self.errores.append(f"Variable '{nombre}' redeclarada.")
        self.tabla_variables[nombre] = nodo.tipo_dato_token.lexema.lower()
        if nodo.valor_inicial_nodo:
            self._analizar_expresion(nodo.valor_inicial_nodo)

    def _analizar_set(self, nodo):
        nombre = nodo.nombre_variable_token.lexema.lower()
        if nombre not in self.tabla_variables:
            self.errores.append(f"Variable '{nombre}' no declarada antes de SET.")
        self._analizar_expresion(nodo.expresion_nodo)

    def _analizar_print(self, nodo):
        self._analizar_expresion(nodo.expresion_nodo)

    def _analizar_expresion(self, nodo_expr):
        if isinstance(nodo_expr, NodoLiteralSQL):
            pass
        elif isinstance(nodo_expr, NodoIdentificadorSQL):
            nombre = nodo_expr.nombre.lower()
            if nombre.startswith('@'):
                if nombre not in self.tabla_variables:
                    self.errores.append(f"Variable '{nombre}' no declarada.")
            # Si es columna, solo se valida en contexto de tabla
        elif isinstance(nodo_expr, NodoExpresionBinariaSQL):
            self._analizar_expresion(nodo_expr.operando_izq_nodo)
            self._analizar_expresion(nodo_expr.operando_der_nodo)
        elif isinstance(nodo_expr, NodoFuncionSQL):
            nombre_func = nodo_expr.nombre_funcion_token.lexema.lower()
            for arg in nodo_expr.argumentos_nodos:
                self._analizar_expresion(arg)
            if nombre_func not in ("getdate", "current_timestamp", "count", "sum", "avg", "min", "max"):
                self.errores.append(f"Función T-SQL desconocida: '{nombre_func}'.")
        elif isinstance(nodo_expr, NodoAsteriscoSQL):
            pass
        else:
            self.errores.append(f"Expresión no soportada: {type(nodo_expr).__name__}")

    def mostrar_resultado(self):
        print("\n--- Análisis Semántico (T-SQL) ---")
        if not self.errores:
            print("No se encontraron errores semánticos en el código T-SQL. La simulación será precisa.")
        else:
            print(f"Se encontraron {len(self.errores)} error(es) semántico(s) en el código T-SQL. La simulación podría no ser precisa.")
            for err in self.errores:
                print(f"  [Semántico] {err}")
        print("--- Fin Análisis Semántico (T-SQL) ---")
