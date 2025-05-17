# src/simulador_ejecucion/interprete_cpp.py

# Importar las clases de nodos AST necesarias desde el parser_cpp.
try:
    from analizador_sintactico.parser_cpp import (
        NodoTraduccionUnidad, NodoDeclaracion, NodoSentencia, NodoExpresion,
        NodoDirectivaPreprocesador, NodoUsingNamespace, NodoNamespaceDefinicion,
        NodoDefinicionClase, NodoDefinicionFuncion, NodoParametroFuncion, NodoTipoCPP,
        NodoBloqueSentenciasCPP, NodoDeclaracionVariableCPP, NodoDeclaradorVariableCPP,
        NodoSentenciaExpresionCPP, NodoSentenciaReturnCPP, NodoMiembroExpresion,
        NodoIdentificadorCPP, NodoLiteralCPP, NodoExpresionBinariaCPP, NodoLlamadaFuncionCPP, NodoSentenciaIfCPP
        # Asegúrate de que todos los nodos que el parser puede generar estén aquí.
    )
    # Importar tipos de token si son necesarios para la evaluación.
    from analizador_lexico.lexer_cpp import Token, TT_OPERADOR_BITWISE, TT_OPERADOR_ASIGNACION, TT_OPERADOR_ARITMETICO, TT_ASTERISCO, TT_OPERADOR_COMPARACION # Para '<<'
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
    class Token: pass; TT_OPERADOR_BITWISE = "OPERADOR_BITWISE_CPP"


# Excepción personalizada para errores en tiempo de ejecución del intérprete de C++
class ErrorTiempoEjecucionCPP(RuntimeError):
    """Error general en tiempo de ejecución para el intérprete de C++."""
    pass

class ErrorRetornoCPP(Exception):
    """Excepción especial para manejar la sentencia 'return' y propagar su valor."""
    def __init__(self, valor):
        super().__init__("Sentencia return ejecutada")
        self.valor = valor

class AlcanceCPP:
    """Representa un alcance (scope) en C++ para almacenar variables y funciones."""
    def __init__(self, padre=None):
        self.simbolos = {}  # Almacena variables, funciones, tipos, etc.
        self.padre = padre

    def declarar(self, nombre, valor, tipo_simbolo="variable"): # tipo_simbolo puede ser "variable", "funcion", "tipo"
        # print(f"[AlcanceCPP DEBUG] Declarando '{nombre}' (tipo: {tipo_simbolo}) en alcance {id(self)}.")
        if nombre in self.simbolos:
            # Manejo de redeclaración (C++ tiene reglas estrictas)
            # Por ahora, una simple advertencia o error.
            # raise ErrorTiempoEjecucionCPP(f"Redeclaración del símbolo '{nombre}' en el mismo alcance.")
            print(f"Advertencia (AlcanceCPP): Redeclaración del símbolo '{nombre}' en el mismo alcance.")
        self.simbolos[nombre] = {'valor': valor, 'tipo_simbolo': tipo_simbolo}

    def asignar(self, nombre, valor):
        # print(f"[AlcanceCPP DEBUG] Asignando '{nombre}' = {repr(valor)} en alcance {id(self)}")
        alcance_busqueda = self
        while alcance_busqueda:
            if nombre in alcance_busqueda.simbolos and alcance_busqueda.simbolos[nombre]['tipo_simbolo'] == "variable":
                alcance_busqueda.simbolos[nombre]['valor'] = valor
                return
            alcance_busqueda = alcance_busqueda.padre
        raise ErrorTiempoEjecucionCPP(f"Variable no declarada '{nombre}' (error en asignación).")

    def obtener(self, nombre):
        # print(f"[AlcanceCPP DEBUG] Obteniendo '{nombre}' desde alcance {id(self)}")
        alcance_busqueda = self
        while alcance_busqueda:
            if nombre in alcance_busqueda.simbolos:
                return alcance_busqueda.simbolos[nombre]['valor'] # Devuelve el valor o el objeto función/tipo
            alcance_busqueda = alcance_busqueda.padre
        
        # Podríamos tener un manejo para identificadores globales predefinidos si es necesario
        # if nombre == 'std': return self.objetos_globales_cpp.get('std') # Ejemplo
        
        raise ErrorTiempoEjecucionCPP(f"Símbolo no declarado '{nombre}'.")


class FuncionDefinidaCPP:
    """Representa una función definida por el usuario en C++."""
    def __init__(self, nombre_qname_tokens, parametros_nodos, cuerpo_nodo, alcance_definicion):
        self.nombre_completo = "".join([t.lexema for t in nombre_qname_tokens])
        self.nombres_parametros = [p.nombre_param_token.lexema for p in parametros_nodos if p.nombre_param_token]
        self.cuerpo_nodo = cuerpo_nodo # NodoBloqueSentenciasCPP
        self.alcance_definicion = alcance_definicion

    def __repr__(self):
        return f"<FuncionCPP: {self.nombre_completo}({', '.join(self.nombres_parametros)})>"


class InterpreteCPP:
    def __init__(self):
        """Inicializa el intérprete de C++."""
        self.alcance_global = AlcanceCPP()
        self.alcance_actual = self.alcance_global
        
        # Simulación de E/S y otros elementos de la biblioteca estándar
        self.objetos_globales_cpp = {
            'std': {
                'cout': self._simular_std_cout, # Esto será un objeto especial o un marcador
                'endl': '\n', # Simular std::endl como un carácter de nueva línea
                'cin': None # Placeholder para std::cin
                # Se podrían añadir más elementos de std como string, vector, etc.
            }
        }
        # Registrar 'std' en el alcance global
        self.alcance_global.declarar('std', self.objetos_globales_cpp['std'], tipo_simbolo="namespace_objeto")
        
        self.buffer_cout = [] # Para simular el comportamiento de cout con múltiples <<

    def _simular_std_cout(self, valor_a_imprimir):
        """Método placeholder que se invoca cuando se usa std::cout."""
        # En C++, cout es un objeto. La operación << está sobrecargada.
        # Aquí, simplemente acumulamos en un buffer.
        self.buffer_cout.append(str(valor_a_imprimir))
        if valor_a_imprimir == '\n': # Si es std::endl (o un \n directo)
            print("".join(self.buffer_cout), end="") # Imprimir buffer y limpiar
            self.buffer_cout = []
        return self.objetos_globales_cpp['std']['cout'] # Devolver 'cout' para encadenar <<

    def interpretar_unidad_traduccion(self, nodo_traduccion):
        """Punto de entrada para la interpretación de una unidad de traducción C++."""
        if not isinstance(nodo_traduccion, NodoTraduccionUnidad):
            print("Error del Intérprete CPP: Se esperaba un NodoTraduccionUnidad.")
            return None

        # print("[InterpreteCPP DEBUG] Iniciando interpretación de unidad de traducción.")
        try:
            # Primera pasada: procesar declaraciones globales, especialmente funciones y variables globales.
            # Las directivas de preprocesador se manejan aquí.
            for declaracion_global in nodo_traduccion.declaraciones_globales:
                self._ejecutar_declaracion_o_definicion_global(declaracion_global)

            # Segunda pasada: buscar y ejecutar main()
            funcion_main = self.alcance_global.obtener('main') # Asume que main está en el alcance global
            if not isinstance(funcion_main, FuncionDefinidaCPP):
                raise ErrorTiempoEjecucionCPP("Función 'main' no definida o no es una función.")
            
            print("\n--- Iniciando Simulación de Ejecución (C++) ---")
            # Simular llamada a main()
            # Crear un nuevo alcance para main
            alcance_anterior_main = self.alcance_actual
            self.alcance_actual = AlcanceCPP(padre=funcion_main.alcance_definicion) # main hereda del global
            
            codigo_retorno = 0 # Valor por defecto para main
            try:
                if funcion_main.cuerpo_nodo: # Verificar si main tiene cuerpo
                    self.visitar_NodoBloqueSentenciasCPP(funcion_main.cuerpo_nodo)
                else:
                    print("Advertencia (InterpreteCPP): La función 'main' no tiene cuerpo.")
            except ErrorRetornoCPP as e_ret:
                codigo_retorno = e_ret.valor
                if not isinstance(codigo_retorno, int): # main debe retornar int
                    print(f"Advertencia (InterpreteCPP): main retornó '{codigo_retorno}', se esperaba un int. Se usará 0.")
                    codigo_retorno = 0
            
            self.alcance_actual = alcance_anterior_main # Restaurar alcance
            print(f"--- Simulación de Ejecución Finalizada (C++). main retornó: {codigo_retorno} ---")
            return codigo_retorno

        except ErrorTiempoEjecucionCPP as e_runtime_cpp:
            print(f"Error en Tiempo de Ejecución (C++): {e_runtime_cpp}")
        except Exception as e_general:
            print(f"Error Inesperado durante la Interpretación de C++: {e_general}")
            import traceback
            traceback.print_exc()
        return None # O un código de error


    def _ejecutar_declaracion_o_definicion_global(self, nodo):
        # print(f"[InterpreteCPP DEBUG] Ejecutando/Visitando declaración global: {type(nodo).__name__}")
        if isinstance(nodo, NodoDirectivaPreprocesador):
            self.visitar_NodoDirectivaPreprocesador(nodo)
        elif isinstance(nodo, NodoUsingNamespace):
            self.visitar_NodoUsingNamespace(nodo)
        elif isinstance(nodo, NodoNamespaceDefinicion):
            self.visitar_NodoNamespaceDefinicion(nodo)
        elif isinstance(nodo, NodoDefinicionClase):
            self.visitar_NodoDefinicionClase(nodo)
        elif isinstance(nodo, NodoDefinicionFuncion):
            self.visitar_NodoDefinicionFuncion(nodo)
        # (Añadir NodoDeclaracionVariableCPP para variables globales si se implementa su parsing)
        elif nodo is None: # Puede ser por un ; vacío global
            pass
        else:
            print(f"Advertencia (IntérpreteCPP): Ejecución para el tipo de nodo global '{type(nodo).__name__}' no implementada.")

    def visitar_NodoDirectivaPreprocesador(self, nodo_dir):
        # print(f"[InterpreteCPP DEBUG] Visitando NodoDirectivaPreprocesador: {nodo_dir.directiva} {nodo_dir.argumentos}")
        if nodo_dir.directiva == 'include':
            if nodo_dir.archivo_cabecera:
                print(f"Simulación: #include <{nodo_dir.archivo_cabecera}> procesado.")
            else:
                print(f"Simulación: #include {nodo_dir.argumentos} (forma no estándar o error) procesado.")
        # (Aquí se podría simular #define almacenando macros simples)
        else:
            print(f"Simulación: Directiva de preprocesador '#{nodo_dir.directiva} {nodo_dir.argumentos}' encontrada.")

    def visitar_NodoUsingNamespace(self, nodo_using):
        """Simula 'using namespace nombre_ns;'."""
        print(f"Simulación: 'using namespace {nodo_using.nombre_namespace_str};' encontrado.")
        if nodo_using.nombre_namespace_str == 'std':
            # Copiar los símbolos de 'std' al alcance actual.
            # Esto es una simplificación de cómo funciona 'using namespace'.
            # En C++ real, los nombres se hacen visibles pero no se "copian" de esta manera.
            # Para la simulación, esto permite que 'cout' y 'endl' se resuelvan directamente.
            if 'std' in self.objetos_globales_cpp:
                for nombre_simbolo, valor_simbolo in self.objetos_globales_cpp['std'].items():
                    # Declarar en el alcance actual, permitiendo "sobrescribir" si ya existe
                    # un símbolo con el mismo nombre (aunque C++ tiene reglas de ambigüedad).
                    # Usamos 'objeto_global_usado' para indicar que vino de un 'using'.
                    self.alcance_actual.declarar(nombre_simbolo, valor_simbolo, tipo_simbolo="usado_de_namespace")
                    # print(f"[InterpreteCPP DEBUG] 'using namespace std': Declarando '{nombre_simbolo}' en alcance actual.")
            else:
                print(f"Advertencia (InterpreteCPP): Namespace 'std' no encontrado en objetos globales para 'using namespace'.")


    def visitar_NodoNamespaceDefinicion(self, nodo_ns):
        # print(f"[InterpreteCPP DEBUG] Visitando NodoNamespaceDefinicion: {nodo_ns.nombre}")
        # Para namespaces, se crea un nuevo alcance anidado.
        alcance_anterior = self.alcance_actual
        # El nombre del namespace podría usarse para crear un "objeto" en el alcance padre
        # que contenga los símbolos del namespace.
        # Por ahora, si tiene nombre, lo registramos como un tipo "namespace_objeto".
        if nodo_ns.nombre:
            ns_obj = {} # Simular el namespace como un diccionario
            self.alcance_actual.declarar(nodo_ns.nombre, ns_obj, tipo_simbolo="namespace")
            # Las declaraciones dentro del namespace deberían ir dentro de ns_obj o un nuevo AlcanceCPP asociado.
            # Esto es una simplificación.
            print(f"Simulación: Namespace '{nodo_ns.nombre}' definido.")

        # Las declaraciones dentro del namespace se ejecutan en el alcance actual (que podría ser el global
        # si no manejamos alcances de namespace anidados correctamente aquí).
        # Una mejor aproximación sería:
        # self.alcance_actual = AlcanceCPP(padre=alcance_anterior)
        # if nodo_ns.nombre: alcance_anterior.declarar(nodo_ns.nombre, self.alcance_actual.simbolos, tipo_simbolo="namespace_symbols")
        
        for declaracion in nodo_ns.declaraciones_internas:
            self._ejecutar_declaracion_o_definicion_global(declaracion) # Recursión

        # self.alcance_actual = alcance_anterior # Restaurar alcance
        print(f"Simulación: Fin de namespace '{nodo_ns.nombre if nodo_ns.nombre else 'anónimo'}'.")


    def visitar_NodoDefinicionClase(self, nodo_clase):
        # print(f"[InterpreteCPP DEBUG] Visitando NodoDefinicionClase: {nodo_clase.nombre}")
        # Por ahora, solo registramos la "declaración" de la clase.
        # Una implementación real almacenaría la estructura de la clase.
        print(f"Simulación: Clase/Struct '{nodo_clase.nombre}' definida (miembros no procesados en detalle).")
        # Podríamos añadirla a un catálogo de tipos:
        # self.alcance_actual.declarar(nodo_clase.nombre, nodo_clase, tipo_simbolo="tipo_clase")


    def visitar_NodoDefinicionFuncion(self, nodo_func):
        # print(f"[InterpreteCPP DEBUG] Visitando NodoDefinicionFuncion: {nodo_func.nombre}")
        # Almacenar la definición de la función en el alcance actual.
        # El alcance de definición es el alcance actual en el momento de la declaración.
        funcion_obj = FuncionDefinidaCPP(
            nodo_func.nombre_funcion_qname_tokens,
            nodo_func.parametros_nodos,
            nodo_func.cuerpo_nodo_bloque,
            self.alcance_actual # Clausura: la función recuerda el alcance donde fue definida
        )
        self.alcance_actual.declarar(funcion_obj.nombre_completo, funcion_obj, tipo_simbolo="funcion")
        print(f"Simulación: Función '{funcion_obj.nombre_completo}' definida.")

    def visitar_NodoBloqueSentenciasCPP(self, nodo_bloque, crear_nuevo_alcance=False): # crear_nuevo_alcance para if/for/while
        # print(f"[InterpreteCPP DEBUG] Visitando NodoBloqueSentenciasCPP. Crear nuevo alcance: {crear_nuevo_alcance}")
        alcance_anterior = self.alcance_actual
        if crear_nuevo_alcance:
            self.alcance_actual = AlcanceCPP(padre=alcance_anterior)
        
        try:
            if nodo_bloque.sentencias:
                for sentencia in nodo_bloque.sentencias:
                    self._ejecutar_sentencia_cpp_interna(sentencia)
        except ErrorRetornoCPP: # Si un return se propaga desde dentro del bloque
            self.alcance_actual = alcance_anterior # Restaurar alcance
            raise # Re-lanzar para que la llamada a función lo maneje
        
        self.alcance_actual = alcance_anterior

    def _ejecutar_sentencia_cpp_interna(self, nodo):
        """Despachador para sentencias dentro de un bloque."""
        # print(f"[InterpreteCPP DEBUG] Ejecutando sentencia interna: {type(nodo).__name__}")
        if isinstance(nodo, NodoDeclaracionVariableCPP):
            self.visitar_NodoDeclaracionVariableCPP(nodo)
        elif isinstance(nodo, NodoSentenciaExpresionCPP):
            self.visitar_NodoSentenciaExpresionCPP(nodo)
        elif isinstance(nodo, NodoSentenciaReturnCPP):
            self.visitar_NodoSentenciaReturnCPP(nodo)
        elif isinstance(nodo, NodoDirectivaPreprocesador): # Permitir directivas dentro de funciones
            self.visitar_NodoDirectivaPreprocesador(nodo)
        elif isinstance(nodo, NodoSentenciaIfCPP): # <-- NUEVA LLAMADA
            self.visitar_NodoSentenciaIfCPP(nodo)
        # (Añadir if, for, while, etc.)
        elif nodo is None: # Sentencia vacía ;
            pass
        else:
            print(f"Advertencia (IntérpreteCPP): Ejecución para sentencia interna '{type(nodo).__name__}' no implementada.")


    def visitar_NodoSentenciaIfCPP(self, nodo_if):
        """Simula la ejecución de una sentencia if-else."""
        # print(f"[InterpreteCPP DEBUG] Visitando NodoSentenciaIfCPP.")
        condicion_evaluada = self._evaluar_expresion_cpp(nodo_if.condicion_nodo)
        
        # En C++, cualquier valor no cero es true, cero es false.
        # bool(0) -> False, bool(cualquier_otro_numero) -> True
        # bool("") -> False, bool("algo") -> True
        # bool(None) -> False (si None simula nullptr o un valor "falsy")
        
        if bool(condicion_evaluada): # Coerción a booleano
            # print(f"[InterpreteCPP DEBUG] Condición IF es verdadera. Ejecutando rama THEN.")
            # El cuerpo de then/else puede ser una sola sentencia o un bloque.
            # _ejecutar_sentencia_cpp_interna o visitar_NodoBloqueSentenciasCPP se encargarán.
            # Si es un bloque, se creará un nuevo alcance para él si es necesario (para let/const en JS, no tanto para C++ var).
            # Por ahora, _ejecutar_sentencia_cpp_interna es suficiente si llama a visitar_NodoBloqueSentenciasCPP.
            self._ejecutar_sentencia_cpp_interna(nodo_if.cuerpo_then_nodo)
        elif nodo_if.cuerpo_else_nodo:
            # print(f"[InterpreteCPP DEBUG] Condición IF es falsa. Ejecutando rama ELSE.")
            self._ejecutar_sentencia_cpp_interna(nodo_if.cuerpo_else_nodo)
        # else:
            # print(f"[InterpreteCPP DEBUG] Condición IF es falsa. No hay rama ELSE.")


    def visitar_NodoDeclaracionVariableCPP(self, nodo_decl_var):
        # print(f"[InterpreteCPP DEBUG] Visitando NodoDeclaracionVariableCPP")
        # El tipo ya está en nodo_decl_var.tipo_nodo (NodoTipoCPP)
        for declarador in nodo_decl_var.declaradores:
            nombre_var = declarador.nombre # Asume que es el nombre simple por ahora
            # Aquí se necesitaría manejar el tipo completo del declarador (punteros, referencias)
            # y el tipo base de NodoDeclaracionVariableCPP.
            
            valor_inicial = None # NULL en C++
            if declarador.inicializador_nodo:
                # Si es NodoLlamadaFuncionCPP (para int x(5);), necesitamos evaluarlo
                if isinstance(declarador.inicializador_nodo, NodoLlamadaFuncionCPP) and \
                   isinstance(declarador.inicializador_nodo.callee_nodo, NodoIdentificadorCPP) and \
                   declarador.inicializador_nodo.callee_nodo.nombre_completo == nombre_var: # Inicialización tipo constructor T(v)
                    # Esto es una simplificación. Para constructores reales, sería más complejo.
                    # Si es int x(5), el argumento es 5.
                    if declarador.inicializador_nodo.argumentos_nodos:
                        valor_inicial = self._evaluar_expresion_cpp(declarador.inicializador_nodo.argumentos_nodos[0])
                    else: # int x(); declaración de función, no inicialización de variable
                        # Esto debería ser manejado por el parser para distinguir.
                        # Por ahora, si no hay args, es como no tener inicializador.
                        pass
                else:
                    valor_inicial = self._evaluar_expresion_cpp(declarador.inicializador_nodo)
            
            self.alcance_actual.declarar(nombre_var, valor_inicial, tipo_simbolo="variable")
            print(f"Simulación: Variable '{nombre_var}' declarada (tipo: {nodo_decl_var.tipo_nodo.nombre_tipo_str}). Valor inicial: {repr(valor_inicial)}.")


    def visitar_NodoSentenciaExpresionCPP(self, nodo_sent_expr):
        # print(f"[InterpreteCPP DEBUG] Visitando NodoSentenciaExpresionCPP")
        self._evaluar_expresion_cpp(nodo_sent_expr.expresion_nodo)
        # Limpiar buffer de cout si no terminó con endl
        if self.buffer_cout:
            print("".join(self.buffer_cout))
            self.buffer_cout = []


    def visitar_NodoSentenciaReturnCPP(self, nodo_return):
        # print(f"[InterpreteCPP DEBUG] Visitando NodoSentenciaReturnCPP")
        valor = None
        if nodo_return.expresion_nodo:
            valor = self._evaluar_expresion_cpp(nodo_return.expresion_nodo)
        raise ErrorRetornoCPP(valor)

    # --- Métodos para evaluar expresiones C++ (Simplificados) ---

    def _evaluar_NodoMiembroExpresion(self, nodo_miembro):
        objeto_evaluado = self._evaluar_expresion_cpp(nodo_miembro.objeto_nodo)
        nombre_propiedad = None

        # Priorizar el atributo 'nombre_propiedad' si el parser lo pobló
        if hasattr(nodo_miembro, 'nombre_propiedad') and nodo_miembro.nombre_propiedad:
            nombre_propiedad = nodo_miembro.nombre_propiedad
        # Fallback si 'propiedad_token' es un Token (como debería ser según el parser del Canvas)
        elif hasattr(nodo_miembro, 'propiedad_token') and isinstance(nodo_miembro.propiedad_token, Token):
            nombre_propiedad = nodo_miembro.propiedad_token.lexema
        # Fallback si 'propiedad_token' es un NodoIdentificadorCPP (basado en el error previo)
        elif hasattr(nodo_miembro, 'propiedad_token') and isinstance(nodo_miembro.propiedad_token, NodoIdentificadorCPP):
            nombre_propiedad = nodo_miembro.propiedad_token.nombre_simple # o nombre_completo
        # Fallback si el AST tiene 'propiedad_nodo' en lugar de 'propiedad_token'
        elif hasattr(nodo_miembro, 'propiedad_nodo') and isinstance(nodo_miembro.propiedad_nodo, NodoIdentificadorCPP):
            nombre_propiedad = nodo_miembro.propiedad_nodo.nombre_simple
        elif hasattr(nodo_miembro, 'propiedad_nodo') and isinstance(nodo_miembro.propiedad_nodo, NodoLiteralCPP) and isinstance(nodo_miembro.propiedad_nodo.valor, str):
             nombre_propiedad = nodo_miembro.propiedad_nodo.valor # Para obj['string_prop']
        else:
            # Si no se puede determinar el nombre de la propiedad, lanzar un error.
            # Esto puede indicar una inconsistencia entre el parser y el intérprete,
            # o una estructura de NodoMiembroExpresion no esperada.
            raise ErrorTiempoEjecucionCPP(f"NodoMiembroExpresion con estructura inesperada. No se pudo obtener nombre de propiedad. Nodo: {nodo_miembro}")

        if isinstance(objeto_evaluado, dict): 
            if nombre_propiedad in objeto_evaluado:
                return objeto_evaluado[nombre_propiedad]
            else: 
                raise ErrorTiempoEjecucionCPP(f"Propiedad '{nombre_propiedad}' no encontrada en el objeto.")
        # No es necesario el chequeo específico para 'std' aquí si _evaluar_expresion_cpp para NodoIdentificadorCPP
        # ya devuelve el diccionario de 'std' cuando se evalúa el objeto_nodo.
        else:
            raise ErrorTiempoEjecucionCPP(f"No se puede acceder a la propiedad '{nombre_propiedad}' de un tipo no objeto: {type(objeto_evaluado).__name__}")


    def _evaluar_expresion_cpp(self, nodo_expr):
        # print(f"[InterpreteCPP DEBUG] Evaluando Expresión CPP: {type(nodo_expr).__name__}")
        if isinstance(nodo_expr, NodoLiteralCPP):
            return nodo_expr.valor
        elif isinstance(nodo_expr, NodoIdentificadorCPP):
            if nodo_expr.nombre_completo == "std::cout":
                return self.objetos_globales_cpp['std']['cout']
            if nodo_expr.nombre_completo == "std::endl":
                return self.objetos_globales_cpp['std']['endl']
            if nodo_expr.nombre_completo == 'std': 
                return self.objetos_globales_cpp['std']
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
                if val_izq == self.objetos_globales_cpp['std']['cout']: 
                    return self._simular_std_cout(val_der) 
                else: 
                    if not (isinstance(val_izq, int) and isinstance(val_der, int)):
                        raise ErrorTiempoEjecucionCPP(f"Operandos para '<<' (bitwise) deben ser enteros.")
                    return val_izq << val_der
            elif op == '>>' and tipo_op_token == TT_OPERADOR_BITWISE:
                 if not (isinstance(val_izq, int) and isinstance(val_der, int)):
                        raise ErrorTiempoEjecucionCPP(f"Operandos para '>>' (bitwise) deben ser enteros.")
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
                    if op == '+' and isinstance(val_izq, str) and isinstance(val_der, str): 
                        return val_izq + val_der
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
            callee_evaluado = self._evaluar_expresion_cpp(nodo_expr.callee_nodo)
            valores_argumentos = [self._evaluar_expresion_cpp(arg_nodo) for arg_nodo in nodo_expr.argumentos_nodos]

            if isinstance(callee_evaluado, FuncionDefinidaCPP):
                funcion_a_llamar = callee_evaluado
                if len(valores_argumentos) != len(funcion_a_llamar.nombres_parametros):
                    raise ErrorTiempoEjecucionCPP(f"Función '{funcion_a_llamar.nombre_completo}' esperaba {len(funcion_a_llamar.nombres_parametros)} args, recibió {len(valores_argumentos)}.")
                
                alcance_anterior = self.alcance_actual
                self.alcance_actual = AlcanceCPP(padre=funcion_a_llamar.alcance_definicion)
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
            elif callable(callee_evaluado): 
                return callee_evaluado(*valores_argumentos)
            else:
                raise ErrorTiempoEjecucionCPP(f"'{nodo_expr.callee_nodo}' no es una función.")
        
        elif isinstance(nodo_expr, NodoMiembroExpresion): 
            return self._evaluar_NodoMiembroExpresion(nodo_expr) # Llamada al método corregido

        else:
            raise ErrorTiempoEjecucionCPP(f"Tipo de nodo de expresión C++ '{type(nodo_expr).__name__}' no soportado para evaluación.")
        return None 

# Fin de la clase InterpreteCPP
