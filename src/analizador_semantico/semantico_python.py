# src/analizador_semantico/semantico_python.py

# Importar los nodos AST del parser de Python
try:
    from analizador_sintactico.parser_python import (
        NodoModulo, NodoSentencia, NodoExpresion, NodoDefinicionFuncion,
        NodoBloque, NodoSentenciaExpresion, NodoAsignacion, NodoLlamadaFuncion,
        NodoIdentificador, NodoLiteral, NodoExpresionBinaria, NodoSentenciaIf,
        NodoSentenciaReturn, NodoSentenciaWhile, NodoSentenciaFor,
        NodoExpresionUnaria, NodoSentenciaBreak, NodoSentenciaContinue
    )
    from analizador_lexico.lexer_python import Token 
    from analizador_lexico.lexer_python import PALABRAS_CLAVE_PYTHON
except ImportError as e_sem_py_import:
    print(f"Error de importación en semantico_python.py: {e_sem_py_import}")
    class NodoModulo: pass; 
    class NodoSentencia: pass; 
    class NodoExpresion: pass
    class NodoDefinicionFuncion: pass; 
    class NodoBloque: pass; 
    class NodoSentenciaExpresion: pass
    class NodoAsignacion: pass; 
    class NodoLlamadaFuncion: pass; 
    class NodoIdentificador: pass
    class NodoLiteral: pass; 
    class NodoExpresionBinaria: pass; 
    class NodoSentenciaIf: pass
    class NodoSentenciaReturn: pass; 
    class NodoSentenciaWhile: pass; 
    class NodoSentenciaFor: pass
    class NodoExpresionUnaria: pass; 
    class NodoSentenciaBreak: pass; 
    class NodoSentenciaContinue: pass
    class Token: pass

import builtins

BUILTIN_NAMES = set(dir(builtins))

class TipoSimbolo:
    VARIABLE = "VARIABLE"; FUNCION = "FUNCION"; PARAMETRO = "PARAMETRO"
    MODULO = "MODULO"; CLASE = "CLASE"; BUILTIN = "BUILTIN"

class Simbolo:
    def __init__(self, nombre, tipo_simbolo, tipo_dato=None, nodo_definicion=None, info_extra=None):
        self.nombre = nombre; self.tipo_simbolo = tipo_simbolo
        self.tipo_dato = tipo_dato; self.nodo_definicion = nodo_definicion
        self.usado = False; self.info_extra = info_extra if info_extra is not None else {}
    def __str__(self):
        return f"<Simbolo(nombre='{self.nombre}', tipo_simbolo='{self.tipo_simbolo}', tipo_dato='{self.tipo_dato}')>"

class TablaDeSimbolos:
    def __init__(self, nombre_alcance="global", padre=None, nodo_alcance=None):
        self.simbolos = {}; self.padre = padre; self.hijos = []
        self.nombre_alcance = nombre_alcance; self.nodo_alcance = nodo_alcance
        if padre: padre.hijos.append(self)

    def declarar(self, simbolo_obj):
        if simbolo_obj.nombre in self.simbolos:
            print(f"Advertencia Semántica: El símbolo '{simbolo_obj.nombre}' ya está declarado en el alcance '{self.nombre_alcance}'. Se sobrescribirá.")
        self.simbolos[simbolo_obj.nombre] = simbolo_obj
        return True

    def buscar(self, nombre_simbolo, buscar_en_padres=True):
        simbolo = self.simbolos.get(nombre_simbolo)
        if simbolo: return simbolo
        if buscar_en_padres and self.padre:
            return self.padre.buscar(nombre_simbolo, True)
        return None
    def __str__(self):
        return f"<TablaDeSimbolos(nombre='{self.nombre_alcance}', num_simbolos={len(self.simbolos)})>"

class AnalizadorSemanticoPython:
    def __init__(self):
        self.tabla_simbolos_global = TablaDeSimbolos(nombre_alcance="global_module")
        self.tabla_simbolos_actual = self.tabla_simbolos_global
        self.errores_semanticos = []
        self.bucles_anidados_contador = 0 # <-- NUEVO ATRIBUTO
        self._inicializar_builtins()

    def _inicializar_builtins(self):
        builtins = {
            'print': Simbolo('print', TipoSimbolo.BUILTIN, tipo_dato='function'),
            'range': Simbolo('range', TipoSimbolo.BUILTIN, tipo_dato='function'),
            'len': Simbolo('len', TipoSimbolo.BUILTIN, tipo_dato='function'),
            'int': Simbolo('int', TipoSimbolo.BUILTIN, tipo_dato='type'),
            'str': Simbolo('str', TipoSimbolo.BUILTIN, tipo_dato='type'),
            'float': Simbolo('float', TipoSimbolo.BUILTIN, tipo_dato='type'),
            'list': Simbolo('list', TipoSimbolo.BUILTIN, tipo_dato='type'),
            'dict': Simbolo('dict', TipoSimbolo.BUILTIN, tipo_dato='type'),
            'bool': Simbolo('bool', TipoSimbolo.BUILTIN, tipo_dato='type'),
        }
        for nombre, simbolo in builtins.items():
            self.tabla_simbolos_global.declarar(simbolo)

    def _registrar_error(self, mensaje, nodo_o_token=None):
        linea = 'desconocida'
        columna = 'desconocida'
        if isinstance(nodo_o_token, Token):
            linea = nodo_o_token.linea
            columna = nodo_o_token.columna
        elif hasattr(nodo_o_token, 'token'): # Para NodoSentenciaBreak/Continue
            linea = nodo_o_token.token.linea
            columna = nodo_o_token.token.columna
        elif hasattr(nodo_o_token, 'id_token') and nodo_o_token.id_token:
            linea = nodo_o_token.id_token.linea
            columna = nodo_o_token.id_token.columna
        elif hasattr(nodo_o_token, 'nombre_funcion_token'):
            linea = nodo_o_token.nombre_funcion_token.linea
            columna = nodo_o_token.nombre_funcion_token.columna
        # ... (más casos si es necesario)
        
        error_msg = f"Error Semántico (Python) en L{linea}:C{columna}: {mensaje}"
        self.errores_semanticos.append(error_msg)
        print(error_msg) 

    def analizar(self, nodo_raiz_ast):
        self.errores_semanticos = [] 
        self.bucles_anidados_contador = 0 # Reiniciar contador
        try:
            self.visitar(nodo_raiz_ast)
        except Exception as e:
            self._registrar_error(f"Error inesperado durante el análisis semántico: {e}")
            import traceback
            traceback.print_exc()
        
        if not self.errores_semanticos:
            print("Análisis semántico de Python completado sin errores.")
        else:
            print(f"Análisis semántico de Python completado con {len(self.errores_semanticos)} error(es).")
        return not self.errores_semanticos 

    def visitar(self, nodo):
        nombre_metodo_visitador = f'visitar_{type(nodo).__name__}'
        visitador = getattr(self, nombre_metodo_visitador, self._visitador_no_encontrado)
        return visitador(nodo)

    def _visitador_no_encontrado(self, nodo):
        # Consider all known AST node classes as base types for visiting
        AST_NODE_CLASSES = (
            NodoModulo, NodoSentencia, NodoExpresion, NodoDefinicionFuncion,
            NodoBloque, NodoSentenciaExpresion, NodoAsignacion, NodoLlamadaFuncion,
            NodoIdentificador, NodoLiteral, NodoExpresionBinaria, NodoSentenciaIf,
            NodoSentenciaReturn, NodoSentenciaWhile, NodoSentenciaFor,
            NodoExpresionUnaria, NodoSentenciaBreak, NodoSentenciaContinue
        )
        for nombre_attr, valor_attr in vars(nodo).items():
            if isinstance(valor_attr, AST_NODE_CLASSES):
                self.visitar(valor_attr)
            elif isinstance(valor_attr, list):
                for item in valor_attr:
                    if isinstance(item, AST_NODE_CLASSES):
                        self.visitar(item)
        return None 

    def visitar_NodoModulo(self, nodo_modulo):
        self.tabla_simbolos_actual.nodo_alcance = nodo_modulo # Asociar nodo con el alcance
        for sentencia in nodo_modulo.cuerpo_sentencias:
            self.visitar(sentencia)

    def visitar_NodoBloque(self, nodo_bloque):
        # Un bloque en Python no crea un nuevo alcance por sí mismo,
        # excepto el bloque de una función o clase.
        # El alcance se maneja en visitar_NodoDefinicionFuncion, etc.
        for sentencia in nodo_bloque.sentencias:
            self.visitar(sentencia)
    
    def visitar_NodoDefinicionFuncion(self, nodo_def_func):
        nombre_funcion = nodo_def_func.nombre_funcion_token.lexema
        # Check for reserved keyword usage as function name
        if nombre_funcion in PALABRAS_CLAVE_PYTHON:
            self._registrar_error(f"El nombre de función '{nombre_funcion}' es una palabra reservada de Python.", nodo_def_func.nombre_funcion_token)
        # Check for duplicate parameter names
        nombres_params = [p.lexema for p in nodo_def_func.parametros_tokens]
        if len(set(nombres_params)) != len(nombres_params):
            self._registrar_error(f"Parámetros duplicados en la definición de la función '{nombre_funcion}'.", nodo_def_func.nombre_funcion_token)
        # Check for shadowing builtins or function name
        for param_token in nodo_def_func.parametros_tokens:
            if param_token.lexema in PALABRAS_CLAVE_PYTHON:
                self._registrar_error(f"El parámetro '{param_token.lexema}' es una palabra reservada de Python.", param_token)
            if param_token.lexema == nombre_funcion:
                self._registrar_error(f"El parámetro '{param_token.lexema}' tiene el mismo nombre que la función.", param_token)
        # ...existing code for function declaration and scope...
        simbolo_funcion = Simbolo(nombre_funcion, TipoSimbolo.FUNCION, 
                                  tipo_dato='function', 
                                  nodo_definicion=nodo_def_func,
                                  info_extra={'parametros': nombres_params, 'num_params': len(nombres_params)})
        self.tabla_simbolos_actual.declarar(simbolo_funcion)

        alcance_anterior = self.tabla_simbolos_actual
        self.tabla_simbolos_actual = TablaDeSimbolos(nombre_alcance=f"funcion_{nombre_funcion}", padre=alcance_anterior, nodo_alcance=nodo_def_func)
        
        for param_token in nodo_def_func.parametros_tokens:
            simbolo_param = Simbolo(param_token.lexema, TipoSimbolo.PARAMETRO, nodo_definicion=param_token) 
            self.tabla_simbolos_actual.declarar(simbolo_param)
            
        # Check for unreachable code after return/break/continue in function body
        self._check_unreachable_in_block(nodo_def_func.cuerpo_bloque_nodo)
        self.tabla_simbolos_actual = alcance_anterior 
        return None 

    def visitar_NodoAsignacion(self, nodo_asignacion):
        nombre_variable = nodo_asignacion.objetivo_nodo.nombre
        # Solo advertir si sobrescribe un nombre builtin real
        if nombre_variable in PALABRAS_CLAVE_PYTHON:
            self._registrar_error(f"El nombre de variable '{nombre_variable}' es una palabra reservada de Python.", nodo_asignacion.objetivo_nodo.id_token)
        elif nombre_variable in BUILTIN_NAMES:
            self._registrar_error(f"La variable '{nombre_variable}' sobrescribe un nombre builtin de Python.", nodo_asignacion.objetivo_nodo.id_token)
        # ...existing code for assignment...
        tipo_valor_asignado = self.visitar(nodo_asignacion.valor_nodo)
        simbolo_existente = self.tabla_simbolos_actual.buscar(nombre_variable, buscar_en_padres=False)
        if simbolo_existente:
            simbolo_existente.tipo_dato = tipo_valor_asignado
            simbolo_existente.nodo_definicion = nodo_asignacion
        else:
            simbolo_variable = Simbolo(nombre_variable, TipoSimbolo.VARIABLE, tipo_valor_asignado, nodo_asignacion)
            self.tabla_simbolos_actual.declarar(simbolo_variable)
        return None

    def visitar_NodoIdentificador(self, nodo_id):
        nombre_id = nodo_id.nombre
        simbolo = self.tabla_simbolos_actual.buscar(nombre_id)
        if simbolo is None:
            self._registrar_error(f"Nombre '{nombre_id}' no está definido.", nodo_id.id_token)
            return "tipo_desconocido_error" 
        simbolo.usado = True 
        return simbolo.tipo_dato 

    def visitar_NodoLiteral(self, nodo_literal):
        if isinstance(nodo_literal.valor, int): return "int"
        if isinstance(nodo_literal.valor, float): return "float"
        if isinstance(nodo_literal.valor, str): return "str"
        if isinstance(nodo_literal.valor, bool): return "bool"
        if nodo_literal.valor is None: return "NoneType"
        return "tipo_desconocido_literal"

    def visitar_NodoLlamadaFuncion(self, nodo_llamada):
        nombre_funcion = None
        if isinstance(nodo_llamada.callee_nodo, NodoIdentificador):
            nombre_funcion = nodo_llamada.callee_nodo.nombre
        else:
            self._registrar_error("Llamadas a métodos de objetos no soportadas aún.", nodo_llamada.callee_nodo)
            return "tipo_desconocido_error"

        simbolo_funcion = self.tabla_simbolos_actual.buscar(nombre_funcion)
        if simbolo_funcion is None:
            self._registrar_error(f"Función '{nombre_funcion}' no definida.", nodo_llamada.callee_nodo.id_token if hasattr(nodo_llamada.callee_nodo, 'id_token') else nodo_llamada.callee_nodo)
            return "tipo_desconocido_error"
        
        if simbolo_funcion.tipo_simbolo not in [TipoSimbolo.FUNCION, TipoSimbolo.BUILTIN]:
            self._registrar_error(f"'{nombre_funcion}' no es una función.", nodo_llamada.callee_nodo.id_token if hasattr(nodo_llamada.callee_nodo, 'id_token') else nodo_llamada.callee_nodo)
            return "tipo_desconocido_error"

        num_args_esperados = simbolo_funcion.info_extra.get('num_params') if simbolo_funcion.info_extra else None
        num_args_provistos = len(nodo_llamada.argumentos_nodos)

        if num_args_esperados is not None and num_args_provistos != num_args_esperados:
            if simbolo_funcion.tipo_simbolo != TipoSimbolo.BUILTIN or nombre_funcion not in ['print']: 
                self._registrar_error(f"Función '{nombre_funcion}' espera {num_args_esperados} argumento(s), pero se proveyeron {num_args_provistos}.", nodo_llamada.callee_nodo)
        
        for arg_nodo in nodo_llamada.argumentos_nodos:
            self.visitar(arg_nodo)
        
        if nombre_funcion == 'range': return "iterable" 
        if nombre_funcion == 'len': return "int"
        if nombre_funcion in ['int', 'str', 'float', 'bool']: return nombre_funcion 
        return simbolo_funcion.info_extra.get('tipo_retorno', 'any') 

    def visitar_NodoExpresionBinaria(self, nodo_bin):
        tipo_izq = self.visitar(nodo_bin.izquierda_nodo)
        tipo_der = self.visitar(nodo_bin.derecha_nodo)
        op = nodo_bin.operador_token.lexema
        if op in ['+', '-', '*', '/', '//', '%', '**']:
            if not (tipo_izq in ["int", "float", "any", "tipo_desconocido_error"] and tipo_der in ["int", "float", "any", "tipo_desconocido_error"]):
                if op == '+' and tipo_izq == "str" and tipo_der == "str": return "str"
                self._registrar_error(f"Operador '{op}' no soporta operandos de tipo '{tipo_izq}' y '{tipo_der}'.", nodo_bin.operador_token)
            if tipo_izq == "float" or tipo_der == "float": return "float"
            if tipo_izq == "str" or tipo_der == "str": return "str" # Para concatenación con +
            return "int"
        elif op in ['<', '>', '<=', '>=', '==', '!=', 'is', 'is not', 'in', 'not in']:
            return "bool"
        elif op in ['and', 'or']:
            return "bool" 
        return "any" 

    def visitar_NodoExpresionUnaria(self, nodo_un):
        tipo_operando = self.visitar(nodo_un.operando_nodo)
        op = nodo_un.operador_token.lexema
        if op == 'not': return "bool"
        elif op in ['+', '-']: 
            if tipo_operando not in ["int", "float", "any", "tipo_desconocido_error"]:
                self._registrar_error(f"Operador unario '{op}' no soporta operando de tipo '{tipo_operando}'.", nodo_un.operador_token)
            return tipo_operando 
        return "any"
        
    def visitar_NodoSentenciaExpresion(self, nodo_sent_expr):
        self.visitar(nodo_sent_expr.expresion_nodo) 
        return None

    def visitar_NodoSentenciaIf(self, nodo_if):
        self.visitar(nodo_if.prueba_nodo) 
        self.visitar(nodo_if.cuerpo_then_nodo) 
        if nodo_if.cuerpo_else_nodo:
            self.visitar(nodo_if.cuerpo_else_nodo) 
        return None

    def visitar_NodoSentenciaReturn(self, nodo_return):
        tipo_retorno = "NoneType"
        if nodo_return.valor_retorno_nodo:
            tipo_retorno = self.visitar(nodo_return.valor_retorno_nodo)
        alcance_funcion_actual = self.tabla_simbolos_actual
        en_funcion = False
        while alcance_funcion_actual:
            if alcance_funcion_actual.nodo_alcance and isinstance(alcance_funcion_actual.nodo_alcance, NodoDefinicionFuncion):
                en_funcion = True
                break
            alcance_funcion_actual = alcance_funcion_actual.padre
        if not en_funcion:
            self._registrar_error("'return' fuera de una función.", nodo_return) 
        return None 

    # --- MÉTODOS VISITADORES PARA BUCLES ACTUALIZADOS ---
    def visitar_NodoSentenciaWhile(self, nodo_while):
        self.visitar(nodo_while.condicion_nodo)
        self.bucles_anidados_contador += 1
        try:
            self.visitar(nodo_while.cuerpo_bloque_nodo)
        finally:
            self.bucles_anidados_contador -= 1
        return None

    def visitar_NodoSentenciaFor(self, nodo_for):
        nombre_var_iter = nodo_for.variable_iteracion_token.lexema
        tipo_iterable = self.visitar(nodo_for.expresion_iterable_nodo)
        
        # Simular la declaración de la variable de iteración en el alcance actual
        # En Python, la variable del bucle for es accesible después del bucle.
        # Si ya existe, se sobrescribe.
        simbolo_var_iter = Simbolo(nombre_var_iter, TipoSimbolo.VARIABLE, tipo_dato="any", nodo_definicion=nodo_for.variable_iteracion_token)
        self.tabla_simbolos_actual.declarar(simbolo_var_iter) 

        self.bucles_anidados_contador += 1
        try:
            self.visitar(nodo_for.cuerpo_bloque_nodo)
        finally:
            self.bucles_anidados_contador -= 1
        return None

    def visitar_NodoSentenciaBreak(self, nodo_break):
        if self.bucles_anidados_contador == 0:
            self._registrar_error("'break' fuera de un bucle.", nodo_break.token) # Usar el token almacenado
        return None

    def visitar_NodoSentenciaContinue(self, nodo_continue):
        if self.bucles_anidados_contador == 0:
            self._registrar_error("'continue' fuera de un bucle.", nodo_continue.token) # Usar el token almacenado
        return None

    def _check_unreachable_in_block(self, nodo_bloque):
        """Check for unreachable code after return, break, or continue in a block."""
        found_terminal = False
        for sentencia in getattr(nodo_bloque, 'sentencias', []):
            if found_terminal:
                self._registrar_error("Código inalcanzable después de 'return', 'break' o 'continue'.", getattr(sentencia, 'token', None))
            if isinstance(sentencia, (NodoSentenciaReturn, NodoSentenciaBreak, NodoSentenciaContinue)):
                found_terminal = True
            # Recursively check nested blocks
            if hasattr(sentencia, 'cuerpo_bloque_nodo'):
                self._check_unreachable_in_block(sentencia.cuerpo_bloque_nodo)
            if hasattr(sentencia, 'cuerpo_then_nodo'):
                self._check_unreachable_in_block(sentencia.cuerpo_then_nodo)
            if hasattr(sentencia, 'cuerpo_else_nodo') and sentencia.cuerpo_else_nodo:
                self._check_unreachable_in_block(sentencia.cuerpo_else_nodo)

# Fin de la clase AnalizadorSemanticoPython
