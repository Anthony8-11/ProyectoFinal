# src/simulador_ejecucion/interprete_cpp.py

# Importar las clases de nodos AST necesarias desde el parser_cpp.
try:
    from analizador_sintactico.parser_cpp import (
        NodoTraduccionUnidad, NodoDeclaracion, NodoSentencia, NodoExpresion,
        NodoDirectivaPreprocesador, NodoUsingNamespace, NodoNamespaceDefinicion,
        NodoDefinicionClase, NodoDefinicionFuncion, NodoParametroFuncion, NodoTipoCPP,
        NodoBloqueSentenciasCPP, NodoDeclaracionVariableCPP, NodoDeclaradorVariableCPP,
        NodoSentenciaExpresionCPP, NodoSentenciaReturnCPP, NodoSentenciaIfCPP, NodoSentenciaWhileCPP, NodoSentenciaForCPP,
        NodoIdentificadorCPP, NodoLiteralCPP, NodoExpresionBinariaCPP, NodoLlamadaFuncionCPP,
        NodoMiembroExpresion 
    )
    from analizador_lexico.lexer_cpp import Token, TT_OPERADOR_BITWISE, TT_OPERADOR_COMPARACION, TT_OPERADOR_ARITMETICO, TT_ASTERISCO, TT_PALABRA_CLAVE, TT_OPERADOR_ASIGNACION
except ImportError as e_import_ast_interprete_cpp:
    print(f"ADVERTENCIA CRÍTICA (InterpreteCPP): No se pudieron importar los nodos AST desde 'parser_cpp.py'. Error: {e_import_ast_interprete_cpp}")
    # Definir placeholders muy básicos
    class NodoTraduccionUnidad: pass; 
    class NodoDeclaracion: pass; 
    class NodoSentencia: pass
    class NodoExpresion: pass; 
    class NodoDirectivaPreprocesador: pass; 
    class NodoUsingNamespace: pass
    class NodoNamespaceDefinicion: pass; 
    class NodoDefinicionClase: pass; 
    class NodoDefinicionFuncion: pass
    class NodoParametroFuncion: pass; 
    class NodoTipoCPP: pass; 
    class NodoBloqueSentenciasCPP: pass
    class NodoDeclaracionVariableCPP: pass; 
    class NodoDeclaradorVariableCPP: pass
    class NodoSentenciaExpresionCPP: pass; 
    class NodoSentenciaReturnCPP: pass
    class NodoIdentificadorCPP: pass; 
    class NodoLiteralCPP: pass; 
    class NodoExpresionBinariaCPP: pass
    class NodoLlamadaFuncionCPP: pass
    class NodoSentenciaIfCPP: pass
    class NodoSentenciaWhielCPP: pass
    class NodoSetnenciaForCPP: pass
    class Token: pass 
    class Token: pass; TT_OPERADOR_BITWISE = "OPERADOR_BITWISE_CPP"; TT_OPERADOR_COMPARACION = "OPERADOR_COMPARACION_CPP"; TT_OPERADOR_ARITMETICO = "OPERADOR_ARITMETICO_CPP"; TT_ASTERISCO = "ASTERISCO_CPP"; TT_PALABRA_CLAVE = "PALABRA_CLAVE_CPP"

class ErrorTiempoEjecucionCPP(RuntimeError):
    pass
class ErrorRetornoCPP(Exception):
    def __init__(self, valor):
        super().__init__("Sentencia return ejecutada")
        self.valor = valor

class AlcanceCPP:
    def __init__(self, padre=None, nombre_alcance="global"): 
        self.simbolos = {} 
        self.padre = padre   
        self.objetos_globales_cpp_ref = None 
        self.nombre_alcance = nombre_alcance 

    def declarar(self, nombre, valor, tipo_simbolo="variable"):
        # print(f"[AlcanceCPP DEBUG ({self.nombre_alcance})] Declarando '{nombre}' (tipo: {tipo_simbolo})")
        if nombre in self.simbolos and tipo_simbolo != "objeto_global_usado" and tipo_simbolo != "miembro_clase": 
            pass 
        self.simbolos[nombre] = {'valor': valor, 'tipo_simbolo': tipo_simbolo}
    def asignar(self, nombre, valor):
        alcance_busqueda = self
        while alcance_busqueda:
            if nombre in alcance_busqueda.simbolos and alcance_busqueda.simbolos[nombre]['tipo_simbolo'] == "variable":
                alcance_busqueda.simbolos[nombre]['valor'] = valor
                return
            alcance_busqueda = alcance_busqueda.padre
        raise ErrorTiempoEjecucionCPP(f"Variable no declarada '{nombre}' (error en asignación).")
    def obtener(self, nombre, buscar_en_globales_directo=True):
        # print(f"[AlcanceCPP DEBUG ({self.nombre_alcance})] Obteniendo '{nombre}'")
        alcance_busqueda = self
        while alcance_busqueda:
            if nombre in alcance_busqueda.simbolos:
                return alcance_busqueda.simbolos[nombre]['valor'] 
            alcance_busqueda = alcance_busqueda.padre
        if buscar_en_globales_directo and self.objetos_globales_cpp_ref:
            partes_nombre = nombre.split('::')
            if len(partes_nombre) == 1 and partes_nombre[0] in self.objetos_globales_cpp_ref:
                 return self.objetos_globales_cpp_ref[partes_nombre[0]]
            if len(partes_nombre) == 2 and partes_nombre[0] in self.objetos_globales_cpp_ref and \
               isinstance(self.objetos_globales_cpp_ref[partes_nombre[0]], dict) and \
               partes_nombre[1] in self.objetos_globales_cpp_ref[partes_nombre[0]]:
                return self.objetos_globales_cpp_ref[partes_nombre[0]][partes_nombre[1]]
        raise ErrorTiempoEjecucionCPP(f"Símbolo no declarado '{nombre}'.")

class FuncionDefinidaCPP:
    def __init__(self, nombre_qname_tokens, parametros_nodos, cuerpo_nodo, alcance_definicion, clase_contenedora=None):
        self.nombre_completo = "".join([t.lexema for t in nombre_qname_tokens])
        self.nombre_simple = nombre_qname_tokens[-1].lexema if nombre_qname_tokens else "anónima"
        self.nombres_parametros = [p.nombre_param_token.lexema for p in parametros_nodos if p.nombre_param_token]
        self.cuerpo_nodo = cuerpo_nodo 
        self.alcance_definicion = alcance_definicion
        self.clase_contenedora = clase_contenedora 
    def __repr__(self):
        return f"<FuncionCPP: {self.nombre_completo}({', '.join(self.nombres_parametros)})>"

class ClaseDefinidaCPP:
    def __init__(self, nombre_clase_completo): 
        self.nombre_clase_completo = nombre_clase_completo 
        self.nombre_simple = nombre_clase_completo.split('::')[-1]
        self.metodos = {} 
        self.miembros_variables_ast = [] 
    def agregar_metodo(self, funcion_obj):
        self.metodos[funcion_obj.nombre_simple] = funcion_obj 
    def __repr__(self):
        return f"<ClaseCPP: {self.nombre_clase_completo}>"

class InstanciaClaseCPP:
    def __init__(self, definicion_clase_obj):
        self.definicion_clase = definicion_clase_obj 
        self.miembros_datos = {} 
    def __repr__(self):
        return f"<Instancia de {self.definicion_clase.nombre_clase_completo}>"

class MetodoEnlazado:
    def __init__(self, instancia_obj, metodo_obj):
        self.instancia = instancia_obj 
        self.metodo = metodo_obj     
    def __repr__(self):
        return f"<MetodoEnlazado: {self.instancia.definicion_clase.nombre_clase_completo}::{self.metodo.nombre_simple}>"

class InterpreteCPP:
    def __init__(self):
        self.alcance_global = AlcanceCPP(nombre_alcance="global")
        self.alcance_actual = self.alcance_global
        self.catalogo_clases = {} 
        self.objetos_globales_cpp = {
            'std': { 'cout': self._simular_std_cout, 'endl': '\n', 'cin': None }
        }
        self.alcance_global.objetos_globales_cpp_ref = self.objetos_globales_cpp 
        self.alcance_global.declarar('std', self.objetos_globales_cpp['std'], tipo_simbolo="namespace_objeto")
        self.buffer_cout = [] 
        self.namespace_actual_prefijo = "" 

    def _simular_std_cout(self, valor_a_imprimir):
        self.buffer_cout.append(str(valor_a_imprimir))
        if valor_a_imprimir == '\n': 
            print("".join(self.buffer_cout), end="") 
            self.buffer_cout = []
        return self.objetos_globales_cpp['std']['cout'] 

    def interpretar_unidad_traduccion(self, nodo_traduccion):
        if not isinstance(nodo_traduccion, NodoTraduccionUnidad):
            print("Error del Intérprete CPP: Se esperaba un NodoTraduccionUnidad.")
            return None
        try:
            for declaracion_global in nodo_traduccion.declaraciones_globales:
                self._ejecutar_declaracion_o_definicion_global(declaracion_global)
            
            main_func_obj = None
            try: main_func_obj = self.alcance_global.obtener('main')
            except ErrorTiempoEjecucionCPP: raise ErrorTiempoEjecucionCPP("Función 'main' no definida en el alcance global.")
            if not isinstance(main_func_obj, FuncionDefinidaCPP): raise ErrorTiempoEjecucionCPP("Símbolo 'main' no es una función definida.")
            
            print("\n--- Iniciando Simulación de Ejecución (C++) ---")
            alcance_anterior_main = self.alcance_actual
            self.alcance_actual = AlcanceCPP(padre=main_func_obj.alcance_definicion, nombre_alcance="main_body"); 
            self.alcance_actual.objetos_globales_cpp_ref = self.objetos_globales_cpp
            
            codigo_retorno = 0 
            try:
                if main_func_obj.cuerpo_nodo: self.visitar_NodoBloqueSentenciasCPP(main_func_obj.cuerpo_nodo)
                else: print("Advertencia (InterpreteCPP): La función 'main' no tiene cuerpo.")
            except ErrorRetornoCPP as e_ret:
                codigo_retorno = e_ret.valor
                if not isinstance(codigo_retorno, int): 
                    print(f"Advertencia (InterpreteCPP): main retornó '{codigo_retorno}', se esperaba un int. Se usará 0."); codigo_retorno = 0
            
            self.alcance_actual = alcance_anterior_main 
            print(f"--- Simulación de Ejecución Finalizada (C++). main retornó: {codigo_retorno} ---")
            return codigo_retorno
        except ErrorTiempoEjecucionCPP as e_runtime_cpp: print(f"Error en Tiempo de Ejecución (C++): {e_runtime_cpp}")
        except Exception as e_general:
            print(f"Error Inesperado durante la Interpretación de C++: {e_general}"); import traceback; traceback.print_exc()
        return None 

    def _ejecutar_declaracion_o_definicion_global(self, nodo):
        if isinstance(nodo, NodoDirectivaPreprocesador): self.visitar_NodoDirectivaPreprocesador(nodo)
        elif isinstance(nodo, NodoUsingNamespace): self.visitar_NodoUsingNamespace(nodo)
        elif isinstance(nodo, NodoNamespaceDefinicion): self.visitar_NodoNamespaceDefinicion(nodo)
        elif isinstance(nodo, NodoDefinicionClase): self.visitar_NodoDefinicionClase(nodo)
        elif isinstance(nodo, NodoDefinicionFuncion): self.visitar_NodoDefinicionFuncion(nodo)
        elif isinstance(nodo, NodoDeclaracionVariableCPP): self.visitar_NodoDeclaracionVariableCPP(nodo)
        elif nodo is None: pass
        else: print(f"Advertencia (IntérpreteCPP): Ejecución para el tipo de nodo global '{type(nodo).__name__}' no implementada.")

    def visitar_NodoDirectivaPreprocesador(self, nodo_dir):
        if nodo_dir.directiva == 'include':
            if nodo_dir.archivo_cabecera: print(f"Simulación: #include <{nodo_dir.archivo_cabecera}> procesado.")
            else: print(f"Simulación: #include {nodo_dir.argumentos} (forma no estándar o error) procesado.")
        else: print(f"Simulación: Directiva de preprocesador '#{nodo_dir.directiva} {nodo_dir.argumentos}' encontrada.")

    def visitar_NodoUsingNamespace(self, nodo_using):
        print(f"Simulación: 'using namespace {nodo_using.nombre_namespace_str};' encontrado.")
        if nodo_using.nombre_namespace_str == 'std':
            if 'std' in self.objetos_globales_cpp:
                for nombre_simbolo, valor_simbolo in self.objetos_globales_cpp['std'].items():
                    self.alcance_actual.declarar(nombre_simbolo, valor_simbolo, tipo_simbolo="usado_de_namespace")
            else:
                print(f"Advertencia (InterpreteCPP): Namespace 'std' no encontrado en objetos globales para 'using namespace'.")

    def visitar_NodoNamespaceDefinicion(self, nodo_ns):
        nombre_ns_real = nodo_ns.nombre if nodo_ns.nombre else "_anon_ns_" + str(id(nodo_ns))
        print(f"Simulación: Entrando a namespace '{nombre_ns_real}'.")
        
        prefijo_anterior = self.namespace_actual_prefijo
        self.namespace_actual_prefijo += nombre_ns_real + "::"
        
        alcance_anterior = self.alcance_actual
        # Las declaraciones dentro del namespace se hacen en el alcance actual,
        # pero los nombres de funciones/clases se calificarán con el prefijo.
        # No creamos un nuevo AlcanceCPP aquí para el namespace en sí,
        # sino que usamos el prefijo para calificar los nombres.
        
        if nodo_ns.nombre: # Registrar el namespace en el alcance padre para que se pueda referenciar
             alcance_anterior.declarar(nodo_ns.nombre, "namespace_marker", tipo_simbolo="namespace_nombre")


        for declaracion in nodo_ns.declaraciones_internas:
            self._ejecutar_declaracion_o_definicion_global(declaracion) 
        
        self.namespace_actual_prefijo = prefijo_anterior # Restaurar prefijo al salir del namespace
        # No restaurar self.alcance_actual aquí si no se cambió.
        print(f"Simulación: Fin de namespace '{nombre_ns_real}'.")

    def visitar_NodoDefinicionClase(self, nodo_clase):
        nombre_clase_simple = nodo_clase.nombre 
        nombre_clase_calificado = self.namespace_actual_prefijo + nombre_clase_simple
        
        print(f"Simulación: Clase/Struct '{nombre_clase_calificado}' definida.")
        print(f"[DEBUG InterpreteCPP - visitar_NodoDefinicionClase] Prefijo NS actual para clase: '{self.namespace_actual_prefijo}'")
        print(f"[DEBUG InterpreteCPP - visitar_NodoDefinicionClase] Almacenando clase en catálogo con clave: '{nombre_clase_calificado}'")

        if nombre_clase_calificado in self.catalogo_clases:
            raise ErrorTiempoEjecucionCPP(f"Redefinición de clase '{nombre_clase_calificado}'.")
        
        definicion_clase_obj = ClaseDefinidaCPP(nombre_clase_calificado)
        
        alcance_padre_clase_para_miembros = self.alcance_actual 
        alcance_clase_para_miembros = AlcanceCPP(padre=alcance_padre_clase_para_miembros, nombre_alcance=f"clase_{nombre_clase_simple}")
        alcance_clase_para_miembros.objetos_globales_cpp_ref = self.objetos_globales_cpp

        prefijo_ns_guardado_clase = self.namespace_actual_prefijo
        self.namespace_actual_prefijo = nombre_clase_calificado + "::" 

        alcance_original_para_procesar_miembros = self.alcance_actual
        self.alcance_actual = alcance_clase_para_miembros 

        print(f"[DEBUG InterpreteCPP - visitar_NodoDefinicionClase] Procesando miembros para '{nombre_clase_calificado}'. Nodos miembro del parser: {len(nodo_clase.miembros_nodos)}") # DEBUG
        for miembro_nodo in nodo_clase.miembros_nodos: # El parser debe poblar esto
            print(f"[DEBUG InterpreteCPP - visitar_NodoDefinicionClase]   Miembro AST: {type(miembro_nodo).__name__}") # DEBUG
            if isinstance(miembro_nodo, NodoDefinicionFuncion):
                print(f"[DEBUG InterpreteCPP - visitar_NodoDefinicionClase]     Es NodoDefinicionFuncion: {miembro_nodo.nombre}") # DEBUG
                metodo_obj = FuncionDefinidaCPP(
                    miembro_nodo.nombre_funcion_qname_tokens, 
                    miembro_nodo.parametros_nodos,
                    miembro_nodo.cuerpo_nodo_bloque,
                    self.alcance_actual, 
                    clase_contenedora=definicion_clase_obj 
                )
                definicion_clase_obj.agregar_metodo(metodo_obj)
                print(f"[DEBUG InterpreteCPP - visitar_NodoDefinicionClase]     Método '{metodo_obj.nombre_simple}' agregado a '{nombre_clase_calificado}'. Métodos actuales: {list(definicion_clase_obj.metodos.keys())}") # DEBUG
        
        self.alcance_actual = alcance_original_para_procesar_miembros 
        self.namespace_actual_prefijo = prefijo_ns_guardado_clase 

        self.catalogo_clases[nombre_clase_calificado] = definicion_clase_obj
        alcance_padre_clase_para_miembros.declarar(nombre_clase_simple, definicion_clase_obj, tipo_simbolo="tipo_clase")
 

    def visitar_NodoDefinicionFuncion(self, nodo_func):
        if nodo_func.es_metodo_clase:
            return 
        
        nombre_base_func = "".join([t.lexema for t in nodo_func.nombre_funcion_qname_tokens])
        nombre_completo_func = self.namespace_actual_prefijo + nombre_base_func
        
        funcion_obj = FuncionDefinidaCPP(
            nodo_func.nombre_funcion_qname_tokens, 
            nodo_func.parametros_nodos,
            nodo_func.cuerpo_nodo_bloque,
            self.alcance_actual 
        )
        self.alcance_actual.declarar(nombre_completo_func, funcion_obj, tipo_simbolo="funcion")
        print(f"Simulación: Función '{nombre_completo_func}' definida.")

    def visitar_NodoBloqueSentenciasCPP(self, nodo_bloque, crear_nuevo_alcance_para_bloque=False):
        alcance_anterior = self.alcance_actual
        if crear_nuevo_alcance_para_bloque:
            self.alcance_actual = AlcanceCPP(padre=alcance_anterior, nombre_alcance=f"bloque_{id(nodo_bloque)}")
            self.alcance_actual.objetos_globales_cpp_ref = self.objetos_globales_cpp
        try:
            if nodo_bloque.sentencias:
                for sentencia in nodo_bloque.sentencias:
                    self._ejecutar_sentencia_cpp_interna(sentencia)
        except ErrorRetornoCPP: 
            self.alcance_actual = alcance_anterior 
            raise 
        self.alcance_actual = alcance_anterior

    def _ejecutar_sentencia_cpp_interna(self, nodo):
        if isinstance(nodo, NodoDeclaracionVariableCPP): self.visitar_NodoDeclaracionVariableCPP(nodo)
        elif isinstance(nodo, NodoSentenciaExpresionCPP): self.visitar_NodoSentenciaExpresionCPP(nodo)
        elif isinstance(nodo, NodoSentenciaReturnCPP): self.visitar_NodoSentenciaReturnCPP(nodo)
        elif isinstance(nodo, NodoDirectivaPreprocesador): self.visitar_NodoDirectivaPreprocesador(nodo)
        elif isinstance(nodo, NodoSentenciaIfCPP): self.visitar_NodoSentenciaIfCPP(nodo)
        elif isinstance(nodo, NodoSentenciaWhileCPP): 
            self.visitar_NodoSentenciaWhileCPP(nodo)
        elif isinstance(nodo, NodoSentenciaForCPP):
            self.visitar_NodoSentenciaForCPP(nodo)
        elif isinstance(nodo, NodoBloqueSentenciasCPP): self.visitar_NodoBloqueSentenciasCPP(nodo, crear_nuevo_alcance_para_bloque=True)
        elif nodo is None: pass
        else: print(f"Advertencia (IntérpreteCPP): Ejecución para sentencia interna '{type(nodo).__name__}' no implementada.")

    # --- MÉTODO visitar_NodoDeclaracionVariableCPP ACTUALIZADO ---
    def visitar_NodoDeclaracionVariableCPP(self, nodo_decl_var):
        for declarador in nodo_decl_var.declaradores:
            nombre_var = declarador.nombre 
            valor_inicial = None 
            
            # Construir el nombre completo del tipo para la búsqueda en el catálogo.
            # El parser en NodoTipoCPP.tokens_tipo debería tener los tokens del nombre base,
            # incluyendo calificadores de namespace si los hay.
            # Ejemplo: si tipo_nodo.tokens_tipo es [Token(ID, 'MyNamespace'), Token(::), Token(ID, 'MiClase')]
            # nombre_tipo_para_catalogo será "MyNamespace::MiClase"
            nombre_tipo_para_catalogo = "".join([t.lexema for t in nodo_decl_var.tipo_nodo.tokens_tipo])
            
            # print(f"[DEBUG InterpreteCPP] Declarando var '{nombre_var}'. Tipo AST: '{nodo_decl_var.tipo_nodo.nombre_tipo_str}'.")
            # print(f"[DEBUG InterpreteCPP] Buscando tipo '{nombre_tipo_para_catalogo}' en catálogo de clases.")
            # print(f"[DEBUG InterpreteCPP] Catálogo actual de clases: {list(self.catalogo_clases.keys())}")

            if nombre_tipo_para_catalogo in self.catalogo_clases:
                # print(f"[DEBUG InterpreteCPP] Tipo '{nombre_tipo_para_catalogo}' ENCONTRADO en catálogo.")
                definicion_clase = self.catalogo_clases[nombre_tipo_para_catalogo]
                valor_inicial = InstanciaClaseCPP(definicion_clase)
                if declarador.inicializador_nodo: # Manejar constructores explícitos (simplificado)
                     print(f"Advertencia (InterpreteCPP): Inicialización explícita/constructor para objeto de clase '{nombre_var}' no completamente simulada.")
                     # Aquí se podría intentar evaluar el inicializador si es una llamada a constructor
            elif declarador.inicializador_nodo:
                # print(f"[DEBUG InterpreteCPP] Tipo '{nombre_tipo_para_catalogo}' NO encontrado. Evaluando inicializador explícito.")
                valor_inicial = self._evaluar_expresion_cpp(declarador.inicializador_nodo)
            # else:
                # print(f"[DEBUG InterpreteCPP] Tipo '{nombre_tipo_para_catalogo}' NO encontrado y SIN inicializador explícito. valor_inicial será None.")
            
            self.alcance_actual.declarar(nombre_var, valor_inicial, tipo_simbolo="variable")
            print(f"Simulación: Variable '{nombre_var}' declarada (tipo: {nodo_decl_var.tipo_nodo.nombre_tipo_str}). Valor inicial: {repr(valor_inicial)}.")
    # --- FIN DE MÉTODO ACTUALIZADO ---

    def visitar_NodoSentenciaExpresionCPP(self, nodo_sent_expr):
        self._evaluar_expresion_cpp(nodo_sent_expr.expresion_nodo)
        if self.buffer_cout:
            print("".join(self.buffer_cout), end="")
            self.buffer_cout = []

    def visitar_NodoSentenciaReturnCPP(self, nodo_return):
        valor = None
        if nodo_return.expresion_nodo:
            valor = self._evaluar_expresion_cpp(nodo_return.expresion_nodo)
        raise ErrorRetornoCPP(valor)

    def visitar_NodoSentenciaIfCPP(self, nodo_if):
        condicion_evaluada = self._evaluar_expresion_cpp(nodo_if.condicion_nodo)
        if bool(condicion_evaluada): 
            self._ejecutar_sentencia_cpp_interna(nodo_if.cuerpo_then_nodo)
        elif nodo_if.cuerpo_else_nodo:
            self._ejecutar_sentencia_cpp_interna(nodo_if.cuerpo_else_nodo)

    def visitar_NodoSentenciaWhileCPP(self, nodo_while):
        """Simula la ejecución de una sentencia while."""
        # print(f"[InterpreteCPP DEBUG] Visitando NodoSentenciaWhileCPP.")
        while True:
            condicion_evaluada = self._evaluar_expresion_cpp(nodo_while.condicion_nodo)
            if not bool(condicion_evaluada):
                # print(f"[InterpreteCPP DEBUG] Condición WHILE es falsa. Saliendo del bucle.")
                break
            
            # print(f"[InterpreteCPP DEBUG] Condición WHILE es verdadera. Ejecutando cuerpo del bucle.")
            # El cuerpo del while puede ser una sola sentencia o un bloque.
            # Si es un bloque, _ejecutar_sentencia_cpp_interna lo pasará a visitar_NodoBloqueSentenciasCPP
            # y ese método creará un nuevo alcance para el bloque del while en cada iteración.
            self._ejecutar_sentencia_cpp_interna(nodo_while.cuerpo_nodo)
            # (Aquí se podría añadir manejo para break y continue si se implementan)

    def visitar_NodoSentenciaForCPP(self, nodo_for):
        """Simula la ejecución de una sentencia for."""
        # print(f"[InterpreteCPP DEBUG] Visitando NodoSentenciaForCPP.")
        
        # 1. Inicialización: Se ejecuta una vez. Puede crear un nuevo alcance si es una declaración.
        alcance_bucle_for = AlcanceCPP(padre=self.alcance_actual, nombre_alcance=f"for_loop_{id(nodo_for)}")
        alcance_bucle_for.objetos_globales_cpp_ref = self.objetos_globales_cpp
        
        alcance_anterior = self.alcance_actual
        self.alcance_actual = alcance_bucle_for # Entrar al alcance del bucle

        if nodo_for.inicializacion_nodo:
            if isinstance(nodo_for.inicializacion_nodo, NodoDeclaracionVariableCPP):
                self.visitar_NodoDeclaracionVariableCPP(nodo_for.inicializacion_nodo)
            elif isinstance(nodo_for.inicializacion_nodo, NodoExpresion): # Podría ser una expresión de asignación
                self._evaluar_expresion_cpp(nodo_for.inicializacion_nodo)
            else: # Podría ser None si la inicialización está vacía
                pass 
        
        # 2. Bucle de Condición, Cuerpo, Actualización
        while True:
            # 2a. Condición
            condicion_evaluada = True # Si no hay condición, el bucle es infinito (a menos que haya break)
            if nodo_for.condicion_nodo:
                condicion_evaluada = self._evaluar_expresion_cpp(nodo_for.condicion_nodo)
            
            if not bool(condicion_evaluada):
                # print(f"[InterpreteCPP DEBUG] Condición FOR es falsa. Saliendo del bucle.")
                break

            # 2b. Cuerpo del bucle
            # print(f"[InterpreteCPP DEBUG] Condición FOR es verdadera. Ejecutando cuerpo del bucle.")
            # El cuerpo se ejecuta en el alcance del bucle for.
            self._ejecutar_sentencia_cpp_interna(nodo_for.cuerpo_nodo)
            # (Aquí se podría añadir manejo para break y continue)

            # 2c. Actualización
            if nodo_for.actualizacion_nodo:
                # print(f"[InterpreteCPP DEBUG] Ejecutando actualización del FOR.")
                self._evaluar_expresion_cpp(nodo_for.actualizacion_nodo)
        
        self.alcance_actual = alcance_anterior # Salir del alcance del bucle

    def _evaluar_NodoMiembroExpresion(self, nodo_miembro):
       
        objeto_evaluado = self._evaluar_expresion_cpp(nodo_miembro.objeto_nodo)
        nombre_propiedad = None
        if hasattr(nodo_miembro, 'nombre_propiedad') and nodo_miembro.nombre_propiedad is not None:
            nombre_propiedad = nodo_miembro.nombre_propiedad
        elif nodo_miembro.es_calculado and hasattr(nodo_miembro, 'propiedad_token_o_nodo'):
            nombre_propiedad = str(self._evaluar_expresion_cpp(nodo_miembro.propiedad_token_o_nodo))
        elif hasattr(nodo_miembro, 'propiedad_token_o_nodo'):
            prop_info = nodo_miembro.propiedad_token_o_nodo
            if isinstance(prop_info, Token):
                nombre_propiedad = prop_info.lexema
            elif isinstance(prop_info, NodoIdentificadorCPP):
                nombre_propiedad = prop_info.nombre_simple 
        if nombre_propiedad is None:
            raise ErrorTiempoEjecucionCPP(f"NodoMiembroExpresion con estructura inesperada. No se pudo obtener nombre de propiedad. Nodo: {nodo_miembro}")
        if isinstance(objeto_evaluado, InstanciaClaseCPP):
            instancia = objeto_evaluado
            clase_def = instancia.definicion_clase
            if nombre_propiedad in clase_def.metodos:
                return MetodoEnlazado(instancia, clase_def.metodos[nombre_propiedad])
            elif nombre_propiedad in instancia.miembros_datos: 
                return instancia.miembros_datos[nombre_propiedad]
            else:
                raise ErrorTiempoEjecucionCPP(f"Miembro '{nombre_propiedad}' no encontrado en la clase '{clase_def.nombre_clase_completo}'.")
        elif isinstance(objeto_evaluado, dict): 
            if nombre_propiedad in objeto_evaluado:
                return objeto_evaluado[nombre_propiedad]
            else: 
                raise ErrorTiempoEjecucionCPP(f"Propiedad '{nombre_propiedad}' no encontrada en el objeto simulado.")
        else:
            raise ErrorTiempoEjecucionCPP(f"No se puede acceder a la propiedad '{nombre_propiedad}' de un tipo no objeto: {type(objeto_evaluado).__name__}")

    def _evaluar_NodoLlamadaFuncionCPP(self, nodo_llamada):
        
        callee_evaluado = self._evaluar_expresion_cpp(nodo_llamada.callee_nodo)
        valores_argumentos = [self._evaluar_expresion_cpp(arg_nodo) for arg_nodo in nodo_llamada.argumentos_nodos]
        if isinstance(callee_evaluado, FuncionDefinidaCPP): 
            funcion_a_llamar = callee_evaluado
            if len(valores_argumentos) != len(funcion_a_llamar.nombres_parametros):
                raise ErrorTiempoEjecucionCPP(f"Función '{funcion_a_llamar.nombre_completo}' esperaba {len(funcion_a_llamar.nombres_parametros)} args, recibió {len(valores_argumentos)}.")
            alcance_anterior = self.alcance_actual
            self.alcance_actual = AlcanceCPP(padre=funcion_a_llamar.alcance_definicion, nombre_alcance=f"func_{funcion_a_llamar.nombre_simple}")
            self.alcance_actual.objetos_globales_cpp_ref = self.objetos_globales_cpp
            for nombre_p, valor_a in zip(funcion_a_llamar.nombres_parametros, valores_argumentos):
                self.alcance_actual.declarar(nombre_p, valor_a)
            valor_retorno_func = None
            try:
                if funcion_a_llamar.cuerpo_nodo: self.visitar_NodoBloqueSentenciasCPP(funcion_a_llamar.cuerpo_nodo, crear_nuevo_alcance_para_bloque=False) 
            except ErrorRetornoCPP as e_ret_func:
                valor_retorno_func = e_ret_func.valor
            self.alcance_actual = alcance_anterior
            return valor_retorno_func
        elif isinstance(callee_evaluado, MetodoEnlazado): 
            metodo_enlazado = callee_evaluado
            if len(valores_argumentos) != len(metodo_enlazado.metodo.nombres_parametros):
                 raise ErrorTiempoEjecucionCPP(f"Método '{metodo_enlazado.metodo.nombre_simple}' esperaba {len(metodo_enlazado.metodo.nombres_parametros)} args, recibió {len(valores_argumentos)}.")
            alcance_anterior = self.alcance_actual
            self.alcance_actual = AlcanceCPP(padre=metodo_enlazado.metodo.alcance_definicion, nombre_alcance=f"metodo_{metodo_enlazado.metodo.nombre_simple}")
            self.alcance_actual.objetos_globales_cpp_ref = self.objetos_globales_cpp
            self.alcance_actual.declarar('this', metodo_enlazado.instancia, tipo_simbolo="variable")
            for nombre_p, valor_a in zip(metodo_enlazado.metodo.nombres_parametros, valores_argumentos):
                self.alcance_actual.declarar(nombre_p, valor_a)
            valor_retorno_metodo = None
            try:
                if metodo_enlazado.metodo.cuerpo_nodo: self.visitar_NodoBloqueSentenciasCPP(metodo_enlazado.metodo.cuerpo_nodo)
            except ErrorRetornoCPP as e_ret_metodo:
                valor_retorno_metodo = e_ret_metodo.valor
            self.alcance_actual = alcance_anterior
            return valor_retorno_metodo
        elif callable(callee_evaluado): 
            return callee_evaluado(*valores_argumentos)
        else:
            raise ErrorTiempoEjecucionCPP(f"'{nodo_llamada.callee_nodo}' no es una función ni método llamable.")
        
        
    def _evaluar_NodoLlamadaFuncionCPP(self, nodo_llamada):
        # print(f"[InterpreteCPP DEBUG] Evaluando NodoLlamadaFuncionCPP. Callee: {type(nodo_llamada.callee_nodo).__name__}")
        callee_evaluado = self._evaluar_expresion_cpp(nodo_llamada.callee_nodo)
        valores_argumentos = [self._evaluar_expresion_cpp(arg_nodo) for arg_nodo in nodo_llamada.argumentos_nodos]

        if isinstance(callee_evaluado, FuncionDefinidaCPP): 
            funcion_a_llamar = callee_evaluado
            # print(f"[InterpreteCPP DEBUG] Llamando a función definida por usuario: {funcion_a_llamar.nombre_completo}")
            if len(valores_argumentos) != len(funcion_a_llamar.nombres_parametros):
                raise ErrorTiempoEjecucionCPP(f"Función '{funcion_a_llamar.nombre_completo}' esperaba {len(funcion_a_llamar.nombres_parametros)} args, recibió {len(valores_argumentos)}.")
            
            alcance_anterior = self.alcance_actual
            self.alcance_actual = AlcanceCPP(padre=funcion_a_llamar.alcance_definicion, nombre_alcance=f"func_{funcion_a_llamar.nombre_simple}") 
            self.alcance_actual.objetos_globales_cpp_ref = self.objetos_globales_cpp

            for nombre_p, valor_a in zip(funcion_a_llamar.nombres_parametros, valores_argumentos):
                self.alcance_actual.declarar(nombre_p, valor_a)
            
            valor_retorno_func = None 
            try:
                if funcion_a_llamar.cuerpo_nodo: 
                    self.visitar_NodoBloqueSentenciasCPP(funcion_a_llamar.cuerpo_nodo, crear_nuevo_alcance_para_bloque=False) 
            except ErrorRetornoCPP as e_ret_func:
                valor_retorno_func = e_ret_func.valor
            
            self.alcance_actual = alcance_anterior 
            return valor_retorno_func

        elif isinstance(callee_evaluado, MetodoEnlazado): 
            metodo_enlazado = callee_evaluado
            # print(f"[InterpreteCPP DEBUG] Llamando a método enlazado: {metodo_enlazado.metodo.nombre_simple}")
            if len(valores_argumentos) != len(metodo_enlazado.metodo.nombres_parametros):
                 raise ErrorTiempoEjecucionCPP(f"Método '{metodo_enlazado.metodo.nombre_simple}' esperaba {len(metodo_enlazado.metodo.nombres_parametros)} args, recibió {len(valores_argumentos)}.")
            
            alcance_anterior = self.alcance_actual
            self.alcance_actual = AlcanceCPP(padre=metodo_enlazado.metodo.alcance_definicion, nombre_alcance=f"metodo_{metodo_enlazado.metodo.nombre_simple}")
            self.alcance_actual.objetos_globales_cpp_ref = self.objetos_globales_cpp
            self.alcance_actual.declarar('this', metodo_enlazado.instancia, tipo_simbolo="variable")

            for nombre_p, valor_a in zip(metodo_enlazado.metodo.nombres_parametros, valores_argumentos):
                self.alcance_actual.declarar(nombre_p, valor_a)
            
            valor_retorno_metodo = None
            try:
                if metodo_enlazado.metodo.cuerpo_nodo: self.visitar_NodoBloqueSentenciasCPP(metodo_enlazado.metodo.cuerpo_nodo)
            except ErrorRetornoCPP as e_ret_metodo:
                valor_retorno_metodo = e_ret_metodo.valor
            self.alcance_actual = alcance_anterior
            return valor_retorno_metodo
        
        elif callable(callee_evaluado): 
            # print(f"[InterpreteCPP DEBUG] Llamando a callable (función Python simulada).")
            return callee_evaluado(*valores_argumentos)
        else:
            raise ErrorTiempoEjecucionCPP(f"'{nodo_llamada.callee_nodo}' no es una función ni método llamable.")


    def _evaluar_expresion_cpp(self, nodo_expr):
        # (Como estaba antes, con la corrección para operadores de comparación)
        if isinstance(nodo_expr, NodoLiteralCPP):
            return nodo_expr.valor
        elif isinstance(nodo_expr, NodoIdentificadorCPP):
            if nodo_expr.nombre_completo == "std::cout": return self.objetos_globales_cpp['std']['cout']
            if nodo_expr.nombre_completo == "std::endl": return self.objetos_globales_cpp['std']['endl']
            if nodo_expr.nombre_completo == 'std': return self.objetos_globales_cpp['std']
            if nodo_expr.nombre_simple in self.alcance_actual.simbolos and \
               self.alcance_actual.simbolos[nodo_expr.nombre_simple].get('tipo_simbolo') == "usado_de_namespace":
                return self.alcance_actual.obtener(nodo_expr.nombre_simple) 
            return self.alcance_actual.obtener(nodo_expr.nombre_completo) 
        elif isinstance(nodo_expr, NodoExpresionBinariaCPP):
            val_izq = self._evaluar_expresion_cpp(nodo_expr.izquierda_nodo)
            val_der = self._evaluar_expresion_cpp(nodo_expr.derecha_nodo)
            op = nodo_expr.operador_token.lexema 
            tipo_op_token = nodo_expr.operador_token.tipo
            if op == '<<' and tipo_op_token == TT_OPERADOR_BITWISE: 
                if val_izq == self.objetos_globales_cpp['std']['cout']: return self._simular_std_cout(val_der) 
                else: 
                    if not (isinstance(val_izq, int) and isinstance(val_der, int)): raise ErrorTiempoEjecucionCPP(f"Operandos para '<<' (bitwise) deben ser enteros.")
                    return val_izq << val_der
            elif op == '>>' and tipo_op_token == TT_OPERADOR_BITWISE:
                 if not (isinstance(val_izq, int) and isinstance(val_der, int)): raise ErrorTiempoEjecucionCPP(f"Operandos para '>>' (bitwise) deben ser enteros.")
                 return val_izq >> val_der
            elif op == '=' and tipo_op_token == TT_OPERADOR_ASIGNACION:
                 if not isinstance(nodo_expr.izquierda_nodo, NodoIdentificadorCPP):
                     raise ErrorTiempoEjecucionCPP("El lado izquierdo de '=' debe ser un identificador (variable).")
                 nombre_var = nodo_expr.izquierda_nodo.nombre_simple 
                 self.alcance_actual.asignar(nombre_var, val_der)
                 return val_der 
            if tipo_op_token == TT_OPERADOR_ARITMETICO or (tipo_op_token == TT_ASTERISCO and op == '*'):
                try: 
                    num_izq = float(val_izq) if not isinstance(val_izq, bool) else (1 if val_izq else 0)
                    num_der = float(val_der) if not isinstance(val_der, bool) else (1 if val_der else 0)
                    if op == '+': return num_izq + num_der
                    if op == '-': return num_izq - num_der
                    if op == '*': return num_izq * num_der
                    if op == '/':
                        if num_der == 0: raise ErrorTiempoEjecucionCPP("División por cero.")
                        return num_izq / num_der 
                    if op == '%': 
                        if num_der == 0: raise ErrorTiempoEjecucionCPP("Módulo por cero.")
                        return int(num_izq) % int(num_der) 
                except (ValueError, TypeError):
                    if op == '+' and isinstance(val_izq, str) and isinstance(val_der, str): return val_izq + val_der
                    raise ErrorTiempoEjecucionCPP(f"Tipos incompatibles para operador aritmético '{op}': {type(val_izq).__name__}, {type(val_der).__name__}")
            if tipo_op_token == TT_OPERADOR_COMPARACION: 
                try:
                    if op == '>': return val_izq > val_der
                    if op == '<': return val_izq < val_der
                    if op == '>=': return val_izq >= val_der
                    if op == '<=': return val_izq <= val_der
                    if op == '==': return val_izq == val_der
                    if op == '!=': return val_izq != val_der
                except TypeError: 
                    print(f"Advertencia (InterpreteCPP): TypeError al comparar '{val_izq}' con '{val_der}' usando '{op}'.")
                    return False 
            raise ErrorTiempoEjecucionCPP(f"Operador binario C++ '{op}' (tipo: {tipo_op_token}) no soportado en evaluación.")
        elif isinstance(nodo_expr, NodoLlamadaFuncionCPP): 
            return self._evaluar_NodoLlamadaFuncionCPP(nodo_expr)
        elif isinstance(nodo_expr, NodoMiembroExpresion): 
            return self._evaluar_NodoMiembroExpresion(nodo_expr) 
        else:
            raise ErrorTiempoEjecucionCPP(f"Tipo de nodo de expresión C++ '{type(nodo_expr).__name__}' no soportado para evaluación.")
        return None 
# Fin de la clase InterpreteCPP