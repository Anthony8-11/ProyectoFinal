# src/nucleo_compilador/tabla_simbolos.py

class TablaSimbolos:
    def __init__(self):
        """
        Inicializa la tabla de símbolos con un alcance global.
        La tabla de símbolos se implementa como una pila de diccionarios,
        donde cada diccionario representa un alcance.
        """
        self.alcances = [{}]  # Pila de diccionarios, el primero es el global
        print(f"[DEBUG TablaSimbolos.__init__] Nueva instancia de TablaSimbolos creada. id(self)={id(self)}, id(self.alcances[0])={id(self.alcances[0])}")

    def entrar_alcance(self):
        """
        Crea un nuevo alcance (empuja un nuevo diccionario a la pila).
        Se llama al entrar a un bloque, función, etc.
        """
        self.alcances.append({})

    def salir_alcance(self):
        """
        Elimina el alcance actual (saca el diccionario de la cima de la pila).
        Se llama al salir de un bloque, función, etc.
        No permite salir del alcance global.
        """
        if len(self.alcances) > 1:
            self.alcances.pop()
        else:
            # Opcional: Podríamos lanzar una excepción o imprimir una advertencia
            # si se intenta salir del alcance global.
            print("Advertencia: Intento de salir del alcance global.")

    def agregar_simbolo(self, nombre, tipo_dato, rol, linea=None, columna=None, valor=None, info_extra=None):
        # Mensaje de depuración inicial
        print(f"[DEBUG TS.agregar_simbolo] INICIO: nombre='{nombre}', tipo_dato='{tipo_dato}', rol='{rol}', linea={linea}")

        # Asegurar que self.alcances exista y tenga al menos un alcance (el global).
        # Esto es una salvaguarda; __init__ debería haber creado el alcance global.
        if not self.alcances:
            print("[DEBUG TS.agregar_simbolo] 'self.alcances' estaba vacío. Creando alcance global [{}]).")
            self.alcances = [{}] # Inicializa o re-inicializa como una lista con un dict vacío.
            if not self.alcances: # No debería fallar, pero por si acaso.
                print("[DEBUG TS.agregar_simbolo] CRÍTICO: No se pudo inicializar 'self.alcances'. No se puede agregar.")
                return False
        
        # Trabajar directamente con el primer diccionario en la lista self.alcances (alcance global).
        # Asumimos que para las declaraciones 'var' del programa principal, siempre es self.alcances[0].
        alcance_global_para_agregar = self.alcances[0] 
        
        print(f"[DEBUG TS.agregar_simbolo] ID del objeto self.alcances[0]: {id(self.alcances[0])}")
        print(f"[DEBUG TS.agregar_simbolo] Contenido de self.alcances[0] ANTES de verificar re-declaración: {alcance_global_para_agregar}")

        if nombre in alcance_global_para_agregar: 
            print(f"[DEBUG TS.agregar_simbolo] '{nombre}' YA EXISTE en self.alcances[0].")
            print(f"Error Semántico (TablaSimbolos): El símbolo '{nombre}' ya está declarado en el alcance global "
                  f"(declarado previamente en L{alcance_global_para_agregar.get(nombre, {}).get('linea', '?')}). "
                  f"No se puede re-declarar en L{linea}.")
            return False 
        
        print(f"[DEBUG TS.agregar_simbolo] '{nombre}' NO existe en self.alcances[0]. Procediendo a agregar.")

        entrada_simbolo = {
            'tipo_dato': tipo_dato,
            'rol': rol,
            'linea': linea,
            'columna': columna,
            'valor': valor,
            'alcance_nivel': 0, # Asumiendo que este es el alcance global (nivel 0)
            'info_extra': info_extra if info_extra is not None else {}
        }
        
        # Modificación directa del diccionario en la lista self.alcances.
        self.alcances[0][nombre] = entrada_simbolo
        
        print(f"[DEBUG TS.agregar_simbolo] Símbolo '{nombre}' AGREGADO a self.alcances[0].")
        print(f"[DEBUG TS.agregar_simbolo] Contenido de self.alcances[0] DESPUÉS de agregar: {self.alcances[0]}")
        print(f"[DEBUG TS.agregar_simbolo] Contenido COMPLETO de self.alcances DESPUÉS de agregar: {self.alcances}")
        return True

    def buscar_simbolo(self, nombre):
        """
        Busca un símbolo por nombre, comenzando desde el alcance actual
        y retrocediendo hacia el alcance global.

        Args:
            nombre (str): El nombre del símbolo a buscar.

        Returns:
            dict or None: El diccionario del símbolo si se encuentra, o None si no.
        """
        for alcance in reversed(self.alcances): # Iterar de adentro hacia afuera
            if nombre in alcance:
                return alcance[nombre]
        return None

    def actualizar_simbolo(self, nombre, **kwargs):
        """
        Actualiza los atributos de un símbolo existente.
        Busca el símbolo en todos los alcances y actualiza la primera ocurrencia encontrada
        (desde el más interno al más externo).

        Args:
            nombre (str): El nombre del símbolo a actualizar.
            **kwargs: Atributos a actualizar (ej: valor="nuevo", utilizado=True).

        Returns:
            bool: True si el símbolo se encontró y actualizó, False en caso contrario.
        """
        for alcance_idx in range(len(self.alcances) - 1, -1, -1):
            alcance_actual = self.alcances[alcance_idx]
            if nombre in alcance_actual:
                for key, value in kwargs.items():
                    if key in alcance_actual[nombre]:
                        alcance_actual[nombre][key] = value
                    else:
                        # Podríamos ser más estrictos y no permitir añadir claves nuevas aquí
                        # o sí, dependiendo del diseño.
                        print(f"Advertencia de Tabla de Símbolos: Atributo '{key}' no es un atributo estándar del símbolo '{nombre}'. Se agregará de todas formas.")
                        alcance_actual[nombre][key] = value # Añade si no existe
                return True
        
        # print(f"Error de Tabla de Símbolos: Símbolo '{nombre}' no encontrado para actualizar.")
        return False

    def obtener_alcance_actual(self):
        """
        Devuelve una copia del diccionario del alcance actual.
        """
        if self.alcances:
            return self.alcances[-1].copy()
        return {}

    def __str__(self):
        """
        Representación en cadena de la tabla de símbolos, mostrando todos los alcances.
        """
        representacion = "Estado de la Tabla de Símbolos:\n"
        for i, alcance in enumerate(self.alcances):
            representacion += f"  Alcance Nivel {i} (Global si 0):\n"
            if not alcance:
                representacion += "    <vacío>\n"
            for nombre_simbolo, detalles_simbolo in alcance.items():
                representacion += f"    - '{nombre_simbolo}': {detalles_simbolo}\n"
        return representacion
    

    def buscar_simbolo_en_alcance_actual(self, nombre):
        """
        Busca un símbolo únicamente en el alcance actual (el diccionario en la cima de la pila).
        Devuelve: El diccionario del símbolo si se encuentra en el alcance actual, o None si no.
        """
        if not self.alcances:
            # Esto no debería ocurrir si la tabla siempre se inicializa con al menos un alcance.
            return None 
        
        alcance_actual = self.alcances[-1] # Obtiene el diccionario del alcance más interno (actual).
        return alcance_actual.get(nombre, None) # Usa .get() para devolver None si la clave no existe.