# src/main.py
import os
import sys
from datetime import datetime
import pytz # Para la fecha/hora

# --- CONTROL DE CONFIGURACIÓN PARA PRUEBAS ---
# Para probar un solo archivo, pon su nombre aquí (ej. "prueba_pascal.pas").
# Si es None, se probarán todos los archivos en la lista archivos_a_probar.
ARCHIVO_ESPECIFICO_A_PROBAR = "prueba_cpp.cpp" 
# ARCHIVO_ESPECIFICO_A_PROBAR = "prueba_tsql.sql" # Ejemplo para probar solo T-SQL
# ARCHIVO_ESPECIFICO_A_PROBAR = "prueba_pascal.pas" # Ejemplo para probar solo Pascal
# --- FIN DE CONTROL DE CONFIGURACIÓN ---

# Configuración de codificación para stdout
if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure') and sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

try:
    from detector_lenguaje.detector import detectar_lenguaje
    from analizador_lexico.lexer_python import LexerPython, TT_ERROR_LEXICO as TT_ERROR_PYTHON, TT_EOF as TT_EOF_PYTHON #PYTHON
    from analizador_lexico.lexer_html import LexerHTML, TT_ERROR_HTML, TT_EOF_HTML #HTML
    from analizador_lexico.lexer_pascal import LexerPascal, TT_ERROR_PASCAL, TT_EOF_PASCAL #PASCAL
    from analizador_lexico.lexer_tsql import LexerTSQL, TT_ERROR_SQL, TT_EOF_SQL #Tsql
    from analizador_sintactico.parser_tsql import ParserTSQL #Tsql
    from simulador_ejecucion.interprete_tsql import InterpreteTSQL #T_SQL
    from analizador_sintactico.parser_pascal import ParserPascal #PASCAL
    from simulador_ejecucion.interprete_pascal import InterpretePascal #PASCAL
    from analizador_lexico.lexer_javascript import LexerJavaScript, TT_ERROR_JS, TT_EOF_JS #JAVASCRIPT
    from analizador_sintactico.parser_javascript import ParserJavaScript #JAVASCRIPT
    from simulador_ejecucion.interprete_javascript import InterpreteJavaScript #JAVASCRIPT
    # IMPORTACIÓN PARA C++ ---
    from analizador_lexico.lexer_cpp import LexerCPP, TT_ERROR_CPP, TT_EOF_CPP
    from analizador_sintactico.parser_cpp import ParserCPP
    from simulador_ejecucion.interprete_cpp import InterpreteCPP





except ImportError as e_import:
    print(f"Error de Importación Específico: {e_import}")
    print("Asegúrate de ejecutar desde el directorio raíz 'simulador_compilador/' usando 'python -m src.main'")
    sys.exit(1)
except Exception as e_general: 
    print(f"Se produjo un error general durante la fase de importación: {e_general}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

DIRECTORIO_EJEMPLOS = "ejemplos_Codigo"

def crear_directorio_si_no_existe(nombre_directorio):
    """Crea un directorio si no existe previamente."""
    if not os.path.exists(nombre_directorio):
        os.makedirs(nombre_directorio)
        print(f"Directorio '{nombre_directorio}' creado.")
    # else:
    #     print(f"Directorio '{nombre_directorio}' ya existe.")


def obtener_fecha_hora_actual_formateada():
    """Obtiene y formatea la fecha y hora actual para la zona horaria de Guatemala."""
    try:
        zona_guatemala = pytz.timezone('America/Guatemala')
        fecha_hora_actual_gt = datetime.now(zona_guatemala)
        return fecha_hora_actual_gt.strftime("%A, %d de %B de %Y, %I:%M:%S %p %Z%z")
    except Exception: 
        return datetime.now().strftime("%A, %d de %B de %Y, %I:%M:%S %p (Hora Local - pytz o zona no disponible)")


def analizar_archivo_y_mostrar(ruta_archivo, nombre_archivo_simple):
    """
    Analiza un archivo de código: detecta el lenguaje, realiza análisis léxico,
    sintáctico (con AST para Pascal) y simulación de ejecución (para Pascal).
    """
    print(f"\n--- Analizando archivo: {nombre_archivo_simple} ---")
    codigo_completo_str = None
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
            codigo_completo_str = archivo.read()

        if not codigo_completo_str.strip():
            print("Resultado: El archivo está vacío o solo contiene espacios/saltos de línea.")
            print("--------------------------------------")
            return
        
        lenguaje_detectado, confianza, _ = detectar_lenguaje(codigo_completo_str)
        print(f"Lenguaje Detectado: {lenguaje_detectado}")
        print(f"Confianza         : {confianza:.2f}%")

        if lenguaje_detectado == "Pascal":
            print("\n--- Análisis Léxico (Pascal) ---")
            ast_generado_pascal = None 
            parser_pascal_instancia = None 
            try:
                lexer_pas = LexerPascal(codigo_completo_str)
                tokens_obtenidos = lexer_pas.tokenizar()
                print(f"Total de tokens generados (Pascal): {len(tokens_obtenidos)}")
                tiene_errores_lexicos_pascal = any(t.tipo == TT_ERROR_PASCAL for t in tokens_obtenidos)
                
                # (Descomentar para imprimir tokens de Pascal)
                # for i, token_obj in enumerate(tokens_obtenidos):
                #     print(f"  {i+1:03d}: {token_obj}")
                
                if tiene_errores_lexicos_pascal:
                    print(">>> Se encontraron errores léxicos en el código Pascal. <<<")
                elif tokens_obtenidos and tokens_obtenidos[-1].tipo == TT_EOF_PASCAL:
                    print(">>> Análisis léxico de Pascal completado sin errores aparentes (finalizado con EOF). <<<")
                else:
                    print(">>> Problema con la salida del lexer de Pascal. <<<")

                if not tiene_errores_lexicos_pascal and tokens_obtenidos and tokens_obtenidos[-1].tipo == TT_EOF_PASCAL:
                    print("\n--- Análisis Sintáctico (Pascal) ---")
                    try:
                        parser_pascal_instancia = ParserPascal(tokens_obtenidos)
                        ast_generado_pascal = parser_pascal_instancia.parse() 
                    except Exception as e_parse_pascal:
                        print(f"ERROR CRÍTICO en la ejecución del Parser de Pascal: {e_parse_pascal}")
                else:
                    print("\n--- Análisis Sintáctico (Pascal) ---")
                    print("No se realizó el análisis sintáctico debido a errores léxicos o problemas con los tokens.")
                print("--- Fin Análisis Sintáctico (Pascal) ---")

                if ast_generado_pascal:
                    print("\n--- Árbol de Sintaxis Abstracto (AST) Generado (Pascal) ---")
                    # print(ast_generado_pascal) # Descomentar para ver el AST
                    print("--- Fin del AST (Pascal) ---")

                    if parser_pascal_instancia and hasattr(parser_pascal_instancia, 'tabla_simbolos') and parser_pascal_instancia.tabla_simbolos:
                        interprete = InterpretePascal(parser_pascal_instancia.tabla_simbolos)
                        interprete.interpretar(ast_generado_pascal)
                    else:
                        print("\nNo se pudo iniciar la simulación: falta la instancia del parser o la tabla de símbolos.")
                elif not tiene_errores_lexicos_pascal and \
                     (parser_pascal_instancia is None or (hasattr(parser_pascal_instancia, 'errores_sintacticos') and not parser_pascal_instancia.errores_sintacticos)):
                    print("\nNo se generó un AST para Pascal, aunque no se reportaron errores explícitos.")
            except Exception as e_proc_pascal:
                print(f"ERROR SEVERO durante el procesamiento de Pascal: {e_proc_pascal}")
            print("--- Fin Procesamiento Pascal ---")
        
        elif lenguaje_detectado == "Python":
            print("\n--- Análisis Léxico (Python) ---")
            if not codigo_completo_str.strip():
                print("El código Python está vacío.")
            else:
                lexer_py = LexerPython(codigo_completo_str)
                tokens_py = lexer_py.tokenizar()
                print(f"Total de tokens generados (Python): {len(tokens_py)}")
                if any(t.tipo == TT_ERROR_PYTHON for t in tokens_py):
                    print(">>> Se encontraron errores léxicos en Python. <<<")
                elif tokens_py and tokens_py[-1].tipo == TT_EOF_PYTHON:
                    print(">>> Análisis léxico de Python completado. <<<")
            print("--- Fin Análisis Léxico (Python) ---")

        elif lenguaje_detectado == "HTML":
            print("\n--- Análisis Léxico (HTML) ---")
            if not codigo_completo_str.strip():
                print("El código HTML está vacío.")
            else:
                lexer_html = LexerHTML(codigo_completo_str)
                tokens_html = lexer_html.tokenizar()
                print(f"Total de tokens generados (HTML): {len(tokens_html)}")
                if any(t.tipo == TT_ERROR_HTML for t in tokens_html):
                    print(">>> Se encontraron errores léxicos en HTML. <<<")
                elif tokens_html and tokens_html[-1].tipo == TT_EOF_HTML:
                    print(">>> Análisis léxico de HTML completado. <<<")
            print("--- Fin Análisis Léxico (HTML) ---")

        elif lenguaje_detectado == "T-SQL":
            print("\n--- Análisis Léxico (T-SQL) ---")
            ast_generado_tsql = None # Para almacenar el AST de T-SQL
            parser_tsql_instancia = None # Para almacenar la instancia del parser

            if not codigo_completo_str.strip(): 
                print("El código T-SQL para el análisis léxico está vacío.")
            else:
                try:
                    # Fase Léxica para T-SQL
                    lexer_tsql = LexerTSQL(codigo_completo_str)
                    tokens_obtenidos_tsql = lexer_tsql.tokenizar()
                    
                    print(f"Total de tokens generados (T-SQL): {len(tokens_obtenidos_tsql)}")
                    tiene_errores_lexicos_tsql = any(t.tipo == TT_ERROR_SQL for t in tokens_obtenidos_tsql)
                    
                    # (Descomentar para imprimir tokens de T-SQL)
                    # for i, token_obj in enumerate(tokens_obtenidos_tsql): 
                    #     print(f"  {i+1:03d}: {token_obj}") 
                    
                    if tiene_errores_lexicos_tsql:
                        print(">>> Se encontraron errores léxicos en el código T-SQL. <<<")
                    elif tokens_obtenidos_tsql and tokens_obtenidos_tsql[-1].tipo == TT_EOF_SQL:
                        print(">>> Análisis léxico de T-SQL completado sin errores aparentes (finalizado con EOF). <<<")
                    else:
                        print(">>> Problema con la salida del lexer de T-SQL. <<<")

                    # Fase Sintáctica para T-SQL (solo si la léxica fue exitosa)
                    if not tiene_errores_lexicos_tsql and \
                       tokens_obtenidos_tsql and \
                       tokens_obtenidos_tsql[-1].tipo == TT_EOF_SQL:
                        
                        print("\n--- Análisis Sintáctico (T-SQL) ---")
                        try:
                            parser_tsql_instancia = ParserTSQL(tokens_obtenidos_tsql)
                            ast_generado_tsql = parser_tsql_instancia.parse()
                            # Los mensajes de éxito/error del parsing ya se imprimen desde parser_tsql_instancia.parse()
                        except Exception as e_parse_tsql:
                            print(f"ERROR CRÍTICO en la ejecución del Parser de T-SQL: {e_parse_tsql}")
                            # import traceback; traceback.print_exc() # Descomentar para más detalles
                    else:
                        print("\n--- Análisis Sintáctico (T-SQL) ---")
                        print("No se realizó el análisis sintáctico debido a errores léxicos o problemas con los tokens.")
                    print("--- Fin Análisis Sintáctico (T-SQL) ---")

                    # Visualización del AST de T-SQL (si se generó)
                    if ast_generado_tsql:
                        print("\n--- Árbol de Sintaxis Abstracto (AST) Generado (T-SQL) ---")
                        print(ast_generado_tsql) # Imprime usando los __repr__ de los nodos AST de SQL
                        print("--- Fin del AST (T-SQL) ---")

                        print("\n--- Simulación de Ejecución (T-SQL) ---")
                        try:
                            # No pasamos tabla de símbolos al intérprete T-SQL por ahora,
                            # ya que el parser T-SQL no la está usando activamente aún.
                            # El intérprete T-SQL tiene su propia self.catalogo_tablas y self.memoria_variables_tsql.
                            interprete_tsql = InterpreteTSQL() 
                            interprete_tsql.interpretar_script(ast_generado_tsql)
                        except Exception as e_interp_tsql:
                            print(f"ERROR CRÍTICO durante la simulación de T-SQL: {e_interp_tsql}")
                            # import traceback; traceback.print_exc() # Descomentar para más detalles

                    elif not tiene_errores_lexicos_tsql and \
                         (parser_tsql_instancia is None or (hasattr(parser_tsql_instancia, 'errores_sintacticos') and not parser_tsql_instancia.errores_sintacticos)):
                        print("\nNo se generó un AST para T-SQL, aunque no se reportaron errores explícitos (revisar lógica del parser).")

                except Exception as e_proc_tsql:
                    print(f"ERROR SEVERO durante el procesamiento de T-SQL: {e_proc_tsql}")
                    # import traceback; traceback.print_exc() # Descomentar para más detalles
            print("--- Fin Procesamiento T-SQL ---")

        # --- BLOQUE PARA JAVASCRIPT ---
        elif lenguaje_detectado == "JavaScript":
            print("\n--- Análisis Léxico (JavaScript) ---")
            ast_generado_js = None
            parser_js_instancia = None

            if not codigo_completo_str.strip():
                print("El código JavaScript para el análisis léxico está vacío.")
            else:
                try:
                    # Fase Léxica para JavaScript
                    lexer_js = LexerJavaScript(codigo_completo_str)
                    tokens_obtenidos_js = lexer_js.tokenizar()
                    
                    print(f"Total de tokens generados (JavaScript): {len(tokens_obtenidos_js)}")
                    tiene_errores_lexicos_js = any(t.tipo == TT_ERROR_JS for t in tokens_obtenidos_js)
                    
                    # (Descomentar para imprimir tokens de JavaScript)
                    # for i, token_obj in enumerate(tokens_obtenidos_js): 
                    #     print(f"  {i+1:03d}: {token_obj}") 
                    
                    if tiene_errores_lexicos_js:
                        print(">>> Se encontraron errores léxicos en el código JavaScript. <<<")
                    elif tokens_obtenidos_js and tokens_obtenidos_js[-1].tipo == TT_EOF_JS:
                        print(">>> Análisis léxico de JavaScript completado sin errores aparentes (finalizado con EOF). <<<")
                    else:
                        print(">>> Problema con la salida del lexer de JavaScript. <<<")

                    # Fase Sintáctica para JavaScript (solo si la léxica fue exitosa)
                    if not tiene_errores_lexicos_js and \
                       tokens_obtenidos_js and \
                       tokens_obtenidos_js[-1].tipo == TT_EOF_JS:
                        
                        print("\n--- Análisis Sintáctico (JavaScript) ---")
                        try:
                            parser_js_instancia = ParserJavaScript(tokens_obtenidos_js)
                            ast_generado_js = parser_js_instancia.parse()
                            # Los mensajes de éxito/error del parsing ya se imprimen desde parser_js_instancia.parse()
                        except Exception as e_parse_js:
                            print(f"ERROR CRÍTICO en la ejecución del Parser de JavaScript: {e_parse_js}")
                            import traceback; traceback.print_exc() # Para más detalles del error del parser
                    else:
                        print("\n--- Análisis Sintáctico (JavaScript) ---")
                        print("No se realizó el análisis sintáctico debido a errores léxicos o problemas con los tokens.")
                    print("--- Fin Análisis Sintáctico (JavaScript) ---")

                    # Visualización del AST de JavaScript (si se generó)
                    if ast_generado_js:
                        print("\n--- Árbol de Sintaxis Abstracto (AST) Generado (JavaScript) ---")
                        # print(ast_generado_js) # Imprime usando los __repr__ de los nodos AST de JS
                        print("--- Fin del AST (JavaScript) ---")

                        print("\n--- Simulación de Ejecución (JavaScript) ---") 
                        try:
                            # El intérprete JS maneja sus propios alcances y objetos globales internamente.
                            interprete_js = InterpreteJavaScript() 
                            interprete_js.interpretar_script(ast_generado_js)
                        except Exception as e_interp_js:
                            print(f"ERROR CRÍTICO durante la simulación de JavaScript: {e_interp_js}")
                            import traceback; traceback.print_exc()
                        
                        # Aquí iría la llamada al intérprete/simulador de JavaScript si lo tuviéramos
                        # print("\n--- Simulación de Ejecución (JavaScript) ---")
                        # interprete_js = InterpreteJavaScript(parser_js_instancia.tabla_simbolos) # Si usa tabla de símbolos
                        # interprete_js.interpretar(ast_generado_js)
                        # print("--- Fin Simulación de Ejecución (JavaScript) ---")

                    elif not tiene_errores_lexicos_js and \
                         (parser_js_instancia is None or (hasattr(parser_js_instancia, 'errores_sintacticos') and not parser_js_instancia.errores_sintacticos)):
                        print("\nNo se generó un AST para JavaScript, aunque no se reportaron errores explícitos (revisar lógica del parser).")

                except Exception as e_proc_js:
                    print(f"ERROR SEVERO durante el procesamiento de JavaScript: {e_proc_js}")
                    import traceback; traceback.print_exc() # Para más detalles
            print("--- Fin Procesamiento JavaScript ---")

        # --- NUEVO BLOQUE PARA C++ ---
        elif lenguaje_detectado == "C++":
            print("\n--- Análisis Léxico (C++) ---")
            ast_generado_cpp = None
            parser_cpp_instancia = None

            if not codigo_completo_str.strip():
                print("El código C++ para el análisis léxico está vacío.")
            else:
                try:
                    # Fase Léxica para C++
                    lexer_cpp = LexerCPP(codigo_completo_str)
                    tokens_obtenidos_cpp = lexer_cpp.tokenizar()
                    
                    print(f"Total de tokens generados (C++): {len(tokens_obtenidos_cpp)}")
                    tiene_errores_lexicos_cpp = any(t.tipo == TT_ERROR_CPP for t in tokens_obtenidos_cpp)
                    
                    # (Descomentar para imprimir tokens de C++)
                    # for i, token_obj in enumerate(tokens_obtenidos_cpp): 
                    #     print(f"  {i+1:03d}: {token_obj}") 
                    
                    if tiene_errores_lexicos_cpp:
                        print(">>> Se encontraron errores léxicos en el código C++. <<<")
                    elif tokens_obtenidos_cpp and tokens_obtenidos_cpp[-1].tipo == TT_EOF_CPP:
                        print(">>> Análisis léxico de C++ completado sin errores aparentes (finalizado con EOF). <<<")
                    else:
                        print(">>> Problema con la salida del lexer de C++. <<<")

                    # Fase Sintáctica para C++ (solo si la léxica fue exitosa)
                    if not tiene_errores_lexicos_cpp and \
                       tokens_obtenidos_cpp and \
                       tokens_obtenidos_cpp[-1].tipo == TT_EOF_CPP:
                        
                        print("\n--- Análisis Sintáctico (C++) ---")
                        try:
                            parser_cpp_instancia = ParserCPP(tokens_obtenidos_cpp)
                            ast_generado_cpp = parser_cpp_instancia.parse()
                        except Exception as e_parse_cpp:
                            print(f"ERROR CRÍTICO en la ejecución del Parser de C++: {e_parse_cpp}")
                            # import traceback; traceback.print_exc() # Para más detalles
                    else:
                        print("\n--- Análisis Sintáctico (C++) ---")
                        print("No se realizó el análisis sintáctico debido a errores léxicos o problemas con los tokens.")
                    print("--- Fin Análisis Sintáctico (C++) ---")

                    # Visualización del AST de C++ (si se generó)
                    if ast_generado_cpp:
                        print("\n--- Árbol de Sintaxis Abstracto (AST) Generado (C++) ---")
                        #print(ast_generado_cpp) # Imprime usando los __repr__ de los nodos AST de C++
                        print("--- Fin del AST (C++) ---")

                        print("\n--- Simulación de Ejecución (C++) ---") 
                        try:
                            interprete_cpp = InterpreteCPP() 
                            interprete_cpp.interpretar_unidad_traduccion(ast_generado_cpp)
                        except Exception as e_interp_cpp:
                            print(f"ERROR CRÍTICO durante la simulación de C++: {e_interp_cpp}")
                            import traceback; traceback.print_exc() 

                    elif not tiene_errores_lexicos_cpp and \
                         (parser_cpp_instancia is None or (hasattr(parser_cpp_instancia, 'errores_sintacticos') and not parser_cpp_instancia.errores_sintacticos)):
                        print("\nNo se generó un AST para C++, aunque no se reportaron errores explícitos (revisar lógica del parser).")

                except Exception as e_proc_cpp:
                    print(f"ERROR SEVERO durante el procesamiento de C++: {e_proc_cpp}")
                    import traceback; traceback.print_exc() # Para más detalles
            print("--- Fin Procesamiento C++ ---")

#FIN
        else:
            print(f"Análisis detallado para '{lenguaje_detectado}' no implementado aún.")

    except FileNotFoundError:
        print(f"Error: El archivo '{ruta_archivo}' no fue encontrado. Por favor, asegúrate de que exista en la carpeta '{DIRECTORIO_EJEMPLOS}'.")
    except Exception as e:
        print(f"Ocurrió un error inesperado al procesar el archivo '{nombre_archivo_simple}': {e}")
        import traceback 
        traceback.print_exc()
    print("--------------------------------------")


if __name__ == "__main__":
    print("Iniciando Simulador de Compilador - Prueba de Fases")
    print("Fecha y Hora Actual:", obtener_fecha_hora_actual_formateada())
    print("="*50)

    # Solo se crea el directorio de ejemplos si no existe.
    # Los archivos de ejemplo ahora deben ser creados manualmente por el usuario.
    crear_directorio_si_no_existe(DIRECTORIO_EJEMPLOS)
    print(f"Asegúrate de que tus archivos de prueba estén en la carpeta: '{os.path.abspath(DIRECTORIO_EJEMPLOS)}'")
    
    if ARCHIVO_ESPECIFICO_A_PROBAR:
        # Analizar solo el archivo especificado
        print(f"\nModo de prueba: Analizando solo '{ARCHIVO_ESPECIFICO_A_PROBAR}'")
        ruta_completa = os.path.join(DIRECTORIO_EJEMPLOS, ARCHIVO_ESPECIFICO_A_PROBAR)
        if os.path.exists(ruta_completa):
            analizar_archivo_y_mostrar(ruta_completa, ARCHIVO_ESPECIFICO_A_PROBAR)
        else:
            print(f"Archivo de prueba específico '{ARCHIVO_ESPECIFICO_A_PROBAR}' no encontrado en '{DIRECTORIO_EJEMPLOS}'.")
    else:
        # Analizar todos los archivos en la lista si no se especifica uno.
        print("\nModo de prueba: Analizando todos los archivos de la lista predefinida.")
        archivos_a_probar = [
            "prueba_pascal.pas",
            "prueba_python.py",
            "prueba_html.html",
            "prueba_tsql.sql", 
        ]
        for nombre_archivo_simple in archivos_a_probar:
            ruta_completa = os.path.join(DIRECTORIO_EJEMPLOS, nombre_archivo_simple)
            if os.path.exists(ruta_completa):
                analizar_archivo_y_mostrar(ruta_completa, nombre_archivo_simple)
            else:
                print(f"Archivo de prueba '{nombre_archivo_simple}' no encontrado en '{DIRECTORIO_EJEMPLOS}'. Asegúrate de crearlo.")
    
    print("\nPrueba del Simulador de Compilador Finalizada.")

