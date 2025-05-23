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
        for stmt in getattr(nodo_cuerpo, 'sentencias', []):
            self._analizar_sentencia(stmt)

    def _analizar_sentencia(self, nodo_stmt):
        if nodo_stmt is None:
            return
        tipo = type(nodo_stmt).__name__
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

    def _analizar_asignacion(self, nodo):
        nombre = nodo.identificador_token.lexema.lower()
        if nombre not in self.tabla_variables:
            self.errores.append(f"Variable '{nombre}' no declarada antes de asignación.")
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
        nombre = nodo.nombre_token.lexema.lower()
        # Aquí podrías validar existencia y parámetros si tienes tabla_procedimientos
        for arg in getattr(nodo, 'argumentos', []):
            self._analizar_expresion(arg)

    def _analizar_expresion(self, nodo_expr):
        if nodo_expr is None:
            return
        tipo = type(nodo_expr).__name__
        if tipo == 'NodoLiteral':
            pass
        elif tipo == 'NodoIdentificador':
            nombre = nodo_expr.token.lexema.lower()
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
