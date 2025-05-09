# src/detector_lenguaje/detector.py
import re
from .pistas_lenguaje import LENGUAJES_SOPORTADOS, PISTAS_LENGUAJE

def detectar_lenguaje(codigo_lineas_o_texto, n_lineas_muestra=20):
    """
    Detecta el lenguaje de programación de un fragmento de código.

    Args:
        codigo_lineas_o_texto (list or str): Una lista de cadenas (líneas de código)
                                            o una única cadena de texto con el código.
        n_lineas_muestra (int): Número máximo de líneas a considerar del inicio del código
                                para la detección.

    Returns:
        tuple: (lenguaje_detectado_str, confianza_float, pistas_activadas_dict)
               - lenguaje_detectado_str: Nombre del lenguaje detectado o "Desconocido".
               - confianza_float: Un valor numérico (puntuación o porcentaje) que indica
                                  la confianza en la detección.
               - pistas_activadas_dict: Un diccionario para depuración que muestra qué pistas
                                        se activaron para cada lenguaje.
    """
    if not codigo_lineas_o_texto:
        return "Desconocido (sin entrada)", 0, {}

    if isinstance(codigo_lineas_o_texto, str):
        codigo_lineas = codigo_lineas_o_texto.splitlines()
    elif isinstance(codigo_lineas_o_texto, list):
        codigo_lineas = codigo_lineas_o_texto
    else:
        return "Desconocido (entrada no válida)", 0, {}

    # Tomar una muestra de líneas no vacías para el análisis
    lineas_relevantes = [linea for linea in codigo_lineas if linea.strip()][:n_lineas_muestra]

    if not lineas_relevantes:
        # Si después de filtrar las primeras n_lineas_muestra no queda nada (ej. solo espacios/saltos)
        # podríamos intentar con todo el código si es corto, o devolver desconocido.
        todas_lineas_relevantes = [linea for linea in codigo_lineas if linea.strip()]
        if not todas_lineas_relevantes:
            return "Desconocido (código vacío o solo espacios)", 0, {}
        # Tomar una muestra de todas las líneas relevantes si las primeras 'n' estaban vacías
        lineas_relevantes = todas_lineas_relevantes[:n_lineas_muestra]
        
    if not lineas_relevantes: # Doble chequeo por si acaso todo el código está vacío
        return "Desconocido (código completamente vacío o solo espacios)", 0, {}

    muestra_texto_completo = "\n".join(lineas_relevantes)

    puntuaciones = {lang: 0 for lang in LENGUAJES_SOPORTADOS}
    # Para depuración: qué pistas se activaron para cada lenguaje
    pistas_activadas_debug = {lang: [] for lang in LENGUAJES_SOPORTADOS}


    # --- Pistas directas y muy fuertes (pueden dar una detección temprana o alta prioridad) ---
    # Estas se pueden manejar antes del bucle principal o dándoles un peso muy alto.
    if re.search(r'<!DOCTYPE\s+html>', muestra_texto_completo, re.IGNORECASE):
        puntuaciones["HTML"] += 200 # Bonificación muy alta
        pistas_activadas_debug["HTML"].append("PISTA_FUERTE: DOCTYPE_HTML_DETECTED")

    if re.search(r'\bprogram\s+\w+;', muestra_texto_completo, re.IGNORECASE) and \
       re.search(r'end\.', "\n".join(codigo_lineas), re.IGNORECASE | re.MULTILINE): # `end.` en todo el código
        puntuaciones["Pascal"] += 150
        pistas_activadas_debug["Pascal"].append("PISTA_FUERTE: PASCAL_PROGRAM_END_DOT")

    if re.search(r'\bdef\s+[a-zA-Z_]\w*\s*\(.*\)\s*:', muestra_texto_completo) and \
       not re.search(r'\bfunction\s', muestra_texto_completo, re.IGNORECASE): # `def` sin `function` cerca
        # Verificar si hay pocos o ningún punto y coma en las líneas significativas
        lineas_con_codigo = [l.strip() for l in lineas_relevantes if l.strip() and not l.strip().startswith('#')]
        if lineas_con_codigo: # Solo si hay líneas con código para analizar
            conteo_punto_coma = sum(1 for l_cod in lineas_con_codigo if l_cod.endswith(';'))
            # Si hay muy pocos punto y coma, es más probable que sea Python
            if (len(lineas_con_codigo) > 2 and conteo_punto_coma / len(lineas_con_codigo) < 0.2) or \
               (len(lineas_con_codigo) <= 2 and conteo_punto_coma == 0):
                puntuaciones["Python"] += 120
                pistas_activadas_debug["Python"].append("PISTA_FUERTE: PYTHON_DEF_POCOS_O_NINGUN_SEMICOLON")

    


    # --- Aplicar todas las pistas del diccionario PISTAS_LENGUAJE ---
    for pista_regex_str, efectos_lenguaje in PISTAS_LENGUAJE.items():
        try:
            # Usamos re.search para encontrar la pista en cualquier parte de la muestra
            # re.MULTILINE permite que ^ y $ funcionen por línea si se usan en el regex
            # re.IGNORECASE hace que la búsqueda no distinga mayúsculas/minúsculas
            if re.search(pista_regex_str, muestra_texto_completo, re.IGNORECASE | re.MULTILINE):
                for lenguaje, puntaje_modificador in efectos_lenguaje.items():
                    if lenguaje in puntuaciones: # Asegurarse de que el lenguaje de la pista está soportado
                        puntuaciones[lenguaje] += puntaje_modificador
                        # Guardar información de depuración
                        pistas_activadas_debug[lenguaje].append(f"PISTA_GENERAL: '{pista_regex_str}' -> {puntaje_modificador:+}") # el :+ fuerza a mostrar el signo
        except re.error as e:
            # Esto no debería ocurrir si todas las expresiones regulares en PISTAS_LENGUAJE son válidas.
            # Es una salvaguarda durante el desarrollo.
            print(f"ADVERTENCIA: Error de Expresión Regular en PISTAS_LENGUAJE: '{pista_regex_str}' - {e}")
            # Podríamos decidir si continuar o detenernos si una pista es inválida.
            # Por ahora, solo imprimimos una advertencia y continuamos con las demás pistas.
            continue

    


    # --- Lógica de refinamiento post-pistas ---
    # Analizar características más generales del código para ajustar puntuaciones.

    # 1. Contar punto y coma al final de líneas no vacías y no comentarios (más globalmente)
    #    Usamos todas las `codigo_lineas` para este análisis, no solo la muestra,
    #    para tener una mejor idea del estilo general si el código es más largo.
    lineas_significativas_completas = [
        l.strip() for l in codigo_lineas 
        if l.strip() and not l.strip().startswith(('#', '//', '--')) and 
           not (l.strip().startswith('/*') and l.strip().endswith('*/')) and
           not (l.strip().startswith('{') and l.strip().endswith('}')) # Excluir líneas que son solo un bloque
    ]

    if lineas_significativas_completas: # Solo si hay algo que contar
        punto_y_comas_final_total = sum(1 for linea_str in lineas_significativas_completas if linea_str.endswith(';'))
        ratio_punto_coma_total = punto_y_comas_final_total / len(lineas_significativas_completas)

        # Si la mayoría de las líneas terminan en punto y coma
        if ratio_punto_coma_total > 0.6: 
            for lang_pc in ["C++", "JavaScript", "PL/SQL", "T-SQL", "Pascal"]: # Lenguajes que usan ;
                if lang_pc in puntuaciones: puntuaciones[lang_pc] += 15
            if "Python" in puntuaciones: puntuaciones["Python"] -= 50 # Fuerte penalización para Python
            if "HTML" in puntuaciones: puntuaciones["HTML"] -= 30 # HTML no usa ; así
            # Registrar esta pista global para depuración
            pistas_activadas_debug.setdefault("REFINAMIENTO_GLOBAL", []).append(f"ALTO_RATIO_PUNTO_COMA ({ratio_punto_coma_total:.2f})")
        # Si muy pocas líneas o ninguna terminan en punto y coma (y hay al menos unas pocas líneas significativas)
        elif ratio_punto_coma_total < 0.1 and len(lineas_significativas_completas) > 2: 
            if "Python" in puntuaciones: puntuaciones["Python"] += 25 # Bonificación para Python
            if "HTML" in puntuaciones: puntuaciones["HTML"] += 10 # HTML no usa ;
            for lang_pc in ["C++", "JavaScript", "PL/SQL", "T-SQL", "Pascal"]:
                if lang_pc in puntuaciones: puntuaciones[lang_pc] -= 10 # Penalización leve
            pistas_activadas_debug.setdefault("REFINAMIENTO_GLOBAL", []).append(f"BAJO_RATIO_PUNTO_COMA ({ratio_punto_coma_total:.2f})")

    # 2. Ajuste por uso de llaves { } (si son balanceadas y frecuentes en la muestra)
    #    Usamos `muestra_texto_completo` para esto, ya que las llaves definen bloques locales.
    llaves_abiertas = muestra_texto_completo.count('{')
    llaves_cerradas = muestra_texto_completo.count('}')
    
    # Si hay llaves y están balanceadas (mismo número de apertura que de cierre)
    if llaves_abiertas > 0 and llaves_abiertas == llaves_cerradas:
        # El factor de llaves limita el impacto si hay muchísimas llaves
        factor_llaves = min(llaves_abiertas, 5) # Considerar hasta 5 pares de llaves para el ajuste
        
        for lang_llaves in ["C++", "JavaScript"]: # Lenguajes que usan mucho { }
            if lang_llaves in puntuaciones: puntuaciones[lang_llaves] += 10 * factor_llaves
        
        # Penalizar lenguajes que no usan llaves o las usan de forma muy diferente
        if "Python" in puntuaciones: puntuaciones["Python"] -= 20 * factor_llaves
        if "Pascal" in puntuaciones: puntuaciones["Pascal"] -= 15 * factor_llaves
        if "HTML" in puntuaciones: puntuaciones["HTML"] -= 10 * factor_llaves # HTML las usa para CSS/JS inline, pero no como bloques primarios
        
        pistas_activadas_debug.setdefault("REFINAMIENTO_GLOBAL", []).append(f"LLAVES_BALANCEADAS_EN_MUESTRA (abiertas: {llaves_abiertas})")

    


    # --- Determinar el lenguaje ganador ---
    
    # Poner un suelo a las puntuaciones (ej. 0) para que no haya negativos al final,
    # ya que algunos puntajes podrían haber bajado mucho debido a penalizaciones.
    # Esto simplifica el cálculo de la "confianza" si la definimos como un porcentaje del total positivo.
    puntuaciones_finales = {lang: max(0, score) for lang, score in puntuaciones.items()}

    # Si todas las puntuaciones finales son 0 (o fueron negativas y se ajustaron a 0),
    # significa que no se encontró ninguna pista lo suficientemente fuerte.
    if not any(p > 0 for p in puntuaciones_finales.values()):
        return "Desconocido (sin pistas claras o puntuaciones negativas)", 0, pistas_activadas_debug

    # Encontrar el lenguaje con la puntuación más alta
    lenguaje_ganador = max(puntuaciones_finales, key=puntuaciones_finales.get)
    puntuacion_ganadora = puntuaciones_finales[lenguaje_ganador]

    # Calcular un porcentaje de confianza (opcional, pero puede ser más intuitivo que la puntuación bruta)
    # Suma de todas las puntuaciones positivas finales.
    total_puntuacion_positiva_acumulada = sum(p for p in puntuaciones_finales.values() if p > 0)
    
    certeza_porcentaje = 0
    if total_puntuacion_positiva_acumulada > 0:
        certeza_porcentaje = (puntuacion_ganadora / total_puntuacion_positiva_acumulada) * 100
    else:
        # Esto no debería ocurrir si ya pasamos el chequeo de 'any(p > 0 ...)'
        # pero es una salvaguarda. Si el ganador tiene 0 y el total es 0.
        certeza_porcentaje = 0




    # --- Umbrales de confianza ---
    # Estos umbrales son empíricos y pueden necesitar ajuste.
    UMBRAL_CONFIANZA_MINIMO_PUNTOS_ABSOLUTOS = 35 # El ganador debe tener al menos esta puntuación.
    UMBRAL_CONFIANZA_MINIMO_PORCENTAJE_RELATIVO = 30 # El ganador debe representar al menos este % del total de puntos positivos.

    # Si la puntuación ganadora es muy baja o su porcentaje relativo es bajo,
    # consideramos la detección como de baja confianza.
    if puntuacion_ganadora < UMBRAL_CONFIANZA_MINIMO_PUNTOS_ABSOLUTOS or \
       (total_puntuacion_positiva_acumulada > 0 and certeza_porcentaje < UMBRAL_CONFIANZA_MINIMO_PORCENTAJE_RELATIVO):
        
        # Creamos un mensaje que indica la baja confianza y cuál podría ser el lenguaje.
        # Podríamos también incluir los N mejores candidatos si quisiéramos.
        # Por ejemplo:
        # sorted_puntuaciones = sorted(puntuaciones_finales.items(), key=lambda item: item[1], reverse=True)
        # top_candidatos_str = ", ".join([f"{lang}({score:.0f}pts)" for lang, score in sorted_puntuaciones if score > 10][:3])
        # mensaje_resultado = f"Desconocido (Baja Confianza. Posibles: {top_candidatos_str})"
        
        mensaje_resultado = f"Desconocido (Baja Confianza: {lenguaje_ganador}? {puntuacion_ganadora:.0f}pts, {certeza_porcentaje:.1f}%)"
        
        # Devolvemos el mensaje de baja confianza, la certeza calculada (que será baja) y las pistas para depuración.
        return mensaje_resultado, certeza_porcentaje, pistas_activadas_debug

    # Si se superan los umbrales de confianza, devolvemos el lenguaje ganador.
    # Se puede elegir devolver la puntuacion_ganadora bruta o el certeza_porcentaje.
    # El porcentaje puede ser más fácil de interpretar para el usuario.
    return lenguaje_ganador, certeza_porcentaje, pistas_activadas_debug