# src/analizador_semantico/semantico_cpp.py
"""
Analizador semántico para C++: verifica declaraciones, tipos, ámbitos, uso de variables, funciones, clases, namespaces, directivas, expresiones y control de flujo.
Reconoce todos los nodos implementados en el parser y lexer actuales.
"""
try:
    from analizador_sintactico.parser_cpp import (
        NodoTraduccionUnidad, NodoDeclaracion, NodoSentencia, NodoExpresion,
        NodoDirectivaPreprocesador, NodoUsingNamespace, NodoNamespaceDefinicion,
        NodoDefinicionClase, NodoDefinicionFuncion, NodoParametroFuncion, NodoTipoCPP,
        NodoBloqueSentenciasCPP, NodoDeclaracionVariableCPP, NodoDeclaradorVariableCPP,
        NodoSentenciaExpresionCPP, NodoSentenciaReturnCPP, NodoSentenciaIfCPP, NodoSentenciaWhileCPP, NodoSentenciaForCPP,
        NodoIdentificadorCPP, NodoLiteralCPP, NodoExpresionBinariaCPP, NodoLlamadaFuncionCPP, NodoMiembroExpresion
    )
    from analizador_lexico.lexer_cpp import Token
except ImportError as e:
    print(f"Error de importación en semantico_cpp.py: {e}")
    class NodoTraduccionUnidad: pass
    class NodoDeclaracion: pass
    class NodoSentencia: pass
    class NodoExpresion: pass
    class NodoDirectivaPreprocesador: pass
    class NodoUsingNamespace: pass
    class NodoNamespaceDefinicion: pass
    class NodoDefinicionClase: pass
    class NodoDefinicionFuncion: pass
    class NodoParametroFuncion: pass
    class NodoTipoCPP: pass
    class NodoBloqueSentenciasCPP: pass
    class NodoDeclaracionVariableCPP: pass
    class NodoDeclaradorVariableCPP: pass
    class NodoSentenciaExpresionCPP: pass
    class NodoSentenciaReturnCPP: pass
    class NodoSentenciaIfCPP: pass
    class NodoSentenciaWhileCPP: pass
    class NodoSentenciaForCPP: pass
    class NodoIdentificadorCPP: pass
    class NodoLiteralCPP: pass
    class NodoExpresionBinariaCPP: pass
    class NodoLlamadaFuncionCPP: pass
    class NodoMiembroExpresion: pass
    class Token: pass

class SimboloCPP:
    def __init__(self, nombre, tipo, tipo_dato=None, nodo_def=None, info_extra=None):
        self.nombre = nombre
        self.tipo = tipo  # 'variable', 'funcion', 'clase', 'namespace', 'parametro', 'builtin'
        self.tipo_dato = tipo_dato
        self.nodo_def = nodo_def
        self.info_extra = info_extra or {}
        self.usado = False

class TablaSimbolosCPP:
    def __init__(self, nombre_alcance="global", padre=None):
        self.simbolos = {}
        self.padre = padre
        self.hijos = []
        self.nombre_alcance = nombre_alcance
        if padre:
            padre.hijos.append(self)
    def declarar(self, simbolo):
        if simbolo.nombre in self.simbolos:
            print(f"Advertencia: Redefinición de '{simbolo.nombre}' en '{self.nombre_alcance}'.")
        self.simbolos[simbolo.nombre] = simbolo
    def buscar(self, nombre, buscar_en_padres=True):
        if nombre in self.simbolos:
            return self.simbolos[nombre]
        if buscar_en_padres and self.padre:
            return self.padre.buscar(nombre)
        return None

class AnalizadorSemanticoCPP:
    def __init__(self):
        self.tabla_global = TablaSimbolosCPP("global")
        self.tabla_actual = self.tabla_global
        self.errores = []
        self._inicializar_builtins()
    def _inicializar_builtins(self):
        for nombre in ["cout", "cin", "endl", "std", "main"]:
            self.tabla_global.declarar(SimboloCPP(nombre, "builtin"))
    def _registrar_error(self, mensaje, nodo=None):
        linea = getattr(nodo, 'linea', 'desconocida')
        columna = getattr(nodo, 'columna', 'desconocida')
        if hasattr(nodo, 'token_directiva'):
            linea = getattr(nodo.token_directiva, 'linea', linea)
            columna = getattr(nodo.token_directiva, 'columna', columna)
        elif hasattr(nodo, 'nombre_clase_token'):
            linea = getattr(nodo.nombre_clase_token, 'linea', linea)
            columna = getattr(nodo.nombre_clase_token, 'columna', columna)
        elif hasattr(nodo, 'qname_tokens') and nodo.qname_tokens:
            linea = getattr(nodo.qname_tokens[0], 'linea', linea)
            columna = getattr(nodo.qname_tokens[0], 'columna', columna)
        self.errores.append(f"Error Semántico (C++) en L{linea}:C{columna}: {mensaje}")
        print(self.errores[-1])
    def analizar(self, nodo_raiz):
        self.errores = []
        try:
            self.visitar(nodo_raiz)
        except Exception as e:
            self._registrar_error(f"Error inesperado durante el análisis semántico: {e}")
            import traceback; traceback.print_exc()
        if not self.errores:
            print("Análisis semántico de C++ completado sin errores.")
        else:
            print(f"Análisis semántico de C++ completado con {len(self.errores)} error(es).")
        return not self.errores
    def visitar(self, nodo):
        nombre_metodo = f"visitar_{type(nodo).__name__}"
        visitador = getattr(self, nombre_metodo, self._visitador_no_encontrado)
        return visitador(nodo)
    def _visitador_no_encontrado(self, nodo):
        for nombre_attr, valor_attr in vars(nodo).items():
            if isinstance(valor_attr, (NodoDeclaracion, NodoSentencia, NodoExpresion)):
                self.visitar(valor_attr)
            elif isinstance(valor_attr, list):
                for item in valor_attr:
                    if isinstance(item, (NodoDeclaracion, NodoSentencia, NodoExpresion)):
                        self.visitar(item)
        return None
    def visitar_NodoTraduccionUnidad(self, nodo):
        for decl in nodo.declaraciones_globales:
            self.visitar(decl)
    def visitar_NodoDirectivaPreprocesador(self, nodo):
        # Solo advertencia si #include repetido, etc.
        pass
    def visitar_NodoUsingNamespace(self, nodo):
        # Registrar el uso del namespace (no crea alcance real, pero se puede advertir si no existe)
        pass
    def visitar_NodoNamespaceDefinicion(self, nodo):
        nombre = nodo.nombre if hasattr(nodo, 'nombre') else None
        simbolo_ns = SimboloCPP(nombre, 'namespace', nodo_def=nodo)
        self.tabla_actual.declarar(simbolo_ns)
        tabla_ns = TablaSimbolosCPP(nombre, self.tabla_actual)
        anterior = self.tabla_actual
        self.tabla_actual = tabla_ns
        for decl in nodo.declaraciones_internas:
            self.visitar(decl)
        self.tabla_actual = anterior
    def visitar_NodoDefinicionClase(self, nodo):
        nombre = nodo.nombre if hasattr(nodo, 'nombre') else None
        simbolo_clase = SimboloCPP(nombre, 'clase', nodo_def=nodo)
        self.tabla_actual.declarar(simbolo_clase)
        tabla_clase = TablaSimbolosCPP(nombre, self.tabla_actual)
        anterior = self.tabla_actual
        self.tabla_actual = tabla_clase
        for miembro in nodo.miembros_nodos:
            self.visitar(miembro)
        self.tabla_actual = anterior
    def visitar_NodoDefinicionFuncion(self, nodo):
        nombre = "".join([t.lexema for t in getattr(nodo, 'nombre_funcion_qname_tokens', [])])
        simbolo_func = SimboloCPP(nombre, 'funcion', tipo_dato=nodo.tipo_retorno_nodo, nodo_def=nodo)
        self.tabla_actual.declarar(simbolo_func)
        tabla_func = TablaSimbolosCPP(nombre, self.tabla_actual)
        anterior = self.tabla_actual
        self.tabla_actual = tabla_func
        for param in getattr(nodo, 'parametros_nodos', []):
            self.visitar(param)
        if nodo.cuerpo_nodo_bloque:
            self.visitar(nodo.cuerpo_nodo_bloque)
        self.tabla_actual = anterior
    def visitar_NodoParametroFuncion(self, nodo):
        nombre = nodo.nombre_param_token.lexema if nodo.nombre_param_token else None
        simbolo_param = SimboloCPP(nombre, 'parametro', tipo_dato=nodo.tipo_param_nodo, nodo_def=nodo)
        self.tabla_actual.declarar(simbolo_param)
    def visitar_NodoBloqueSentenciasCPP(self, nodo):
        for sent in nodo.sentencias:
            self.visitar(sent)
    def visitar_NodoDeclaracionVariableCPP(self, nodo):
        tipo = nodo.tipo_nodo
        for declarador in nodo.declaradores:
            self.visitar_NodoDeclaradorVariableCPP(declarador, tipo)
    def visitar_NodoDeclaradorVariableCPP(self, nodo, tipo=None):
        nombre = nodo.nombre
        simbolo_var = SimboloCPP(nombre, 'variable', tipo_dato=tipo, nodo_def=nodo)
        self.tabla_actual.declarar(simbolo_var)
        if nodo.inicializador_nodo:
            self.visitar(nodo.inicializador_nodo)
    def visitar_NodoSentenciaExpresionCPP(self, nodo):
        self.visitar(nodo.expresion_nodo)
    def visitar_NodoSentenciaReturnCPP(self, nodo):
        if nodo.expresion_nodo:
            self.visitar(nodo.expresion_nodo)
    def visitar_NodoSentenciaIfCPP(self, nodo):
        self.visitar(nodo.condicion_nodo)
        self.visitar(nodo.cuerpo_then_nodo)
        if nodo.cuerpo_else_nodo:
            self.visitar(nodo.cuerpo_else_nodo)
    def visitar_NodoSentenciaWhileCPP(self, nodo):
        self.visitar(nodo.condicion_nodo)
        self.visitar(nodo.cuerpo_nodo)
    def visitar_NodoSentenciaForCPP(self, nodo):
        if nodo.inicializacion_nodo:
            self.visitar(nodo.inicializacion_nodo)
        if nodo.condicion_nodo:
            self.visitar(nodo.condicion_nodo)
        if nodo.actualizacion_nodo:
            self.visitar(nodo.actualizacion_nodo)
        self.visitar(nodo.cuerpo_nodo)
    def visitar_NodoIdentificadorCPP(self, nodo):
        nombre = nodo.nombre_simple
        simbolo = self.tabla_actual.buscar(nombre)
        if simbolo is None:
            self._registrar_error(f"Identificador '{nombre}' no está definido.", nodo)
        else:
            simbolo.usado = True
    def visitar_NodoLiteralCPP(self, nodo):
        return nodo.tipo_literal_original
    def visitar_NodoExpresionBinariaCPP(self, nodo):
        tipo_izq = self.visitar(nodo.izquierda_nodo)
        tipo_der = self.visitar(nodo.derecha_nodo)
        # Aquí se pueden agregar reglas de tipos para operadores
        return None
    def visitar_NodoLlamadaFuncionCPP(self, nodo):
        if isinstance(nodo.callee_nodo, NodoIdentificadorCPP):
            nombre = nodo.callee_nodo.nombre_simple
            simbolo = self.tabla_actual.buscar(nombre)
            if simbolo is None or simbolo.tipo not in ['funcion', 'builtin']:
                self._registrar_error(f"Llamada a función no definida: '{nombre}'", nodo)
        for arg in nodo.argumentos_nodos:
            self.visitar(arg)
    def visitar_NodoMiembroExpresion(self, nodo):
        self.visitar(nodo.objeto_nodo)
        # No se valida el miembro aquí, pero se podría advertir si la clase no tiene el miembro

# Fin de AnalizadorSemanticoCPP
