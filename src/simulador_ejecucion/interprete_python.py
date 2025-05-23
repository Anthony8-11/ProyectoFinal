# src/simulador_ejecucion/interprete_python.py
import re 

# Importar los nodos AST del parser de Python
try:
    from analizador_sintactico.parser_python import (
        NodoModulo, NodoSentencia, NodoExpresion, NodoDefinicionFuncion,
        NodoBloque, NodoSentenciaExpresion, NodoAsignacion, NodoLlamadaFuncion,
        NodoIdentificador, NodoLiteral, NodoExpresionBinaria, NodoSentenciaIf,
        NodoSentenciaReturn, NodoSentenciaWhile, NodoSentenciaFor, 
        NodoExpresionUnaria, NodoSentenciaBreak, NodoSentenciaContinue 
    )
    from analizador_lexico.lexer_python import Token, TT_CADENA, TT_OPERADOR, TT_PALABRA_CLAVE 
except ImportError as e_ip_py:
    print(f"Error de importación en interprete_python.py: {e_ip_py}")
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
    class Token: pass; TT_CADENA = "CADENA"; TT_OPERADOR = "OPERADOR"; TT_PALABRA_CLAVE = "PALABRA_CLAVE"

class ErrorTiempoEjecucionPython(RuntimeError):
    """Error general en tiempo de ejecución para el intérprete de Python."""
    pass

class ValorRetorno(Exception):
    """Excepción para manejar la sentencia 'return' y propagar su valor."""
    def __init__(self, valor):
        super().__init__("Sentencia return ejecutada")
        self.valor = valor

# --- NUEVAS EXCEPCIONES PARA CONTROL DE BUCLES ---
class BreakException(Exception):
    """Excepción para manejar la sentencia 'break'."""
    pass

class ContinueException(Exception):
    """Excepción para manejar la sentencia 'continue'."""
    pass
# --- FIN DE NUEVAS EXCEPCIONES ---

class AlcancePython:
    def __init__(self, padre=None, nombre_alcance="global"):
        self.simbolos = {}  
        self.padre = padre
        self.nombre_alcance = nombre_alcance

    def declarar(self, nombre_simbolo, valor):
        self.simbolos[nombre_simbolo] = valor

    def asignar(self, nombre_simbolo, valor):
        self.simbolos[nombre_simbolo] = valor

    def obtener(self, nombre_simbolo):
        if nombre_simbolo in self.simbolos:
            return self.simbolos[nombre_simbolo]
        elif self.padre:
            return self.padre.obtener(nombre_simbolo) 
        else: 
            if nombre_simbolo == 'range': 
                return range 
            raise ErrorTiempoEjecucionPython(f"Nombre '{nombre_simbolo}' no está definido.")

class FuncionDefinidaPython:
    def __init__(self, nombre_token, parametros_tokens_lista, cuerpo_nodo, alcance_definicion):
        self.nombre = nombre_token.lexema
        self.nombres_parametros = [p.lexema for p in parametros_tokens_lista]
        self.cuerpo_nodo = cuerpo_nodo 
        self.alcance_definicion = alcance_definicion 

    def __repr__(self):
        return f"<FuncionPython: {self.nombre}({', '.join(self.nombres_parametros)})>"


class InterpretePython:
    def __init__(self):
        self.alcance_global = AlcancePython(nombre_alcance="global")
        self.alcance_actual = self.alcance_global
        self.alcance_global.declarar('print', self._simular_print)
        self.alcance_global.declarar('range', range) 

    def _simular_print(self, *args):
        output = " ".join(map(str, args))
        print(output)
        return None 

    def interpretar_modulo(self, nodo_modulo):
        if not isinstance(nodo_modulo, NodoModulo):
            print("Error del Intérprete Python: Se esperaba un NodoModulo.")
            return
        
        resultado_final = None
        try:
            for sentencia_nodo in nodo_modulo.cuerpo_sentencias:
                resultado_sentencia = self.visitar(sentencia_nodo)
                if resultado_sentencia is not None: 
                    resultado_final = resultado_sentencia 
        except ErrorTiempoEjecucionPython as e_runtime:
            print(f"Error en Tiempo de Ejecución (Python): {e_runtime}")
        except ValorRetorno as vr: 
            print(f"Error de Sintaxis (Simulado): 'return' fuera de función. Valor: {vr.valor}")
        except BreakException:
            print("Error de Sintaxis (Simulado): 'break' fuera de bucle.")
        except ContinueException:
            print("Error de Sintaxis (Simulado): 'continue' fuera de bucle.")
        except Exception as e_general:
            print(f"Error Inesperado durante la Interpretación de Python: {e_general}")
            import traceback
            traceback.print_exc()
        return resultado_final

    def visitar(self, nodo):
        nombre_metodo_visitador = f'visitar_{type(nodo).__name__}'
        visitador = getattr(self, nombre_metodo_visitador, self._visitador_no_encontrado)
        return visitador(nodo)

    def _visitador_no_encontrado(self, nodo):
        raise ErrorTiempoEjecucionPython(f"No hay método visitador_Nodo... para el tipo de nodo {type(nodo).__name__}")

    def visitar_NodoDefinicionFuncion(self, nodo_def_func):
        nombre_funcion = nodo_def_func.nombre_funcion_token.lexema
        funcion_obj = FuncionDefinidaPython(
            nodo_def_func.nombre_funcion_token,
            nodo_def_func.parametros_tokens,
            nodo_def_func.cuerpo_bloque_nodo,
            self.alcance_actual 
        )
        self.alcance_actual.declarar(nombre_funcion, funcion_obj)
        return None

    def visitar_NodoBloque(self, nodo_bloque):
        resultado_bloque = None
        for sentencia_nodo in nodo_bloque.sentencias:
            # No necesitamos try-except para Break/Continue aquí, se manejan en los bucles
            resultado_sentencia = self.visitar(sentencia_nodo)
            if resultado_sentencia is not None: 
                resultado_bloque = resultado_sentencia
        return resultado_bloque


    def visitar_NodoSentenciaExpresion(self, nodo_sent_expr):
        return self._evaluar_expresion(nodo_sent_expr.expresion_nodo)

    def visitar_NodoAsignacion(self, nodo_asignacion):
        nombre_variable = nodo_asignacion.objetivo_nodo.nombre 
        valor = self._evaluar_expresion(nodo_asignacion.valor_nodo)
        self.alcance_actual.asignar(nombre_variable, valor)
        return None

    def visitar_NodoSentenciaIf(self, nodo_if):
        condicion_val = self._evaluar_expresion(nodo_if.prueba_nodo)
        if bool(condicion_val):
            return self.visitar(nodo_if.cuerpo_then_nodo) 
        elif nodo_if.cuerpo_else_nodo:
            return self.visitar(nodo_if.cuerpo_else_nodo)
        return None

    def visitar_NodoSentenciaReturn(self, nodo_return):
        valor_a_retornar = None
        if nodo_return.valor_retorno_nodo:
            valor_a_retornar = self._evaluar_expresion(nodo_return.valor_retorno_nodo)
        raise ValorRetorno(valor_a_retornar)

    # --- MÉTODOS VISITADORES PARA BREAK Y CONTINUE ---
    def visitar_NodoSentenciaBreak(self, nodo_break):
        # print("[InterpretePython DEBUG] Ejecutando break")
        raise BreakException()

    def visitar_NodoSentenciaContinue(self, nodo_continue):
        # print("[InterpretePython DEBUG] Ejecutando continue")
        raise ContinueException()


    # --- MÉTODO visitar_NodoSentenciaWhile ACTUALIZADO ---
    def visitar_NodoSentenciaWhile(self, nodo_while):
        while True:
            condicion_evaluada = self._evaluar_expresion(nodo_while.condicion_nodo)
            if not bool(condicion_evaluada):
                break
            try:
                self.visitar(nodo_while.cuerpo_bloque_nodo) 
            except BreakException:
                # print("[InterpretePython DEBUG] Break capturado en while")
                break # Salir del bucle while
            except ContinueException:
                # print("[InterpretePython DEBUG] Continue capturado en while")
                continue # Saltar al inicio de la siguiente iteración del while
            except ValorRetorno: 
                raise # Propagar return fuera del bucle
        return None
 

    # --- MÉTODO visitar_NodoSentenciaFor ACTUALIZADO ---
    def visitar_NodoSentenciaFor(self, nodo_for):
        nombre_variable_iteracion = nodo_for.variable_iteracion_token.lexema
        iterable_obj = self._evaluar_expresion(nodo_for.expresion_iterable_nodo)
        
        alcance_anterior = self.alcance_actual
        # La variable del bucle for se asigna en el alcance actual (o el que contiene el for)
        # self.alcance_actual = AlcancePython(padre=alcance_anterior, nombre_alcance=f"for_loop_var_{nombre_variable_iteracion}")

        try:
            for valor_iteracion in iterable_obj:
                self.alcance_actual.declarar(nombre_variable_iteracion, valor_iteracion) 
                try:
                    self.visitar(nodo_for.cuerpo_bloque_nodo)
                except BreakException:
                    # print("[InterpretePython DEBUG] Break capturado en for")
                    break # Salir del bucle for
                except ContinueException:
                    # print("[InterpretePython DEBUG] Continue capturado en for")
                    continue # Saltar a la siguiente iteración del for
                except ValorRetorno: 
                    # self.alcance_actual = alcance_anterior # No es necesario si no cambiamos de alcance
                    raise
        except TypeError: 
            raise ErrorTiempoEjecucionPython(f"El objeto para el bucle FOR no es iterable: {type(iterable_obj).__name__}")
        # finally: # No es necesario si no cambiamos de alcance para la variable de iteración
            # self.alcance_actual = alcance_anterior
        return None
   

    def _evaluar_expresion(self, nodo_expr):
        # (Como estaba antes)
        if isinstance(nodo_expr, NodoLiteral):
            if nodo_expr.literal_token.tipo == TT_CADENA and \
               nodo_expr.literal_token.lexema.lower().startswith(('f"', "f'", 'rf"', "rf'", 'fr"', "fr'")):
                formato_str = str(nodo_expr.valor) 
                def reemplazar_variable(match):
                    nombre_variable = match.group(1).strip() 
                    try:
                        valor_variable = self.alcance_actual.obtener(nombre_variable)
                        return str(valor_variable)
                    except ErrorTiempoEjecucionPython:
                        return match.group(0) 
                resultado_interpolado = re.sub(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}', reemplazar_variable, formato_str)
                return resultado_interpolado
            else:
                return nodo_expr.valor 
        elif isinstance(nodo_expr, NodoIdentificador):
            return self.alcance_actual.obtener(nodo_expr.nombre)
        elif isinstance(nodo_expr, NodoLlamadaFuncion):
            return self.visitar_NodoLlamadaFuncion(nodo_expr)
        elif isinstance(nodo_expr, NodoExpresionBinaria):
            val_izq = self._evaluar_expresion(nodo_expr.izquierda_nodo)
            val_der = self._evaluar_expresion(nodo_expr.derecha_nodo)
            op = nodo_expr.operador 
            if op == '+': return val_izq + val_der
            if op == '-': return val_izq - val_der
            if op == '*': return val_izq * val_der
            if op == '/': 
                if val_der == 0: raise ErrorTiempoEjecucionPython("División por cero")
                return val_izq / val_der
            if op == '//':
                if val_der == 0: raise ErrorTiempoEjecucionPython("División entera por cero")
                return val_izq // val_der
            if op == '%':
                if val_der == 0: raise ErrorTiempoEjecucionPython("Módulo por cero")
                return val_izq % val_der
            if op == '**':
                return val_izq ** val_der
            if op == '>': return val_izq > val_der
            if op == '<': return val_izq < val_der
            if op == '==': return val_izq == val_der
            if op == '!=': return val_izq != val_der
            if op == '>=': return val_izq >= val_der
            if op == '<=': return val_izq <= val_der
            if op.lower() == 'in': return val_izq in val_der 
            if op.lower() == 'not in': return val_izq not in val_der 
            if op.lower() == 'is': return val_izq is val_der
            if op.lower() == 'is not': return val_izq is not val_der
            if op == 'and': return bool(val_izq) and bool(val_der) 
            if op == 'or':  return bool(val_izq) or bool(val_der)  
            raise ErrorTiempoEjecucionPython(f"Operador binario '{op}' no soportado.")
        elif isinstance(nodo_expr, NodoExpresionUnaria):
            op = nodo_expr.operador_token.lexema.lower()
            operando_val = self._evaluar_expresion(nodo_expr.operando_nodo)
            if op == 'not': return not bool(operando_val)
            if op == '-': return -operando_val
            if op == '+': return +operando_val 
            raise ErrorTiempoEjecucionPython(f"Operador unario '{op}' no soportado.")
        else:
            raise ErrorTiempoEjecucionPython(f"Tipo de nodo de expresión '{type(nodo_expr).__name__}' no soportado para evaluación.")

    def visitar_NodoLlamadaFuncion(self, nodo_llamada):
    
        nombre_funcion_a_llamar = None
        if isinstance(nodo_llamada.callee_nodo, NodoIdentificador):
            nombre_funcion_a_llamar = nodo_llamada.callee_nodo.nombre
        else:
            raise ErrorTiempoEjecucionPython(f"Llamada a callee de tipo no soportado: {type(nodo_llamada.callee_nodo).__name__}")
        try:
            funcion_obj = self.alcance_actual.obtener(nombre_funcion_a_llamar)
        except ErrorTiempoEjecucionPython:
            raise ErrorTiempoEjecucionPython(f"Función o método '{nombre_funcion_a_llamar}' no definido.")
        argumentos_evaluados = [self._evaluar_expresion(arg) for arg in nodo_llamada.argumentos_nodos]
        if isinstance(funcion_obj, FuncionDefinidaPython):
            alcance_funcion = AlcancePython(padre=funcion_obj.alcance_definicion, nombre_alcance=f"funcion_{funcion_obj.nombre}")
            if len(argumentos_evaluados) != len(funcion_obj.nombres_parametros):
                raise ErrorTiempoEjecucionPython(
                    f"Función '{funcion_obj.nombre}' esperaba {len(funcion_obj.nombres_parametros)} argumentos, "
                    f"pero recibió {len(argumentos_evaluados)}."
                )
            for nombre_param, valor_arg in zip(funcion_obj.nombres_parametros, argumentos_evaluados):
                alcance_funcion.declarar(nombre_param, valor_arg)
            alcance_anterior = self.alcance_actual
            self.alcance_actual = alcance_funcion
            valor_retorno = None
            try:
                self.visitar(funcion_obj.cuerpo_nodo) 
            except ValorRetorno as vr:
                valor_retorno = vr.valor
            self.alcance_actual = alcance_anterior 
            return valor_retorno
        elif callable(funcion_obj): 
            return funcion_obj(*argumentos_evaluados)
        else:
            raise ErrorTiempoEjecucionPython(f"'{nombre_funcion_a_llamar}' no es una función llamable.")

# Fin de la clase InterpretePython
