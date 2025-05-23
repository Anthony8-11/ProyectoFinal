# src/analizador_semantico/semantico_javascript.py
"""
Analizador semántico para JavaScript: verifica declaraciones, ámbitos, uso de variables, funciones, tipos de literales, control de flujo, objetos, arrays y expresiones.
Reconoce todos los nodos implementados en el lexer y parser actuales.
"""
try:
    from analizador_sintactico.parser_javascript import (
        NodoProgramaJS, NodoSentencia, NodoExpresion,
        NodoDeclaracionVariable, NodoDeclaradorVariable,
        NodoDeclaracionFuncion, NodoBloqueSentencias,
        NodoSentenciaExpresion, NodoSentenciaIf, NodoSentenciaReturn, NodoBucleFor,
        NodoIdentificadorJS, NodoLiteralJS, NodoAsignacionExpresion,
        NodoExpresionBinariaJS, NodoLlamadaExpresion, NodoMiembroExpresion,
        NodoExpresionActualizacion, NodoArrayLiteralJS, NodoObjetoLiteralJS, NodoPropiedadObjetoJS
    )
    from analizador_lexico.lexer_javascript import Token
except ImportError as e:
    print(f"Error de importación en semantico_javascript.py: {e}")
    class NodoProgramaJS: pass
    class NodoSentencia: pass
    class NodoExpresion: pass
    class NodoDeclaracionVariable: pass
    class NodoDeclaradorVariable: pass
    class NodoDeclaracionFuncion: pass
    class NodoBloqueSentencias: pass
    class NodoSentenciaExpresion: pass
    class NodoSentenciaIf: pass
    class NodoSentenciaReturn: pass
    class NodoBucleFor: pass
    class NodoIdentificadorJS: pass
    class NodoLiteralJS: pass
    class NodoAsignacionExpresion: pass
    class NodoExpresionBinariaJS: pass
    class NodoLlamadaExpresion: pass
    class NodoMiembroExpresion: pass
    class NodoExpresionActualizacion: pass
    class NodoArrayLiteralJS: pass
    class NodoObjetoLiteralJS: pass
    class NodoPropiedadObjetoJS: pass
    class Token: pass

class SimboloJS:
    def __init__(self, nombre, tipo, tipo_dato=None, nodo_def=None, info_extra=None):
        self.nombre = nombre
        self.tipo = tipo  # 'variable', 'funcion', 'parametro', 'builtin'
        self.tipo_dato = tipo_dato
        self.nodo_def = nodo_def
        self.info_extra = info_extra or {}
        self.usado = False

class TablaSimbolosJS:
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

class AnalizadorSemanticoJS:
    def __init__(self):
        self.tabla_global = TablaSimbolosJS("global")
        self.tabla_actual = self.tabla_global
        self.errores = []
        self._inicializar_builtins()
    def _inicializar_builtins(self):
        for nombre in ["console", "log", "alert", "window", "document", "parseInt", "parseFloat", "isNaN", "isFinite", "Array", "Object", "String", "Number", "Boolean", "Math", "Date", "JSON"]:
            self.tabla_global.declarar(SimboloJS(nombre, "builtin"))
    def _registrar_error(self, mensaje, nodo=None):
        linea = getattr(nodo, 'linea', 'desconocida')
        columna = getattr(nodo, 'columna', 'desconocida')
        if hasattr(nodo, 'token_id'):
            linea = getattr(nodo.token_id, 'linea', linea)
            columna = getattr(nodo.token_id, 'columna', columna)
        elif hasattr(nodo, 'token_literal'):
            linea = getattr(nodo.token_literal, 'linea', linea)
            columna = getattr(nodo.token_literal, 'columna', columna)
        elif hasattr(nodo, 'identificador_token'):
            linea = getattr(nodo.identificador_token, 'linea', linea)
            columna = getattr(nodo.identificador_token, 'columna', columna)
        elif hasattr(nodo, 'nombre_funcion_token'):
            linea = getattr(nodo.nombre_funcion_token, 'linea', linea)
            columna = getattr(nodo.nombre_funcion_token, 'columna', columna)
        self.errores.append(f"Error Semántico (JS) en L{linea}:C{columna}: {mensaje}")
        print(self.errores[-1])
    def analizar(self, nodo_raiz):
        self.errores = []
        try:
            self.visitar(nodo_raiz)
        except Exception as e:
            self._registrar_error(f"Error inesperado durante el análisis semántico: {e}")
            import traceback; traceback.print_exc()
        if not self.errores:
            print("Análisis semántico de JavaScript completado sin errores.")
        else:
            print(f"Análisis semántico de JavaScript completado con {len(self.errores)} error(es).")
        return not self.errores
    def visitar(self, nodo):
        nombre_metodo = f"visitar_{type(nodo).__name__}"
        visitador = getattr(self, nombre_metodo, self._visitador_no_encontrado)
        return visitador(nodo)
    def _visitador_no_encontrado(self, nodo):
        AST_NODE_CLASSES = (
            NodoProgramaJS, NodoSentencia, NodoExpresion, NodoDeclaracionVariable, NodoDeclaradorVariable,
            NodoDeclaracionFuncion, NodoBloqueSentencias, NodoSentenciaExpresion, NodoSentenciaIf, NodoSentenciaReturn, NodoBucleFor,
            NodoIdentificadorJS, NodoLiteralJS, NodoAsignacionExpresion, NodoExpresionBinariaJS, NodoLlamadaExpresion, NodoMiembroExpresion,
            NodoExpresionActualizacion, NodoArrayLiteralJS, NodoObjetoLiteralJS, NodoPropiedadObjetoJS
        )
        for nombre_attr, valor_attr in vars(nodo).items():
            if isinstance(valor_attr, AST_NODE_CLASSES):
                self.visitar(valor_attr)
            elif isinstance(valor_attr, list):
                for item in valor_attr:
                    if isinstance(item, AST_NODE_CLASSES):
                        self.visitar(item)
        return None
    def visitar_NodoProgramaJS(self, nodo):
        for sent in nodo.cuerpo:
            self.visitar(sent)
    def visitar_NodoBloqueSentencias(self, nodo):
        # Usar el atributo correcto 'cuerpo_sentencias' en vez de 'sentencias'
        for sent in nodo.cuerpo_sentencias:
            self.visitar(sent)
    def visitar_NodoDeclaracionVariable(self, nodo):
        tipo_decl = nodo.tipo_declaracion
        for declarador in nodo.declaraciones:
            self.visitar_NodoDeclaradorVariable(declarador, tipo_decl)
    def visitar_NodoDeclaradorVariable(self, nodo, tipo_decl=None):
        nombre = nodo.nombre
        simbolo = SimboloJS(nombre, 'variable', nodo_def=nodo, info_extra={'tipo_decl': tipo_decl})
        self.tabla_actual.declarar(simbolo)
        if nodo.valor_inicial_nodo:
            self.visitar(nodo.valor_inicial_nodo)
    def visitar_NodoDeclaracionFuncion(self, nodo):
        nombre = nodo.nombre
        simbolo_func = SimboloJS(nombre, 'funcion', nodo_def=nodo, info_extra={'parametros': [p.lexema for p in nodo.parametros_tokens]})
        self.tabla_actual.declarar(simbolo_func)
        tabla_func = TablaSimbolosJS(nombre, self.tabla_actual)
        anterior = self.tabla_actual
        self.tabla_actual = tabla_func
        for param_token in nodo.parametros_tokens:
            simbolo_param = SimboloJS(param_token.lexema, 'parametro', nodo_def=param_token)
            self.tabla_actual.declarar(simbolo_param)
        self.visitar(nodo.cuerpo_nodo_bloque)
        self.tabla_actual = anterior
    def visitar_NodoSentenciaExpresion(self, nodo):
        self.visitar(nodo.expresion_nodo)
    def visitar_NodoSentenciaIf(self, nodo):
        # Usar los nombres correctos de atributos según el AST: prueba_nodo, consecuente_nodo, alternativo_nodo
        self.visitar(nodo.prueba_nodo)
        self.visitar(nodo.consecuente_nodo)
        if nodo.alternativo_nodo:
            self.visitar(nodo.alternativo_nodo)
    def visitar_NodoSentenciaReturn(self, nodo):
        if nodo.argumento_nodo:
            self.visitar(nodo.argumento_nodo)
    def visitar_NodoBucleFor(self, nodo):
        if nodo.inicializacion_nodo:
            self.visitar(nodo.inicializacion_nodo)
        if nodo.condicion_nodo:
            self.visitar(nodo.condicion_nodo)
        if nodo.actualizacion_nodo:
            self.visitar(nodo.actualizacion_nodo)
        self.visitar(nodo.cuerpo_nodo)
    def visitar_NodoIdentificadorJS(self, nodo):
        nombre = nodo.nombre
        simbolo = self.tabla_actual.buscar(nombre)
        if simbolo is None:
            self._registrar_error(f"Identificador '{nombre}' no está definido.", nodo)
        else:
            simbolo.usado = True
    def visitar_NodoLiteralJS(self, nodo):
        return type(nodo.valor).__name__
    def visitar_NodoAsignacionExpresion(self, nodo):
        self.visitar(nodo.izquierda_nodo)
        self.visitar(nodo.derecha_nodo)
    def visitar_NodoExpresionBinariaJS(self, nodo):
        self.visitar(nodo.izquierda_nodo)
        self.visitar(nodo.derecha_nodo)
    def visitar_NodoLlamadaExpresion(self, nodo):
        self.visitar(nodo.callee_nodo)
        for arg in nodo.argumentos_nodos:
            self.visitar(arg)
    def visitar_NodoMiembroExpresion(self, nodo):
        self.visitar(nodo.objeto_nodo)
        self.visitar(nodo.propiedad_nodo)
    def visitar_NodoExpresionActualizacion(self, nodo):
        # Usar el atributo correcto 'argumento_nodo' en vez de 'objetivo_nodo'
        self.visitar(nodo.argumento_nodo)
    def visitar_NodoArrayLiteralJS(self, nodo):
        # Usar el atributo correcto 'elementos_nodos' en vez de 'elementos'
        for elem in getattr(nodo, 'elementos_nodos', []):
            self.visitar(elem)
    def visitar_NodoObjetoLiteralJS(self, nodo):
        # Usar el atributo correcto 'propiedades_nodos' en vez de 'propiedades'
        for prop in getattr(nodo, 'propiedades_nodos', []):
            self.visitar(prop)
    def visitar_NodoPropiedadObjetoJS(self, nodo):
        self.visitar(nodo.valor_nodo)
# Fin de AnalizadorSemanticoJS
