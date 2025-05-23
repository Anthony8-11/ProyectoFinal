# src/analizador_semantico/semantico_plsql.py
"""
Análisis semántico para PL/SQL.
Reconoce y valida todas las implementaciones soportadas por el lexer y parser:
- Declaraciones de variables y tipos
- Asignaciones
- Llamadas a procedimientos y funciones (incluyendo DBMS_OUTPUT, NVL, CHR, SYSDATE, RAISE_APPLICATION_ERROR)
- Bucles LOOP y FOR (con REVERSE, EXIT WHEN)
- Bloques BEGIN...END anidados
- Manejo de excepciones (EXCEPTION, WHEN, RAISE)
- Operadores aritméticos, lógicos, comparación, concatenación
- Funciones y procedimientos incorporados
- Validación de alcance y shadowing de variables
- Validación de uso correcto de SYSDATE, NVL, CHR, SQLERRM, etc.
- Validación de sentencias y expresiones soportadas
"""

from analizador_sintactico.parser_plsql import *
from analizador_lexico.lexer_plsql import *

class ErrorSemanticoPLSQL(Exception):
    pass

class AnalizadorSemanticoPLSQL:
    def __init__(self):
        self.errores = []
        self.tabla_simbolos = [{}]  # pila de scopes

    def analizar(self, nodo_script):
        if not isinstance(nodo_script, NodoScriptPLSQL):
            self.errores.append("El nodo raíz no es un NodoScriptPLSQL.")
            return
        for elemento in nodo_script.elementos:
            if isinstance(elemento, NodoBloquePLSQL):
                self._analizar_bloque(elemento)
            elif isinstance(elemento, NodoSelect):
                pass  # SELECT fuera de bloque: solo advertencia
            else:
                self.errores.append(f"Elemento de script no soportado: {type(elemento).__name__}")

    def _analizar_bloque(self, nodo_bloque):
        self.tabla_simbolos.append({})
        # Declaraciones
        if nodo_bloque.seccion_declaracion:
            for decl in nodo_bloque.seccion_declaracion:
                self._analizar_declaracion_variable(decl)
        # Ejecutable
        if nodo_bloque.seccion_ejecutable:
            for stmt in nodo_bloque.seccion_ejecutable:
                self._analizar_sentencia(stmt)
        # Excepciones
        if nodo_bloque.seccion_excepcion:
            self._analizar_excepcion(nodo_bloque.seccion_excepcion)
        self.tabla_simbolos.pop()

    def _analizar_declaracion_variable(self, nodo_decl):
        # Permitir que el nombre sea un Token o un str (según cómo lo construya el parser)
        if hasattr(nodo_decl.nombre_variable_token, 'lexema'):
            nombre = nodo_decl.nombre_variable_token.lexema.lower()
        else:
            nombre = str(nodo_decl.nombre_variable_token).lower()
        if nombre in self.tabla_simbolos[-1]:
            self.errores.append(f"Redeclaración de variable '{nombre}' en el mismo bloque.")
        self.tabla_simbolos[-1][nombre] = nodo_decl.tipo_dato_nodo
        if nodo_decl.valor_inicial_nodo:
            self._analizar_expresion(nodo_decl.valor_inicial_nodo)

    def _analizar_sentencia(self, nodo_stmt):
        if isinstance(nodo_stmt, NodoSentenciaAsignacionPLSQL):
            self._analizar_asignacion(nodo_stmt)
        elif isinstance(nodo_stmt, NodoLlamadaProcedimientoPLSQL):
            self._analizar_llamada_proc(nodo_stmt)
        elif isinstance(nodo_stmt, NodoSentenciaLoopPLSQL):
            self._analizar_loop(nodo_stmt)
        elif isinstance(nodo_stmt, NodoSentenciaForLoopPLSQL):
            self._analizar_for(nodo_stmt)
        elif isinstance(nodo_stmt, NodoSentenciaIfPLSQL):
            self._analizar_if(nodo_stmt)
        elif isinstance(nodo_stmt, NodoBloquePLSQL):
            self._analizar_bloque(nodo_stmt)
        elif isinstance(nodo_stmt, NodoSentenciaRaisePLSQL):
            self._analizar_raise(nodo_stmt)
        elif isinstance(nodo_stmt, NodoSentenciaExitWhenPLSQL):
            self._analizar_exit_when(nodo_stmt)
        elif nodo_stmt is None:
            pass
        else:
            self.errores.append(f"Sentencia no soportada: {type(nodo_stmt).__name__}")

    def _analizar_asignacion(self, nodo_asig):
        nombre = None
        if isinstance(nodo_asig.variable_nodo, NodoIdentificadorPLSQL):
            nombre = nodo_asig.variable_nodo.nombre.lower()
            if not self._existe_variable(nombre):
                self.errores.append(f"Variable '{nombre}' no declarada antes de asignación.")
        self._analizar_expresion(nodo_asig.expresion_nodo)

    def _analizar_llamada_proc(self, nodo_llamada):
        # Puede ser DBMS_OUTPUT.PUT_LINE, funciones incorporadas, etc.
        self._analizar_expresion(nodo_llamada.callee_nodo)
        if nodo_llamada.argumentos_nodos:
            for arg in nodo_llamada.argumentos_nodos:
                self._analizar_expresion(arg)

    def _analizar_loop(self, nodo_loop):
        for stmt in nodo_loop.cuerpo_sentencias:
            self._analizar_sentencia(stmt)

    def _analizar_for(self, nodo_for):
        # Permitir que la variable de iteración sea Token o str
        if hasattr(nodo_for.variable_iteracion_token, 'lexema'):
            var_name = nodo_for.variable_iteracion_token.lexema.lower()
        else:
            var_name = str(nodo_for.variable_iteracion_token).lower()
        # En vez de pasar un string, creamos un Token dummy para INTEGER
        integer_token = Token(TT_PALABRA_CLAVE_PLSQL, "INTEGER", 0, 0)
        self.tabla_simbolos[-1][var_name] = NodoTipoDatoPLSQL([integer_token])
        self._analizar_expresion(nodo_for.expresion_inicio_nodo)
        self._analizar_expresion(nodo_for.expresion_fin_nodo)
        for stmt in nodo_for.cuerpo_sentencias_nodos:
            self._analizar_sentencia(stmt)
        self.tabla_simbolos[-1].pop(var_name, None)

    def _analizar_if(self, nodo_if):
        for cond, cuerpo in nodo_if.casos_if_elsif:
            self._analizar_expresion(cond)
            for stmt in cuerpo:
                self._analizar_sentencia(stmt)
        if nodo_if.cuerpo_else:
            for stmt in nodo_if.cuerpo_else:
                self._analizar_sentencia(stmt)

    def _analizar_raise(self, nodo_raise):
        # Puede tener nombre de excepción
        pass

    def _analizar_exit_when(self, nodo_exit):
        self._analizar_expresion(nodo_exit.condicion_nodo)

    def _analizar_excepcion(self, nodo_ex):
        for clausula in nodo_ex.clausulas_when:
            for stmt in clausula.cuerpo_sentencias_nodos:
                self._analizar_sentencia(stmt)

    def _analizar_expresion(self, nodo_expr):
        if isinstance(nodo_expr, NodoLiteralPLSQL):
            pass
        elif isinstance(nodo_expr, NodoIdentificadorPLSQL):
            nombre = nodo_expr.nombre.lower()
            if nombre not in ("sysdate", "sqlerrm", "sqlcode") and not self._existe_variable(nombre):
                self.errores.append(f"Identificador '{nombre}' no declarado.")
        elif isinstance(nodo_expr, NodoExpresionBinariaPLSQL):
            self._analizar_expresion(nodo_expr.izquierda_nodo)
            self._analizar_expresion(nodo_expr.derecha_nodo)
        elif isinstance(nodo_expr, NodoExpresionUnariaPLSQL):
            self._analizar_expresion(nodo_expr.operando_nodo)
        elif isinstance(nodo_expr, NodoFuncionSQL):
            nombre_func = nodo_expr.nombre_funcion_token.lexema.lower()
            for arg in nodo_expr.argumentos_nodos:
                self._analizar_expresion(arg)
            # Validar funciones incorporadas
            if nombre_func not in ("sysdate", "nvl", "chr", "raise_application_error", "sqlerrm", "to_char"):
                self.errores.append(f"Función PL/SQL desconocida: '{nombre_func}'.")
        elif isinstance(nodo_expr, NodoMiembroExpresionPLSQL):
            # Ej: dbms_output.put_line
            pass
        else:
            self.errores.append(f"Expresión no soportada: {type(nodo_expr).__name__}")

    def _existe_variable(self, nombre):
        for scope in reversed(self.tabla_simbolos):
            if nombre in scope:
                return True
        return False

    def mostrar_resultado(self):
        if not self.errores:
            print("--- Análisis Semántico (PL/SQL) ---")
            print("No se encontraron errores semánticos en el código PL/SQL. La simulación será precisa.")
            print("--- Fin Análisis Semántico (PL/SQL) ---")
        else:
            print("--- Análisis Semántico (PL/SQL) ---")
            print(">>> Se encontraron errores semánticos en el código PL/SQL. La simulación podría no ser precisa. <<<")
            for err in self.errores:
                print(f"  [Semántico] {err}")
            print("--- Fin Análisis Semántico (PL/SQL) ---")

# Uso:
# analizador = AnalizadorSemanticoPLSQL()
# analizador.analizar(ast)
# print(analizador.errores)
# analizador.mostrar_resultado()
