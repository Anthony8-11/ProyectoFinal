# src/simulador_ejecucion/interprete_javascript.py

# Importar las clases de nodos AST necesarias desde el parser_javascript.
try:
    from analizador_sintactico.parser_javascript import (
        NodoProgramaJS, NodoSentencia, NodoExpresion,
        NodoDeclaracionVariable, NodoDeclaradorVariable,
        NodoDeclaracionFuncion, NodoBloqueSentencias,
        NodoSentenciaExpresion, NodoSentenciaIf, NodoSentenciaReturn, NodoBucleFor,
        NodoIdentificadorJS, NodoLiteralJS, NodoAsignacionExpresion,
        NodoExpresionBinariaJS, NodoLlamadaExpresion, NodoMiembroExpresion,
        NodoExpresionActualizacion, NodoArrayLiteralJS, NodoObjetoLiteralJS, NodoPropiedadObjetoJS
        # Asegúrate de que NodoExpresionUnariaJS esté aquí si la tienes definida
    )
    # Podríamos necesitar tipos de token si el intérprete necesita verificar algo del token original.
    from analizador_lexico.lexer_javascript import Token, TT_PALABRA_CLAVE, TT_IDENTIFICADOR, TT_LITERAL_CADENA, TT_LITERAL_NUMERICO, TT_OPERADOR_ARITMETICO, TT_OPERADOR_COMPARACION, TT_OPERADOR_LOGICO # Para 'undefined', etc.
except ImportError as e_import_ast_interprete_js:
    print(f"ADVERTENCIA CRÍTICA (InterpreteJavaScript): No se pudieron importar los nodos AST desde 'parser_javascript.py'. Error: {e_import_ast_interprete_js}")
    # Definir placeholders muy básicos
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
    TT_PALABRA_CLAVE = "PALABRA_CLAVE_JS"
    TT_LITERAL_CADENA = "LITERAL_CADENA_JS"
    TT_IDENTIFICADOR = "IDENTIFICADOR_JS"


# Excepción personalizada para errores en tiempo de ejecución del intérprete de JS
class ErrorTiempoEjecucionJS(RuntimeError):
    pass

class ErrorRetornoJS(Exception):
    """Excepción especial para manejar la sentencia 'return' y propagar su valor."""
    def __init__(self, valor):
        super().__init__("Sentencia return ejecutada")
        self.valor = valor # El valor que se retorna

class FuncionDefinidaUsuario:
    """Representa una función definida por el usuario en JavaScript."""
    def __init__(self, nombre_token_o_ninguno, parametros_tokens, cuerpo_nodo_bloque, alcance_definicion):
        self.nombre = nombre_token_o_ninguno.lexema if nombre_token_o_ninguno else None # Puede ser None para funciones anónimas/flecha
        self.nombres_parametros = [p_token.lexema for p_token in parametros_tokens]
        self.cuerpo_nodo = cuerpo_nodo_bloque # NodoBloqueSentencias
        self.alcance_definicion = alcance_definicion # El alcance donde la función fue CREADA (para clausuras)

    def __repr__(self):
        return f"<FuncionJS: {self.nombre or 'anónima'}({', '.join(self.nombres_parametros)})>"

class AlcanceJS:
    def __init__(self, padre=None):
        self.variables = {}
        self.padre = padre

    def declarar_variable(self, nombre_var, tipo_declaracion, valor_inicial=None):
        # print(f"[Alcance DEBUG] Declarando '{nombre_var}' (tipo decl: {tipo_declaracion}) en alcance {id(self)} con valor inicial: {repr(valor_inicial)}")
        if tipo_declaracion in ['let', 'const'] and nombre_var in self.variables:
            raise ErrorTiempoEjecucionJS(f"Identificador '{nombre_var}' ya ha sido declarado en este alcance.")
        
        # Para 'var', si ya existe en este alcance de función o global, no se crea una nueva,
        # pero la inicialización (si existe) puede ocurrir.
        # Si es 'let' o 'const', o si 'var' no existe, se añade.
        # JavaScript 'var' tiene hoisting y alcance de función, 'let'/'const' tienen alcance de bloque.
        # Nuestra simulación de alcance actual es más simple (un solo diccionario por AlcanceJS).
        # Para un manejo completo de 'var' vs 'let'/'const' se necesitaría diferenciar
        # el tipo de alcance (bloque, función, global).
        
        self.variables[nombre_var] = valor_inicial # Python None simula 'undefined'

    def asignar_variable(self, nombre_var, valor):
        # print(f"[Alcance DEBUG] Asignando '{nombre_var}' = {repr(valor)} en alcance {id(self)}")
        alcance_busqueda = self
        while alcance_busqueda:
            if nombre_var in alcance_busqueda.variables:
                # Aquí se podría añadir lógica para constantes (const)
                alcance_busqueda.variables[nombre_var] = valor
                return
            alcance_busqueda = alcance_busqueda.padre
        raise ErrorTiempoEjecucionJS(f"Referencia a variable no declarada: '{nombre_var}' no ha sido definida (error en asignación).")

    def obtener_valor_variable(self, nombre_var):
        # print(f"[Alcance DEBUG] Obteniendo valor de '{nombre_var}' desde alcance {id(self)}")
        alcance_busqueda = self
        while alcance_busqueda:
            if nombre_var in alcance_busqueda.variables:
                return alcance_busqueda.variables[nombre_var]
            alcance_busqueda = alcance_busqueda.padre
        
        # Valores globales predefinidos de JavaScript
        if nombre_var == 'undefined': return None
        if nombre_var == 'NaN': return float('nan')
        if nombre_var == 'Infinity': return float('inf')
            
        raise ErrorTiempoEjecucionJS(f"Referencia a variable no declarada: '{nombre_var}' no está definida.")


class InterpreteJavaScript:
    def __init__(self):
        self.alcance_global = AlcanceJS() # Alcance global principal
        self.alcance_actual = self.alcance_global # El alcance en el que se está ejecutando actualmente

        self.objetos_globales = {
            'console': {
                'log': self._simular_console_log,
                # Se podrían añadir más métodos de console (error, warn, etc.)
            },
            # 'Math': { ... }, 'Date': { ... }, 'JSON': { ... }
            # 'alert': self._simular_alert (si se implementa)
        }
        # Registrar 'console' en el alcance global
        self.alcance_global.declarar_variable('console', 'var', self.objetos_globales['console'])


    def _simular_console_log(self, *args):
        """Simula la función console.log()."""
        # print("[InterpreteJS DEBUG] Ejecutando console.log simulado.")
        print(*(str(arg) for arg in args)) # Imprime los argumentos separados por espacio
        return None # console.log devuelve undefined

    def interpretar_script(self, nodo_programa_js):
        """Punto de entrada para la interpretación de un script JS completo."""
        if not isinstance(nodo_programa_js, NodoProgramaJS):
            print("Error del Intérprete JS: Se esperaba un NodoProgramaJS como raíz.")
            return

        try:
            print("\n--- Iniciando Simulación de Ejecución (JavaScript) ---")
            # El cuerpo de un NodoProgramaJS es una lista de sentencias/declaraciones
            if nodo_programa_js.cuerpo:
                for elemento_script in nodo_programa_js.cuerpo:
                    self._ejecutar_sentencia_o_declaracion(elemento_script)
            print("--- Simulación de Ejecución Finalizada (JavaScript) ---")
            # print(f"[InterpreteJS DEBUG] Alcance global final: {self.alcance_actual.variables}")
        except ErrorTiempoEjecucionJS as e_runtime_js:
            print(f"Error en Tiempo de Ejecución (JavaScript): {e_runtime_js}")
        except Exception as e_general:
            print(f"Error Inesperado durante la Interpretación de JavaScript: {e_general}")
            import traceback
            traceback.print_exc()

    def _ejecutar_sentencia_o_declaracion(self, nodo):
        """Despachador para ejecutar/visitar diferentes tipos de nodos de sentencia o declaración."""
        # print(f"[InterpreteJS DEBUG] Ejecutando/Visitando: {type(nodo).__name__}")
        if isinstance(nodo, NodoDeclaracionVariable):
            self.visitar_NodoDeclaracionVariable(nodo)
        elif isinstance(nodo, NodoDeclaracionFuncion):
            self.visitar_NodoDeclaracionFuncion(nodo)
        elif isinstance(nodo, NodoSentenciaExpresion):
            self.visitar_NodoSentenciaExpresion(nodo)
        elif isinstance(nodo, NodoBloqueSentencias):
            self.visitar_NodoBloqueSentencias(nodo)
        elif isinstance(nodo, NodoSentenciaReturn):
            self.visitar_NodoSentenciaReturn(nodo) # Esto lanzará ErrorRetornoJS
        elif isinstance(nodo, NodoSentenciaIf):
            self.visitar_NodoSentenciaIf(nodo)
        elif isinstance(nodo, NodoBucleFor):
            self.visitar_NodoBucleFor(nodo)
        elif nodo is None: # Puede ocurrir por un punto y coma vacío parseado
            pass
        else:
            print(f"Advertencia (IntérpreteJS): Ejecución para el tipo de nodo '{type(nodo).__name__}' no implementada.")


    def visitar_NodoSentenciaReturn(self, nodo_return):
        # print(f"[InterpreteJS DEBUG] Visitando NodoSentenciaReturn")
        valor = None
        if nodo_return.argumento_nodo:
            valor = self._evaluar_expresion(nodo_return.argumento_nodo)
        raise ErrorRetornoJS(valor) # Lanza la excepción para indicar un retorno



    def visitar_NodoDeclaracionVariable(self, nodo_decl_var):
        """Simula la declaración de variables (var, let, const)."""
        # print(f"[InterpreteJS DEBUG] Visitando NodoDeclaracionVariable (tipo: {nodo_decl_var.tipo_declaracion})")
        for declarador in nodo_decl_var.declaraciones:
            nombre_var = declarador.nombre
            valor_inicial = None # Por defecto, las variables se inicializan a undefined (None en Python)
            if declarador.valor_inicial_nodo:
                valor_inicial = self._evaluar_expresion(declarador.valor_inicial_nodo)
            
            # Usar el alcance actual para declarar la variable
            self.alcance_actual.declarar_variable(nombre_var, nodo_decl_var.tipo_declaracion, valor_inicial)

    def visitar_NodoSentenciaExpresion(self, nodo_sent_expr):
        """Ejecuta una sentencia que consiste en una expresión."""
        # print(f"[InterpreteJS DEBUG] Visitando NodoSentenciaExpresion")
        self._evaluar_expresion(nodo_sent_expr.expresion_nodo) # Evaluar la expresión por sus efectos secundarios

    # --- Métodos para evaluar expresiones (se expandirán) ---
    def _evaluar_expresion(self, nodo_expr):
        """Método despachador para evaluar diferentes tipos de nodos de expresión."""
        # print(f"[InterpreteJS DEBUG] Evaluando Expresión: {type(nodo_expr).__name__}")
        if isinstance(nodo_expr, NodoLiteralJS):
            return self._evaluar_NodoLiteralJS(nodo_expr)
        elif isinstance(nodo_expr, NodoIdentificadorJS):
            return self._evaluar_NodoIdentificadorJS(nodo_expr)
        elif isinstance(nodo_expr, NodoLlamadaExpresion):
            return self._evaluar_NodoLlamadaExpresion(nodo_expr)
        elif isinstance(nodo_expr, NodoMiembroExpresion):
            return self._evaluar_NodoMiembroExpresion(nodo_expr)
        elif isinstance(nodo_expr, NodoAsignacionExpresion):
            return self._evaluar_NodoAsignacionExpresion(nodo_expr)
        elif isinstance(nodo_expr, NodoExpresionBinariaJS):
            return self._evaluar_NodoExpresionBinariaJS(nodo_expr)
        elif isinstance(nodo_expr, NodoArrayLiteralJS):
            return self._evaluar_NodoArrayLiteralJS(nodo_expr)
        elif isinstance(nodo_expr, NodoObjetoLiteralJS):
            return self._evaluar_NodoObjetoLiteralJS(nodo_expr)
        elif isinstance(nodo_expr, NodoExpresionActualizacion):
            return self._evaluar_NodoExpresionActualizacion(nodo_expr)
        # (Añadir NodoExpresionUnariaJS si se implementa)
        else:
            raise ErrorTiempoEjecucionJS(f"Tipo de nodo de expresión desconocido o no soportado para evaluar: {type(nodo_expr).__name__}")


    def _evaluar_NodoLiteralJS(self, nodo_literal):
        # Si es una template literal (backticks) y contiene ${...}, procesar interpolación
        valor = nodo_literal.valor
        if isinstance(valor, str) and valor.find('${') != -1 and valor.count('`') == 0:
            # Simulación básica: solo soporta variables simples ${var} en el contexto actual
            import re
            def reemplazo(match):
                expr = match.group(1).strip()
                try:
                    return str(self.alcance_actual.obtener_valor_variable(expr))
                except Exception:
                    return '${' + expr + '}'
            valor = re.sub(r'\$\{([^}]+)\}', reemplazo, valor)
        return valor

    def _evaluar_NodoIdentificadorJS(self, nodo_id):
        # Busca el valor de la variable en el sistema de alcances.
        # print(f"[InterpreteJS DEBUG] Evaluando NodoIdentificadorJS: {nodo_id.nombre}")
        return self.alcance_actual.obtener_valor_variable(nodo_id.nombre)

    def _evaluar_NodoLlamadaExpresion(self, nodo_llamada):
        """Evalúa una llamada a función o método."""
        # print(f"[InterpreteJS DEBUG] Evaluando NodoLlamadaExpresion. Callee: {type(nodo_llamada.callee_nodo).__name__}")
        valores_argumentos = [self._evaluar_expresion(arg_nodo) for arg_nodo in nodo_llamada.argumentos_nodos]
        
        callee_evaluado = self._evaluar_expresion(nodo_llamada.callee_nodo)

        if isinstance(callee_evaluado, FuncionDefinidaUsuario):
            funcion_a_llamar = callee_evaluado
            # print(f"[InterpreteJS DEBUG] Llamando a función definida por usuario: {funcion_a_llamar.nombre}")
            if len(valores_argumentos) != len(funcion_a_llamar.nombres_parametros):
                raise ErrorTiempoEjecucionJS(
                    f"Función '{funcion_a_llamar.nombre}' esperaba {len(funcion_a_llamar.nombres_parametros)} argumentos, pero recibió {len(valores_argumentos)}."
                )

            # Crear nuevo alcance para la función
            alcance_anterior = self.alcance_actual
            # El nuevo alcance tiene como padre el alcance donde la función fue DEFINIDA (clausura)
            self.alcance_actual = AlcanceJS(padre=funcion_a_llamar.alcance_definicion) 

            # Asignar argumentos a parámetros en el nuevo alcance
            for nombre_param, valor_arg in zip(funcion_a_llamar.nombres_parametros, valores_argumentos):
                # Los parámetros se comportan como 'var' en términos de redeclaración dentro de la función,
                # o como 'let' si son parámetros rest/default (más complejo).
                # Aquí, simplemente los declaramos.
                self.alcance_actual.declarar_variable(nombre_param, 'param', valor_arg) # 'param' como tipo_declaracion

            valor_retorno = None # Valor por defecto si no hay return explícito con valor
            try:
                # Ejecutar el cuerpo de la función en el nuevo alcance
                self.visitar_NodoBloqueSentencias(funcion_a_llamar.cuerpo_nodo)
            except ErrorRetornoJS as e_ret:
                valor_retorno = e_ret.valor # Capturar el valor de retorno
            
            self.alcance_actual = alcance_anterior # Restaurar el alcance anterior
            return valor_retorno

        elif callable(callee_evaluado): # Para funciones Python simuladas como console.log
            # print(f"[InterpreteJS DEBUG] Llamando a callable (función Python simulada).")
            return callee_evaluado(*valores_argumentos)
        else:
            raise ErrorTiempoEjecucionJS(f"No se puede llamar a algo que no es una función: '{nodo_llamada.callee_nodo}'.")


    def _evaluar_NodoMiembroExpresion(self, nodo_miembro):
        # print(f"[InterpreteJS DEBUG] Evaluando NodoMiembroExpresion.")
        objeto_evaluado = self._evaluar_expresion(nodo_miembro.objeto_nodo)
        
        if nodo_miembro.es_calculado: # obj[propiedad_expresion]
            nombre_propiedad = str(self._evaluar_expresion(nodo_miembro.propiedad_nodo))
        else: # obj.propiedad_identificador
            if not isinstance(nodo_miembro.propiedad_nodo, NodoIdentificadorJS):
                raise ErrorTiempoEjecucionJS("Acceso a propiedad con '.' debe usar un identificador.")
            nombre_propiedad = nodo_miembro.propiedad_nodo.nombre

        # Simulación básica de acceso a propiedades
        if isinstance(objeto_evaluado, dict): # Si el objeto es un diccionario Python (simulando objeto JS)
            if nombre_propiedad in objeto_evaluado:
                return objeto_evaluado[nombre_propiedad]
            else:
                # En JS, acceder a una propiedad no existente devuelve 'undefined'
                # print(f"Advertencia: Propiedad '{nombre_propiedad}' no encontrada en objeto {objeto_evaluado}. Devolviendo undefined (None).")
                return None # Simula undefined
        # (Aquí se podría añadir manejo para arrays, strings, etc.)
        else:
            raise ErrorTiempoEjecucionJS(f"No se puede acceder a la propiedad '{nombre_propiedad}' de un tipo no objeto: {type(objeto_evaluado).__name__}")


    def _evaluar_NodoAsignacionExpresion(self, nodo_asignacion):
        # print(f"[InterpreteJS DEBUG] Evaluando NodoAsignacionExpresion. Operador: {nodo_asignacion.operador}")
        
        # El lado derecho se evalúa primero
        valor_derecho = self._evaluar_expresion(nodo_asignacion.derecha_nodo)

        # El lado izquierdo (lhs) debe ser una referencia a la que se pueda asignar
        # (identificador o acceso a miembro).
        if isinstance(nodo_asignacion.izquierda_nodo, NodoIdentificadorJS):
            nombre_variable = nodo_asignacion.izquierda_nodo.nombre
            # Aquí se manejarían operadores como +=, -=, etc.
            if nodo_asignacion.operador == '=':
                self.alcance_actual.asignar_variable(nombre_variable, valor_derecho)
            # (Añadir otros operadores de asignación aquí)
            else:
                raise ErrorTiempoEjecucionJS(f"Operador de asignación no soportado: {nodo_asignacion.operador}")
            return valor_derecho # La asignación en JS devuelve el valor asignado
        
        elif isinstance(nodo_asignacion.izquierda_nodo, NodoMiembroExpresion):
            # Asignación a propiedad de objeto: obj.prop = valor o obj['prop'] = valor
            objeto_evaluado = self._evaluar_expresion(nodo_asignacion.izquierda_nodo.objeto_nodo)
            
            if nodo_asignacion.izquierda_nodo.es_calculado: # obj[expr]
                nombre_propiedad = str(self._evaluar_expresion(nodo_asignacion.izquierda_nodo.propiedad_nodo))
            else: # obj.prop
                if not isinstance(nodo_asignacion.izquierda_nodo.propiedad_nodo, NodoIdentificadorJS):
                    raise ErrorTiempoEjecucionJS("Acceso a propiedad con '.' debe usar un identificador en asignación.")
                nombre_propiedad = nodo_asignacion.izquierda_nodo.propiedad_nodo.nombre

            if isinstance(objeto_evaluado, dict):
                if nodo_asignacion.operador == '=':
                    objeto_evaluado[nombre_propiedad] = valor_derecho
                else:
                    raise ErrorTiempoEjecucionJS(f"Operador de asignación a miembro no soportado: {nodo_asignacion.operador}")
                return valor_derecho
            else:
                raise ErrorTiempoEjecucionJS(f"No se puede asignar a propiedad de un tipo no objeto: {type(objeto_evaluado).__name__}")
        else:
            raise ErrorTiempoEjecucionJS("El lado izquierdo de una asignación debe ser una variable o propiedad.")
    
    def _evaluar_NodoExpresionBinariaJS(self, nodo_binario):
        # (Como estaba antes, con la lógica para operadores aritméticos, relacionales y lógicos)
        val_izq = self._evaluar_expresion(nodo_binario.izquierda_nodo)
        val_der = self._evaluar_expresion(nodo_binario.derecha_nodo)
        op = nodo_binario.operador_token.lexema # Usar el lexema original para los operadores
        tipo_op = nodo_binario.operador_token.tipo

        # print(f"[InterpreteJS DEBUG] ExpBin: {repr(val_izq)} {op} {repr(val_der)}")

        if tipo_op == TT_OPERADOR_ARITMETICO:
            if op == '+': return val_izq + val_der # JS maneja concatenación y suma
            # Para otros operadores aritméticos, JS intenta convertir a número
            try:
                num_izq = float(val_izq) if not isinstance(val_izq, bool) else (1 if val_izq else 0)
                num_der = float(val_der) if not isinstance(val_der, bool) else (1 if val_der else 0)
            except (ValueError, TypeError):
                 # Si uno no es convertible y no es '+', podría ser NaN o error dependiendo de la operación
                if op != '+': # Si no es + (que puede concatenar)
                    return float('nan') # Comportamiento común en JS
                 # Para '+', si uno es string, el otro se convierte a string. Ya manejado por Python '+'
            
            if op == '-': return num_izq - num_der
            if op == '*': return num_izq * num_der
            if op == '/':
                if num_der == 0: return float('Infinity') if num_izq != 0 else float('nan') # JS division by zero
                return num_izq / num_der
            if op == '%':
                if num_der == 0: return float('nan')
                return num_izq % num_der
            # (Faltan **, ++, -- si se manejan como binarios aquí, pero suelen ser unarios o de actualización)

        elif tipo_op == TT_OPERADOR_COMPARACION:
            # JS tiene coerción de tipos para == y !=
            if op == '==': return val_izq == val_der
            if op == '!=': return val_izq != val_der
            # === y !== son comparaciones estrictas (sin coerción de tipos)
            if op == '===': return val_izq is val_der if type(val_izq) is type(val_der) else False # Simplificación
            if op == '!==': return not (val_izq is val_der if type(val_izq) is type(val_der) else False) # Simplificación
            # Para <, <=, >, >=, JS también hace conversiones numéricas
            try:
                num_izq = float(val_izq) if not isinstance(val_izq, (bool, str)) else val_izq # No convertir str a float para <, > directamente
                num_der = float(val_der) if not isinstance(val_der, (bool, str)) else val_der
                if op == '<': return num_izq < num_der
                if op == '<=': return num_izq <= num_der
                if op == '>': return num_izq > num_der
                if op == '>=': return num_izq >= num_der
            except (ValueError, TypeError):
                 # Si la conversión a número falla para comparaciones relacionales, el resultado es complejo en JS.
                 # Por ahora, si no son directamente comparables, podría ser false.
                 return False


        elif tipo_op == TT_OPERADOR_LOGICO: # &&, || (el lexer ya los tiene como operadores)
            # JS usa evaluación de cortocircuito y devuelve el valor del operando, no necesariamente un booleano.
            if op == '&&': return val_izq and val_der 
            if op == '||': return val_izq or val_der
        
        elif tipo_op == TT_PALABRA_CLAVE and op in ['instanceof', 'in']: # 'in' y 'instanceof'
            if op == 'instanceof': # Muy simplificado
                return isinstance(val_izq, type(val_der)) if val_der is not None else False
            if op == 'in': # Verifica si una propiedad está en un objeto
                if not isinstance(val_der, dict): # Asumimos que val_der es un objeto (dict)
                    raise ErrorTiempoEjecucionJS(f"El operando derecho de 'in' debe ser un objeto.")
                return str(val_izq) in val_der # La clave debe ser string

        raise ErrorTiempoEjecucionJS(f"Operador binario no soportado: '{op}' (tipo: {tipo_op})")

    def _evaluar_NodoArrayLiteralJS(self, nodo_array):
        elementos_evaluados = []
        for elemento_nodo in nodo_array.elementos_nodos:
            # En JS, los elementos vacíos en un array literal (ej. [1,,3]) resultan en "empty slots"
            # que se comportan como undefined en muchos contextos.
            # Si el parser crea un nodo None o un tipo especial para elisiones, se manejaría aquí.
            # Por ahora, asumimos que todos los elementos son expresiones válidas.
            if elemento_nodo is None: # Placeholder para elisión, se trata como undefined
                elementos_evaluados.append(None)
            else:
                elementos_evaluados.append(self._evaluar_expresion(elemento_nodo))
        return elementos_evaluados

    def _evaluar_NodoObjetoLiteralJS(self, nodo_objeto):
        objeto_simulado = {}
        for propiedad_nodo in nodo_objeto.propiedades_nodos:
            clave_prop = ""
            # La clave puede ser un identificador, una cadena o un número.
            # Si es un identificador no entrecomillado, su lexema es la clave.
            # Si es una cadena literal, su valor (sin comillas) es la clave.
            # Si es un número literal, su representación en cadena es la clave.
            if propiedad_nodo.clave_token.tipo == TT_IDENTIFICADOR:
                clave_prop = propiedad_nodo.clave_token.lexema
            elif propiedad_nodo.clave_token.tipo == TT_LITERAL_CADENA:
                clave_prop = propiedad_nodo.clave_token.valor 
            elif propiedad_nodo.clave_token.tipo == TT_LITERAL_NUMERICO:
                clave_prop = str(propiedad_nodo.clave_token.valor)
            else: 
                raise ErrorTiempoEjecucionJS(f"Tipo de clave de propiedad de objeto no válido: {propiedad_nodo.clave_token.tipo}")

            valor_prop = self._evaluar_expresion(propiedad_nodo.valor_nodo)
            objeto_simulado[clave_prop] = valor_prop
        return objeto_simulado

    def _evaluar_NodoExpresionActualizacion(self, nodo_actualizacion): # Para i++, i--
        if not isinstance(nodo_actualizacion.argumento_nodo, NodoIdentificadorJS): # Solo variables
            raise ErrorTiempoEjecucionJS("El operando de un operador de actualización (++/--) debe ser una variable.")

        nombre_var = nodo_actualizacion.argumento_nodo.nombre
        valor_actual = self.alcance_actual.obtener_valor_variable(nombre_var)

        if not isinstance(valor_actual, (int, float)): # Deben ser números
            raise ErrorTiempoEjecucionJS(f"El operando de '{nodo_actualizacion.operador}' debe ser numérico, se obtuvo {type(valor_actual).__name__}.")

        if nodo_actualizacion.es_prefijo: # ++i o --i (no implementado en parser aún)
            if nodo_actualizacion.operador == '++': valor_actual += 1
            elif nodo_actualizacion.operador == '--': valor_actual -= 1
            self.alcance_actual.asignar_variable(nombre_var, valor_actual)
            return valor_actual
        else: # i++ o i-- (postfijo)
            valor_original = valor_actual
            if nodo_actualizacion.operador == '++': valor_actual += 1
            elif nodo_actualizacion.operador == '--': valor_actual -= 1
            self.alcance_actual.asignar_variable(nombre_var, valor_actual)
            return valor_original 

    # --- Métodos para visitar sentencias de control (a implementar) ---
    def visitar_NodoDeclaracionFuncion(self, nodo_func_decl):
        # print(f"[InterpreteJS DEBUG] Declarando función: {nodo_func_decl.nombre}")
        # El alcance de definición es el alcance actual cuando se declara la función.
        funcion_obj = FuncionDefinidaUsuario(
            nodo_func_decl.nombre_funcion_token,
            nodo_func_decl.parametros_tokens,
            nodo_func_decl.cuerpo_nodo_bloque,
            self.alcance_actual # Captura el alcance léxico
        )
        # Las declaraciones de función (no expresiones) se "hoistean" y se declaran con 'var' en el alcance actual.
        self.alcance_actual.declarar_variable(funcion_obj.nombre, 'function', funcion_obj) # 'function' como tipo_declaracion
        print(f"Simulación: Función '{funcion_obj.nombre}' declarada.")


    def visitar_NodoBloqueSentencias(self, nodo_bloque, crear_nuevo_alcance_bloque=False):
       # print(f"[InterpreteJS DEBUG] Visitando NodoBloqueSentencias. Crear nuevo alcance: {crear_nuevo_alcance_bloque}")
        alcance_anterior = self.alcance_actual
        if crear_nuevo_alcance_bloque: # Para let/const dentro de bloques if, for, etc.
            self.alcance_actual = AlcanceJS(padre=alcance_anterior)
        
        try:
            if nodo_bloque.cuerpo_sentencias:
                for sentencia in nodo_bloque.cuerpo_sentencias:
                    self._ejecutar_sentencia_o_declaracion(sentencia)
        except ErrorRetornoJS: # Si un return se propaga desde dentro del bloque
            self.alcance_actual = alcance_anterior # Restaurar alcance
            raise # Re-lanzar para que la llamada a función lo maneje
        
        self.alcance_actual = alcance_anterior # Restaurar alcance al salir del bloque


    def visitar_NodoSentenciaIf(self, nodo_if):
        condicion = self._evaluar_expresion(nodo_if.prueba_nodo)
        if bool(condicion): 
            # Para if/else, el cuerpo (si no es un bloque explícito) se ejecuta en el mismo alcance.
            # Si el cuerpo es un NodoBloqueSentencias, _parse_bloque_sentencias_js ya crea un nuevo alcance
            # si se le indica (lo cual no hacemos aquí por defecto, JS if no crea nuevo scope para var).
            # Para 'let'/'const' dentro de un if sin {}, el alcance es complicado.
            # Por simplicidad, ejecutamos la sentencia en el alcance actual.
            # Si la sentencia es un bloque, _parse_bloque_sentencias_js manejará su propio alcance si es necesario.
            self._ejecutar_sentencia_o_declaracion(nodo_if.consecuente_nodo)
        elif nodo_if.alternativo_nodo:
            self._ejecutar_sentencia_o_declaracion(nodo_if.alternativo_nodo)

    def visitar_NodoBucleFor(self, nodo_for):
        # print(f"[InterpreteJS DEBUG] Visitando NodoBucleFor")
        # Para bucles for con 'let'/'const' en la inicialización, cada iteración
        # conceptualmente tiene su propio alcance para esas variables.
        # Esto es complejo de simular perfectamente sin un manejo de alcances más detallado.
        # Simplificación: si la inicialización es una declaración, se hace en un alcance
        # que rodea al bucle o en el alcance actual si es 'var'.

        alcance_bucle_padre = self.alcance_actual
        # Si la inicialización es una declaración con let/const, debería crear un nuevo alcance para el bucle.
        # Por ahora, la inicialización ocurre en el alcance actual o en el de la función.
        
        if nodo_for.inicializacion_nodo:
            if isinstance(nodo_for.inicializacion_nodo, NodoDeclaracionVariable):
                # Si es 'let' o 'const', idealmente se crea un nuevo alcance para el bucle.
                # Si es 'var', se declara en el alcance de la función o global.
                # Por ahora, lo declaramos en el alcance actual.
                self.visitar_NodoDeclaracionVariable(nodo_for.inicializacion_nodo)
            else: 
                self._evaluar_expresion(nodo_for.inicializacion_nodo)

        while True:
            condicion_resultado = True 
            if nodo_for.condicion_nodo:
                condicion_resultado = self._evaluar_expresion(nodo_for.condicion_nodo)
            
            if not bool(condicion_resultado): 
                break 

            # El cuerpo del bucle for en JS crea un nuevo alcance para declaraciones 'let'/'const'
            # en cada iteración si estas ocurren dentro del cuerpo de un bloque.
            # Si el cuerpo es una sola sentencia, no necesariamente.
            # Por ahora, si el cuerpo es un bloque, _visitar_NodoBloqueSentencias podría manejarlo.
            # Aquí, el cuerpo se ejecuta. Si es un bloque, _visitar_NodoBloqueSentencias se llamará.
            try:
                self._ejecutar_sentencia_o_declaracion(nodo_for.cuerpo_nodo)
            except ErrorRetornoJS: # Un return dentro de un bucle for sale de la función, no solo del bucle.
                self.alcance_actual = alcance_bucle_padre # Restaurar por si acaso
                raise 

            if nodo_for.actualizacion_nodo:
                self._evaluar_expresion(nodo_for.actualizacion_nodo)
        
        self.alcance_actual = alcance_bucle_padre # Asegurar que se restaure el alcance

# Fin de la clase InterpreteJavaScript
