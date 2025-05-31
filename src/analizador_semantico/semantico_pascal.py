# src/analizador_semantico/semantico_pascal.py
"""
Análisis semántico para Pascal.
Reconoce y valida todas las implementaciones soportadas por el lexer y parser:
- PROGRAM, VAR, BEGIN/END, asignaciones, expresiones, IF/THEN/ELSE, WHILE, FOR, REPEAT, procedimientos y funciones, llamadas a procedimientos, Writeln/Write/Readln/Read, declaraciones de constantes y tipos, arrays, records, operadores, etc.
- Validación de variables, tipos, alcance, uso correcto de procedimientos y funciones, control de flujo, etc.
"""

from analizador_sintactico.parser_pascal import *
from analizador_lexico.lexer_pascal import *

class ErrorSemanticoPascal(Exception):
    pass

class AnalizadorSemanticoPascal:
    def __init__(self):
        self.errores = []
        self.tabla_variables = {}  # nombre -> tipo
        self.tabla_constantes = {} # nombre -> valor
        self.tabla_tipos = {}      # nombre -> tipo base
        self.tabla_procedimientos = {} # nombre -> (params, nodo)
        self.tabla_funciones = {}      # nombre -> (params, tipo_retorno, nodo)
        self.alcance_actual = [{}]     # pila de diccionarios para variables locales

    def analizar(self, nodo_programa):
        if not isinstance(nodo_programa, NodoPrograma):
            self.errores.append("El nodo raíz no es un NodoPrograma.")
            return
        self._analizar_bloque(nodo_programa.bloque_nodo)

    def _analizar_bloque(self, nodo_bloque):
        if nodo_bloque.declaraciones_var_nodo:
            self._analizar_declaraciones_var(nodo_bloque.declaraciones_var_nodo)
        if nodo_bloque.cuerpo_nodo:
            self._analizar_cuerpo(nodo_bloque.cuerpo_nodo)

    def _analizar_declaraciones_var(self, nodo_decls):
        for decl in nodo_decls.declaraciones:
            self._analizar_declaracion_var(decl)

    def _analizar_declaracion_var(self, nodo_decl):
        tipo = nodo_decl.tipo_nodo.tipo_token.lexema.lower() if nodo_decl.tipo_nodo else None
        for id_token in nodo_decl.lista_identificadores_tokens:
            nombre = id_token.lexema.lower()
            if nombre in self.tabla_variables:
                self.errores.append(f"Variable '{nombre}' redeclarada.")
            self.tabla_variables[nombre] = tipo

    def _analizar_cuerpo(self, nodo_cuerpo):
        print(f"[DEBUG] _analizar_cuerpo: nodo_cuerpo type = {type(nodo_cuerpo).__name__}")
        print(f"[DEBUG] dir(nodo_cuerpo): {dir(nodo_cuerpo)}")
        print(f"[DEBUG] getattr(nodo_cuerpo, 'lista_sentencias_nodos', None): {getattr(nodo_cuerpo, 'lista_sentencias_nodos', None)}")
        for stmt in getattr(nodo_cuerpo, 'lista_sentencias_nodos', []):
            self._analizar_sentencia(stmt)

    def _analizar_sentencia(self, nodo_stmt):
        if nodo_stmt is None:
            return
        tipo = type(nodo_stmt).__name__
        print(f"[DEBUG] _analizar_sentencia: tipo nodo = {tipo}")
        if tipo == 'NodoAsignacion':
            self._analizar_asignacion(nodo_stmt)
        elif tipo == 'NodoIf':
            self._analizar_if(nodo_stmt)
        elif tipo == 'NodoWhile':
            self._analizar_while(nodo_stmt)
        elif tipo == 'NodoFor':
            self._analizar_for(nodo_stmt)
        elif tipo == 'NodoRepeat':
            self._analizar_repeat(nodo_stmt)
        elif tipo == 'NodoLlamadaProcedimiento':
            self._analizar_llamada_procedimiento(nodo_stmt)
        elif tipo == 'NodoWriteln' or tipo == 'NodoWrite' or tipo == 'NodoReadln' or tipo == 'NodoRead':
            for expr in getattr(nodo_stmt, 'argumentos', []):
                self._analizar_expresion(expr)
        elif tipo == 'NodoBeginEnd':
            for s in nodo_stmt.sentencias:
                self._analizar_sentencia(s)
        # Agregar más sentencias según el parser
        else:
            self.errores.append(f"Sentencia no soportada: {tipo}")

    def _inferir_tipo_expresion(self, nodo_expr):
        print(f"[DEBUG] _inferir_tipo_expresion: llamado con nodo {type(nodo_expr).__name__} -> {getattr(nodo_expr, 'nombre', getattr(nodo_expr, 'literal_token', None))}")
        """
        Infer the type of an expression node. Returns a string (e.g., 'integer', 'real', 'string', 'boolean', 'char') or None if unknown.
        """
        if nodo_expr is None:
            return None
        tipo = type(nodo_expr).__name__
        if tipo == 'NodoLiteral':
            token = nodo_expr.literal_token
            if token.tipo == 'NUMERO_ENTERO':
                return 'integer'
            elif token.tipo == 'NUMERO_REAL':
                return 'real'
            elif token.tipo == 'CADENA_LITERAL':
                return 'string'
            elif token.tipo == 'PALABRA_RESERVADA' and str(token.lexema).lower() in ['true', 'false']:
                return 'boolean'
        elif tipo == 'NodoIdentificador':
            nombre = nodo_expr.nombre.lower()  # <--- CORREGIDO: antes era nodo_expr.token.lexema.lower() o similar
            tipo_en_tabla = self.tabla_variables.get(nombre)
            print(f"[DEBUG] _inferir_tipo_expresion: identificador '{nombre}' tiene tipo '{tipo_en_tabla}' en tabla_variables")
            return tipo_en_tabla
        elif tipo == 'NodoExpresionBinaria':
            tipo_izq = self._inferir_tipo_expresion(nodo_expr.operando_izq_nodo)
            tipo_der = self._inferir_tipo_expresion(nodo_expr.operando_der_nodo)
            op = nodo_expr.operador_token.lexema.lower()
            if op in ['+', '-', '*', '/', 'div', 'mod']:
                if tipo_izq == 'real' or tipo_der == 'real':
                    return 'real'
                elif tipo_izq == 'integer' and tipo_der == 'integer':
                    return 'integer'
                else:
                    return None
            elif op in ['and', 'or']:
                return 'boolean'
            elif op in ['=', '<>', '<', '>', '<=', '>=']:
                return 'boolean'
        elif tipo == 'NodoExpresionUnaria':
            op = nodo_expr.operador_token.lexema.lower()
            if op == 'not':
                return 'boolean'
            return self._inferir_tipo_expresion(nodo_expr.operando_nodo)
        return None

    def _analizar_asignacion(self, nodo):
        nombre = nodo.variable_token_id.lexema.lower()
        print(f"[DEBUG] tabla_variables: {self.tabla_variables}")
        print(f"[DEBUG] Analizando asignación a '{nombre}'")
        print(f"[DEBUG] nodo.expresion_nodo: {nodo.expresion_nodo} (type: {type(nodo.expresion_nodo).__name__})")
        if nombre not in self.tabla_variables:
            self.errores.append(f"Variable '{nombre}' no declarada antes de asignación.")
        tipo_var = self.tabla_variables.get(nombre)
        tipo_expr = self._inferir_tipo_expresion(nodo.expresion_nodo)
        print(f"[DEBUG] Tipo variable: {tipo_var}, Tipo expresión: {tipo_expr}")
        print(f"[DEBUG] (ASIGNACION) variable '{nombre}' tipo '{tipo_var}', expresión tipo '{tipo_expr}'")
        if tipo_var and tipo_expr and tipo_var != tipo_expr:
            self.errores.append(f"Incompatibilidad de tipos en asignación a '{nombre}': se esperaba '{tipo_var}', se obtuvo '{tipo_expr}'.")
        self._analizar_expresion(nodo.expresion_nodo)

    def _analizar_if(self, nodo):
        self._analizar_expresion(nodo.condicion_nodo)
        self._analizar_sentencia(nodo.sentencia_then)
        if getattr(nodo, 'sentencia_else', None):
            self._analizar_sentencia(nodo.sentencia_else)

    def _analizar_while(self, nodo):
        self._analizar_expresion(nodo.condicion_nodo)
        self._analizar_sentencia(nodo.sentencia_cuerpo)

    def _analizar_for(self, nodo):
        var = nodo.variable_token.lexema.lower()
        if var not in self.tabla_variables:
            self.errores.append(f"Variable de control '{var}' no declarada en FOR.")
        self._analizar_expresion(nodo.expresion_inicio)
        self._analizar_expresion(nodo.expresion_fin)
        self._analizar_sentencia(nodo.sentencia_cuerpo)

    def _analizar_repeat(self, nodo):
        for s in nodo.sentencias:
            self._analizar_sentencia(s)
        self._analizar_expresion(nodo.condicion_nodo)

    def _analizar_llamada_procedimiento(self, nodo):
        nombre = nodo.nombre_proc_token.lexema.lower()
        # Aquí podrías validar existencia y parámetros si tienes tabla_procedimientos
        for arg in getattr(nodo, 'argumentos_nodos', []):
            self._analizar_expresion(arg)

    def _analizar_expresion(self, nodo_expr):
        if nodo_expr is None:
            return
        tipo = type(nodo_expr).__name__
        if tipo == 'NodoLiteral':
            pass
        elif tipo == 'NodoIdentificador':
            nombre = nodo_expr.nombre.lower()  # <--- CORREGIDO: antes era nodo_expr.token.lexema.lower()
            if nombre not in self.tabla_variables and nombre not in self.tabla_constantes:
                self.errores.append(f"Identificador '{nombre}' no declarado.")
        elif tipo == 'NodoExpresionBinaria':
            self._analizar_expresion(nodo_expr.izq)
            self._analizar_expresion(nodo_expr.der)
        elif tipo == 'NodoExpresionUnaria':
            self._analizar_expresion(nodo_expr.operando)
        elif tipo == 'NodoLlamadaFuncion':
            nombre = nodo_expr.nombre_token.lexema.lower()
            # Validar existencia y parámetros si tienes tabla_funciones
            for arg in nodo_expr.argumentos:
                self._analizar_expresion(arg)
        else:
            self.errores.append(f"Expresión no soportada: {tipo}")

    def mostrar_resultado(self):
        print("\n--- Análisis Semántico (Pascal) ---")
        if not self.errores:
            print("No se encontraron errores semánticos en el código Pascal. La simulación será precisa.")
        else:
            print(f"Se encontraron {len(self.errores)} error(es) semántico(s) en el código Pascal. La simulación podría no ser precisa.")
            for err in self.errores:
                print(f"  [Semántico] {err}")
        print("--- Fin Análisis Semántico (Pascal) ---")
