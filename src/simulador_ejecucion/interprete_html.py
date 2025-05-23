# src/simulador_ejecucion/interprete_html.py

# Importar los nodos AST del parser de HTML
try:
    from analizador_sintactico.parser_html import (
        NodoDocumentoHTML, NodoEtiquetaHTML, NodoAtributoHTML,
        NodoTextoHTML, NodoComentarioHTML, NodoDoctypeHTML
    )
except ImportError as e_ip_html:
    print(f"Error de importación en interprete_html.py: {e_ip_html}")
    # Placeholders si la importación falla
    class NodoDocumentoHTML: pass; 
    class NodoEtiquetaHTML: pass; 
    class NodoAtributoHTML: pass
    class NodoTextoHTML: pass; 
    class NodoComentarioHTML: pass; 
    class NodoDoctypeHTML: pass

class ErrorVisualizacionHTML(RuntimeError):
    """Error general durante la visualización de HTML."""
    pass

class VisualizadorHTML:
    def __init__(self):
        self.resultado_visualizacion = [] # Lista para acumular la salida
        self.nivel_indentacion_actual = 0

    def _indentar(self):
        return "  " * self.nivel_indentacion_actual

    def visualizar_documento(self, nodo_documento):
        if not isinstance(nodo_documento, NodoDocumentoHTML):
            print("Error del Visualizador HTML: Se esperaba un NodoDocumentoHTML.")
            return ""
        
        self.resultado_visualizacion = [] # Limpiar para nueva visualización
        self.nivel_indentacion_actual = 0
        print("\n--- Iniciando Visualización de Estructura HTML ---")
        
        try:
            self.visitar(nodo_documento)
        except ErrorVisualizacionHTML as e_vis:
            print(f"Error durante la visualización HTML: {e_vis}")
        except Exception as e_general:
            print(f"Error Inesperado durante la Visualización de HTML: {e_general}")
            import traceback
            traceback.print_exc()
        
        salida_final = "\n".join(self.resultado_visualizacion)
        print(salida_final)
        print("--- Fin de Visualización de Estructura HTML ---")
        return salida_final

    def visitar(self, nodo):
        """Método visitador genérico para nodos del AST HTML."""
        nombre_metodo_visitador = f'visitar_{type(nodo).__name__}'
        visitador = getattr(self, nombre_metodo_visitador, self._visitador_no_encontrado)
        # print(f"[VisualizadorHTML DEBUG] Visitando nodo: {type(nodo).__name__} con {nombre_metodo_visitador}")
        return visitador(nodo)

    def _visitador_no_encontrado(self, nodo):
        raise ErrorVisualizacionHTML(f"No hay método visitador_Nodo... para el tipo de nodo {type(nodo).__name__}")

    def visitar_NodoDocumentoHTML(self, nodo_doc):
        # print(f"[VisualizadorHTML DEBUG] Visitando NodoDocumentoHTML")
        for hijo in nodo_doc.hijos:
            self.visitar(hijo)

    def visitar_NodoEtiquetaHTML(self, nodo_etiqueta):
        indent = self._indentar()
        linea_salida = f"{indent}<{nodo_etiqueta.nombre_etiqueta}"
        
        if nodo_etiqueta.atributos:
            for attr_nodo in nodo_etiqueta.atributos:
                linea_salida += self.visitar_NodoAtributoHTML(attr_nodo) # visitar_NodoAtributoHTML devuelve el string del atributo
        
        if nodo_etiqueta.es_autocierre:
            linea_salida += " />"
            self.resultado_visualizacion.append(linea_salida)
        else:
            linea_salida += ">"
            self.resultado_visualizacion.append(linea_salida)
            
            self.nivel_indentacion_actual += 1
            for hijo_nodo in nodo_etiqueta.hijos:
                self.visitar(hijo_nodo)
            self.nivel_indentacion_actual -= 1
            
            self.resultado_visualizacion.append(f"{indent}</{nodo_etiqueta.nombre_etiqueta}>")

    def visitar_NodoAtributoHTML(self, nodo_atributo):
        # Este método devuelve el string del atributo para ser concatenado
        nombre_attr = nodo_atributo.nombre_token.lexema
        if nodo_atributo.valor_token:
            # El valor del token ya tiene las comillas quitadas por el lexer
            valor_attr = nodo_atributo.valor_token.valor 
            return f" {nombre_attr}=\"{valor_attr}\""
        else:
            return f" {nombre_attr}" # Atributo booleano

    def visitar_NodoTextoHTML(self, nodo_texto):
        indent = self._indentar()
        # Limpiar el texto de espacios/saltos de línea excesivos solo para la visualización
        contenido_limpio = " ".join(nodo_texto.contenido.strip().split())
        if contenido_limpio: # Solo añadir si hay texto visible
            self.resultado_visualizacion.append(f"{indent}{contenido_limpio}")

    def visitar_NodoComentarioHTML(self, nodo_comentario):
        indent = self._indentar()
        # El lexema del comentario ya incluye self.resultado_visualizacion.append(f"{indent}{nodo_comentario.contenido}")

    def visitar_NodoDoctypeHTML(self, nodo_doctype):
        # DOCTYPE usualmente no se indenta
        self.resultado_visualizacion.append(f"{nodo_doctype.contenido}")

# Fin de la clase VisualizadorHTML
