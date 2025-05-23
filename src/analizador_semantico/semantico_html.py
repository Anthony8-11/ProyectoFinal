# src/analizador_semantico/semantico_html.py
"""
Analizador semántico para HTML: verifica estructura, anidamiento, unicidad de atributos, cierre de etiquetas, y advertencias comunes.
Reconoce todos los nodos implementados en el lexer y parser actuales.
"""
try:
    from analizador_sintactico.parser_html import (
        NodoDocumentoHTML, NodoEtiquetaHTML, NodoAtributoHTML, NodoTextoHTML, NodoComentarioHTML, NodoDoctypeHTML
    )
    from analizador_lexico.lexer_html import Token
except ImportError as e:
    print(f"Error de importación en semantico_html.py: {e}")
    class NodoDocumentoHTML: pass
    class NodoEtiquetaHTML: pass
    class NodoAtributoHTML: pass
    class NodoTextoHTML: pass
    class NodoComentarioHTML: pass
    class NodoDoctypeHTML: pass
    class Token: pass

class AnalizadorSemanticoHTML:
    def __init__(self):
        self.errores = []
        self.pila_etiquetas = []
        self.etiquetas_autocierre = set([
            'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'
        ])

    def _registrar_error(self, mensaje, nodo=None):
        linea = getattr(nodo, 'linea', 'desconocida')
        columna = getattr(nodo, 'columna', 'desconocida')
        if hasattr(nodo, 'nombre_token'):
            linea = getattr(nodo.nombre_token, 'linea', linea)
            columna = getattr(nodo.nombre_token, 'columna', columna)
        elif hasattr(nodo, 'comentario_token'):
            linea = getattr(nodo.comentario_token, 'linea', linea)
            columna = getattr(nodo.comentario_token, 'columna', columna)
        elif hasattr(nodo, 'texto_token'):
            linea = getattr(nodo.texto_token, 'linea', linea)
            columna = getattr(nodo.texto_token, 'columna', columna)
        self.errores.append(f"Error Semántico (HTML) en L{linea}:C{columna}: {mensaje}")
        print(self.errores[-1])

    def analizar(self, nodo_raiz):
        self.errores = []
        try:
            self._visitar(nodo_raiz)
        except Exception as e:
            self._registrar_error(f"Error inesperado durante el análisis semántico: {e}")
            import traceback; traceback.print_exc()
        if not self.errores:
            print("Análisis semántico de HTML completado sin errores.")
        else:
            print(f"Análisis semántico de HTML completado con {len(self.errores)} error(es).")
        return not self.errores

    def _visitar(self, nodo):
        if isinstance(nodo, NodoDocumentoHTML):
            for hijo in nodo.hijos:
                self._visitar(hijo)
        elif isinstance(nodo, NodoEtiquetaHTML):
            self._verificar_etiqueta(nodo)
        elif isinstance(nodo, NodoAtributoHTML):
            self._verificar_atributo(nodo)
        elif isinstance(nodo, NodoTextoHTML):
            self._verificar_texto(nodo)
        elif isinstance(nodo, NodoComentarioHTML):
            pass # Comentarios no requieren verificación semántica
        elif isinstance(nodo, NodoDoctypeHTML):
            self._verificar_doctype(nodo)

    def _verificar_etiqueta(self, nodo):
        nombre = nodo.nombre_etiqueta.lower() if hasattr(nodo, 'nombre_etiqueta') else ''
        if not nombre:
            self._registrar_error("Etiqueta sin nombre.", nodo)
            return
        # Verificar unicidad de atributos
        nombres_atributos = set()
        for atributo in getattr(nodo, 'atributos', []):
            if atributo.nombre_token.lexema in nombres_atributos:
                self._registrar_error(f"Atributo duplicado '{atributo.nombre_token.lexema}' en <{nombre}>.", atributo)
            else:
                nombres_atributos.add(atributo.nombre_token.lexema)
            self._visitar(atributo)
        # Verificar hijos
        if not nodo.es_autocierre and nombre not in self.etiquetas_autocierre:
            self.pila_etiquetas.append(nombre)
            for hijo in getattr(nodo, 'hijos', []):
                self._visitar(hijo)
            etiqueta_cerrada = self.pila_etiquetas.pop() if self.pila_etiquetas else None
            if etiqueta_cerrada != nombre:
                self._registrar_error(f"Etiqueta <{nombre}> no cerrada correctamente.", nodo)
        elif nodo.es_autocierre and nombre not in self.etiquetas_autocierre:
            self._registrar_error(f"Etiqueta <{nombre}/> no es autocerrable según HTML estándar.", nodo)

    def _verificar_atributo(self, nodo):
        if nodo.valor_token is None:
            self._registrar_error(f"Atributo '{nodo.nombre_token.lexema}' sin valor explícito.", nodo)

    def _verificar_texto(self, nodo):
        # Opcional: advertir sobre texto fuera de <body> o <html>
        if not nodo.contenido.strip():
            self._registrar_error("Texto vacío o solo espacios en HTML.", nodo)

    def _verificar_doctype(self, nodo):
        if not nodo.contenido.lower().startswith('<!doctype'):
            self._registrar_error("Declaración DOCTYPE inválida.", nodo)

# Fin de AnalizadorSemanticoHTML
