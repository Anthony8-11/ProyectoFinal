# src/nucleo_compilador/tabla_simbolos.py

class TablaSimbolos:
    def __init__(self):
        """
        Inicializa la tabla de símbolos con un alcance global.
        La tabla de símbolos se implementa como una pila de diccionarios,
        donde cada diccionario representa un alcance.
        """
        self.alcances = [{}]  # Pila de diccionarios, el primero es el global

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

    def agregar_simbolo(self, nombre, tipo_dato, rol, valor=None, 
                        inicializado=False, utilizado=False, 
                        parametros=None, tipo_retorno=None, 
                        linea=None, columna=None):
        """
        Agrega un nuevo símbolo al alcance actual (el diccionario en la cima de la pila).

        Args:
            nombre (str): El nombre del identificador.
            tipo_dato (str): El tipo de dato del símbolo (ej: 'int', 'string', 'function').
            rol (str): El papel del símbolo (ej: 'variable', 'constante', 'funcion').
            valor: El valor del símbolo (si es una constante o para simulación).
            inicializado (bool): Si el símbolo ha sido inicializado.
            utilizado (bool): Si el símbolo ha sido utilizado.
            parametros (list): Lista de parámetros si es una función/procedimiento.
            tipo_retorno (str): Tipo de retorno si es una función.
            linea (int): Número de línea donde se declara el símbolo.
            columna (int): Número de columna donde se declara el símbolo.

        Returns:
            bool: True si el símbolo se agregó con éxito, False si ya existe en el alcance actual.
        """
        alcance_actual = self.alcances[-1]
        if nombre in alcance_actual:
            # Manejo de re-declaración. Dependiendo del lenguaje, esto podría
            # ser un error semántico que se reporte más tarde.
            # Por ahora, simplemente no lo agregamos y podríamos imprimir una advertencia.
            print(f"Advertencia/Error de Tabla de Símbolos: El símbolo '{nombre}' ya está declarado en el alcance actual (línea: {linea}).")
            # Podríamos añadir información del símbolo existente para más claridad.
            return False
        
        alcance_actual[nombre] = {
            'nombre': nombre, # Guardamos el nombre también para facilitar la recuperación
            'tipo_dato': tipo_dato,
            'rol': rol,
            'valor': valor,
            'inicializado': inicializado,
            'utilizado': utilizado,
            'parametros': parametros if parametros is not None else [],
            'tipo_retorno': tipo_retorno,
            'linea_declaracion': linea,
            'columna_declaracion': columna,
            'alcance_nivel': len(self.alcances) -1 # Nivel de anidamiento del alcance
        }
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