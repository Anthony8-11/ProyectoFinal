# src/main.py
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os

# Para que la importación funcione correctamente cuando ejecutamos main.py desde el directorio src/
# o cuando src/ es parte de PYTHONPATH, necesitamos asegurarnos de que Python
# pueda encontrar el paquete detector_lenguaje.
# Si ejecutas desde simulador_compilador/ usando `python -m src.main`,
# las importaciones relativas como `from .detector_lenguaje...` deberían funcionar.
# Si ejecutas directamente src/main.py, Python podría no reconocer 'src' como paquete
# a menos que el directorio padre ('simulador_compilador') esté en sys.path.
# Una forma robusta es ajustar sys.path si es necesario, o estructurar las llamadas.

# Asumiendo que ejecutamos desde el directorio 'simulador_compilador/' con `python src/main.py`
# o que el IDE maneja bien la raíz del proyecto.
try:
    from detector_lenguaje.detector import detectar_lenguaje
    # Lexer para Python
    from analizador_lexico.lexer_python import LexerPython 
    from analizador_lexico.lexer_python import TT_ERROR_LEXICO as TT_ERROR_PYTHON, TT_EOF as TT_EOF_PYTHON 
    
    # Importaciones para el Lexer de HTML
    from analizador_lexico.lexer_html import LexerHTML
    # Aquí es donde necesitas importar las constantes:
    from analizador_lexico.lexer_html import Token as TokenHTML # Si la redefiniste o para claridad
    from analizador_lexico.lexer_html import TT_ERROR_HTML, TT_EOF_HTML 

    # Añadir la nueva importación para el lexer de Pascal
    from analizador_lexico.lexer_pascal import LexerPascal
    # Asumimos que la clase Token es la misma o LexerPascal usa su propia definición interna
    # y que TT_ERROR_PASCAL y TT_EOF_PASCAL están definidos en lexer_pascal.py
    from analizador_lexico.lexer_pascal import TT_ERROR_PASCAL, TT_EOF_PASCAL

    # Parser para Pascal (NUEVA IMPORTACIÓN)
    from analizador_sintactico.parser_pascal import ParserPascal
except ImportError:

    # Este bloque es para ayudar si la ejecución directa de src/main.py causa problemas de importación
    # y el directorio 'simulador_compilador' no está en PYTHONPATH.
    import sys
    # Añadir el directorio padre (simulador_compilador) al path para encontrar 'detector_lenguaje'
    # sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    # from detector_lenguaje.detector import detectar_lenguaje
    # La línea anterior es un poco riesgosa si la estructura cambia.
    # Es mejor ejecutar como módulo: python -m src.main desde simulador_compilador/
    print("Error: No se pudo importar 'detectar_lenguaje'.")
    print("Asegúrate de ejecutar desde el directorio raíz 'simulador_compilador/' usando 'python -m src.main'")
    print("o que tu PYTHONPATH esté configurado correctamente.")
    sys.exit(1)


def analizar_archivo_y_mostrar(ruta_archivo):
    """
    Lee un archivo, detecta su lenguaje y muestra los resultados.
    """
    try:
        # Usar 'errors='ignore'' puede ocultar problemas de codificación,
        # pero es práctico para una prueba rápida con diversos archivos.
        # Para producción, sería mejor manejar las codificaciones explícitamente.
        with open(ruta_archivo, 'r', encoding='utf-8', errors='ignore') as f:
            lineas_codigo = f.readlines() 
        
        if not lineas_codigo and os.path.getsize(ruta_archivo) == 0: # Archivo realmente vacío
            print(f"\n--- Analizando archivo: {os.path.basename(ruta_archivo)} ---")
            print("Resultado: El archivo está vacío.")
            print("--------------------------------------")
            return
        elif not lineas_codigo and os.path.getsize(ruta_archivo) > 0: # Archivo con contenido no decodificable o solo BOM
             print(f"\n--- Analizando archivo: {os.path.basename(ruta_archivo)} ---")
             print("Resultado: El archivo tiene contenido pero no se pudieron leer líneas (posible problema de codificación o solo BOM).")
             print("--------------------------------------")
             # Intentar leer como bytes y pasar a detectar_lenguaje para ver si puede manejarlo
             with open(ruta_archivo, 'rb') as bf:
                 bytes_content = bf.read().decode('utf-8', errors='replace') # Reemplazar errores
             lineas_codigo = bytes_content.splitlines()
             if not any(line.strip() for line in lineas_codigo): # Si después de reemplazar, sigue sin contenido útil
                 return


        print(f"\n--- Analizando archivo: {os.path.basename(ruta_archivo)} ---")
        # Enviamos todas las líneas, la función detectar_lenguaje tomará una muestra
        lenguaje_detectado, confianza, pistas_debug = detectar_lenguaje(lineas_codigo)
        
        print(f"Lenguaje Detectado: {lenguaje_detectado}")
        print(f"Confianza         : {confianza:.2f}%")

        if lenguaje_detectado == "Python":
            print("\n--- Análisis Léxico (Python) ---")
            # Unir las líneas de código en una sola cadena si el lexer espera eso
            # (Nuestro LexerPython espera una cadena completa)
            codigo_completo_str = "".join(lineas_codigo)
            
            if not codigo_completo_str.strip() and not (lenguaje_detectado == "Python" and len(lineas_codigo) > 0 and all(not line.strip() for line in lineas_codigo)):
                print("El código Python está vacío o solo contiene espacios/saltos de línea.")
            else:
                try:
                    lexer_py = LexerPython(codigo_completo_str)
                    tokens_obtenidos = lexer_py.tokenizar()
                    
                    print(f"Total de tokens generados (Python): {len(tokens_obtenidos)}")
                    tiene_errores_lexicos = False
                    for i, token_obj in enumerate(tokens_obtenidos):
                        # Usamos el __repr__ de la clase Token que definimos
                        print(f"  {i+1:03d}: {token_obj}") 
                        if token_obj.tipo == 'ERROR_LEXICO': # Usar la constante TT_ERROR_LEXICO sería mejor
                            tiene_errores_lexicos = True
                    
                    if tiene_errores_lexicos:
                        print(">>> Se encontraron errores léxicos en el código Python. <<<")
                    elif tokens_obtenidos and tokens_obtenidos[-1].tipo == 'EOF': # Usar TT_EOF
                        print(">>> Análisis léxico de Python completado sin errores aparentes (finalizado con EOF). <<<")
                    else:
                        print(">>> Análisis léxico de Python finalizado (verificar si falta EOF o hay otros problemas). <<<")

                except Exception as e_lex:
                    print(f"ERROR durante el análisis léxico de Python: {e_lex}")
                    import traceback
                    traceback.print_exc()
            print("--- Fin Análisis Léxico (Python) ---")

        elif lenguaje_detectado == "HTML":
                print("\n--- Análisis Léxico (HTML) ---")
                codigo_completo_str = "".join(lineas_codigo)

                if not codigo_completo_str.strip():
                    print("El código HTML para el análisis léxico está vacío o solo contiene espacios/saltos de línea.")
                else:
                    try:
                        lexer_ht = LexerHTML(codigo_completo_str)
                        tokens_obtenidos = lexer_ht.tokenizar() # Usar el método tokenizar con la máquina de estados
                        
                        print(f"Total de tokens generados (HTML): {len(tokens_obtenidos)}")
                        tiene_errores_lexicos_html = False
                        for i, token_obj in enumerate(tokens_obtenidos):
                            # Asumimos que la clase Token (o TokenHTML) tiene un __repr__ adecuado
                            print(f"  {i+1:03d}: {token_obj}") 
                            if token_obj.tipo == TT_ERROR_HTML: # Usar la constante importada
                                tiene_errores_lexicos_html = True
                        
                        if tiene_errores_lexicos_html:
                            print(">>> Se encontraron errores léxicos en el código HTML. <<<")
                        elif tokens_obtenidos and tokens_obtenidos[-1].tipo == TT_EOF_HTML: # Usar la constante importada
                            print(">>> Análisis léxico de HTML completado sin errores aparentes (finalizado con EOF). <<<")
                        elif not tokens_obtenidos:
                             print(">>> No se generaron tokens HTML (posiblemente código vacío). <<<")
                        else:
                            print(f">>> Análisis léxico de HTML finalizado, pero el último token no es EOF (último: {tokens_obtenidos[-1].tipo if tokens_obtenidos else 'N/A'}). <<<")

                    except Exception as e_lex_html:
                        print(f"ERROR SEVERO durante el análisis léxico de HTML: {e_lex_html}")
                        import traceback
                        traceback.print_exc()
                print("--- Fin Análisis Léxico (HTML) ---")

        elif lenguaje_detectado == "Pascal":
                print("\n--- Análisis Léxico (Pascal) ---")
                codigo_completo_str = "".join(lineas_codigo)

                if not codigo_completo_str.strip():
                    print("El código Pascal para el análisis léxico está vacío o solo contiene espacios/saltos de línea.")
                else:
                    try:
                        # --- Inicio del Análisis Léxico de Pascal (como estaba antes) ---
                        lexer_pas = LexerPascal(codigo_completo_str)
                        tokens_obtenidos = lexer_pas.tokenizar()
                        
                        print(f"Total de tokens generados (Pascal): {len(tokens_obtenidos)}")
                        tiene_errores_lexicos_pascal = False
                        for i, token_obj in enumerate(tokens_obtenidos):
                            print(f"  {i+1:03d}: {token_obj}") 
                            if token_obj.tipo == TT_ERROR_PASCAL:
                                tiene_errores_lexicos_pascal = True
                        
                        mensaje_lexico = ""
                        if tiene_errores_lexicos_pascal:
                            mensaje_lexico = ">>> Se encontraron errores léxicos en el código Pascal. <<<"
                        elif tokens_obtenidos and tokens_obtenidos[-1].tipo == TT_EOF_PASCAL:
                            mensaje_lexico = ">>> Análisis léxico de Pascal completado sin errores aparentes (finalizado con EOF). <<<"
                        elif not tokens_obtenidos:
                             mensaje_lexico = ">>> No se generaron tokens Pascal (posiblemente código vacío o solo comentarios/espacios). <<<"
                        else:
                            mensaje_lexico = f">>> Análisis léxico de Pascal finalizado, pero el último token no es EOF (último: {tokens_obtenidos[-1].tipo if tokens_obtenidos else 'N/A'}). <<<"
                        print(mensaje_lexico)
                        # --- Fin del Análisis Léxico de Pascal ---

                        # --- INICIO DEL BLOQUE DE ANÁLISIS SINTÁCTICO PARA PASCAL ---
                        # Solo intentar el análisis sintáctico si el léxico fue exitoso (sin errores y con EOF)
                        if not tiene_errores_lexicos_pascal and \
                           tokens_obtenidos and \
                           tokens_obtenidos[-1].tipo == TT_EOF_PASCAL:
                            
                            print("\n--- Análisis Sintáctico (Pascal) ---")
                            try:
                                # Se crea una instancia del parser con la lista de tokens (ya filtrada de whitespace por el ParserPascal en su __init__)
                                parser_pas = ParserPascal(tokens_obtenidos) 
                                # El método parse() internamente llamará a _error_sintactico que lanza SyntaxError
                                # y también imprime mensajes de éxito o fallo.
                                resultado_parseo_exitoso = parser_pas.parse() 
                                
                                # El método parse() ya debería haber impreso si fue exitoso o los errores.
                                # Aquí solo confirmamos que el proceso de llamada al parser terminó.
                                # if resultado_parseo_exitoso:
                                # print("El parser de Pascal finalizó su ejecución (ver mensajes anteriores para el resultado).")
                                # else:
                                # print("El parser de Pascal finalizó su ejecución con errores (ver mensajes anteriores).")

                            except Exception as e_parse_pascal:
                                # Captura errores inesperados dentro de la lógica del parser,
                                # no errores sintácticos del código fuente (esos los maneja _error_sintactico).
                                print(f"ERROR CRÍTICO en la ejecución del Parser de Pascal: {e_parse_pascal}")
                                import traceback
                                traceback.print_exc()
                        elif tiene_errores_lexicos_pascal:
                            print("\n--- Análisis Sintáctico (Pascal) ---")
                            print("No se realizó el análisis sintáctico debido a errores léxicos previos.")
                        else: # No hay tokens o no terminó en EOF
                            print("\n--- Análisis Sintáctico (Pascal) ---")
                            print("No se realizó el análisis sintáctico (problema con la lista de tokens del lexer).")
                        print("--- Fin Análisis Sintáctico (Pascal) ---")
                        # --- FIN DEL BLOQUE DE ANÁLISIS SINTÁCTICO ---

                    except Exception as e_lex_pascal:
                        # Este error es del lexer
                        print(f"ERROR SEVERO durante el análisis léxico de Pascal: {e_lex_pascal}")
                        import traceback
                        traceback.print_exc()
                print("--- Fin Análisis Léxico (Pascal) ---")
        
        # Opcional: Mostrar las pistas activadas para depuración
        # print("Pistas activadas (debug):")
        # for lang_key, p_list in pistas_debug.items():
        #     if p_list and (lenguaje_detectado.startswith(lang_key) or "Desconocido" in lenguaje_detectado):
        #         print(f"  Para '{lang_key}':")
        #         for pista_info in p_list:
        #             print(f"    - {pista_info}")
        # if "REFINAMIENTO_GLOBAL" in pistas_debug and pistas_debug["REFINAMIENTO_GLOBAL"]:
        #     print(f"  Refinamientos Globales:")
        #     for pista_info in pistas_debug["REFINAMIENTO_GLOBAL"]:
        #         print(f"    - {pista_info}")

        print("--------------------------------------")

    except FileNotFoundError:
        print(f"Error: El archivo '{ruta_archivo}' no fue encontrado.")
    except Exception as e:
        print(f"Ocurrió un error al procesar el archivo '{os.path.basename(ruta_archivo)}': {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Iniciando Simulador de Compilador - Prueba del Detector de Lenguaje")
    print("Fecha y Hora Actual:", "[[CURRENT_DATETIME_CST_GUATEMALA]]") # Placeholder para la fecha actual

    # Directorio donde se crearán/buscarán los archivos de ejemplo
    # Asumimos que main.py está en src/, y ejemplos_codigo/ está al mismo nivel que src/
    directorio_base_proyecto = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    directorio_ejemplos = os.path.join(directorio_base_proyecto, "ejemplos_codigo")

    if not os.path.exists(directorio_ejemplos):
        print(f"Creando directorio de ejemplos en: {directorio_ejemplos}")
        os.makedirs(directorio_ejemplos)

    # Definición de archivos de prueba y su contenido
    # (Estos son los mismos que te mostré antes, pero ahora los crearemos si no existen)
    archivos_de_prueba_contenido = {
        "prueba_python.py": """
def saludar(nombre):
    # Esto es un comentario
    mensaje = "Hola, " + nombre + "!" # Concatenación
    print(f"Mensaje: {mensaje}")
    if 10 > 5 and True:
        x = 20.5 * 2
        print(f"Valor de x: {x}")
    return mensaje
saludar("Mundo")
class MiClase:
    pass
        """,
        "prueba_html.html": """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Mi Página de Prueba</title>
    <style> body { font-family: Arial, sans-serif; } </style>
</head>
<body>
    <h1>Hola Mundo Web</h1>
    <p>Este es un párrafo de prueba con <a href="#">un enlace</a>.</p>
    <!-- Comentario HTML -->
    <script>
        // Comentario JS
        console.log("JavaScript embebido en HTML");
        function test() { return 1+1; }
    </script>
</body>
</html>
        """,
        "prueba_cpp.cpp": """
#include <iostream>
#include <vector>
#include <string>

// Clase de ejemplo simple
class MiClaseCpp {
public:
    int datoMiembro;
    MiClaseCpp(int d) : datoMiembro(d) {}
    void mostrarDato() {
        std::cout << "El dato es: " << datoMiembro << std::endl;
    }
};

int main(int argc, char *argv[]) {
    std::cout << "¡Hola desde C++ en el simulador!" << std::endl;
    for (int i = 0; i < 3; ++i) {
        // Un bucle simple
    }
    MiClaseCpp objeto(123);
    objeto.mostrarDato();
    /* Comentario
       multilínea C++ */
    return 0;
}
        """,
        "prueba_pascal.pas": """
program SaludoCordialPascal;
uses Crt; (* Libreria para manejo de pantalla *)

var
   nombreUsuario : string[50];
   edad : integer;
   confirmacion : char;

begin
   clrscr; (* Limpiar pantalla *)
   writeln('Bienvenido al Sistema de Prueba Pascal.');
   write('Por favor, ingrese su nombre: ');
   readln(nombreUsuario);
   write('Ingrese su edad: ');
   readln(edad);

   { Este es un comentario de bloque en Pascal }
   if edad >= 18 then
      writeln('Hola ', nombreUsuario, ', usted es mayor de edad.')
   else
      writeln('Hola ', nombreUsuario, ', usted es menor de edad.');

   write('¿Desea continuar? (S/N): ');
   readln(confirmacion);
   (* Otro comentario *)
   writeln('Presione cualquier tecla para finalizar...');
   readkey; (* Esperar una tecla *)
end.
        """,
        "prueba_plsql.sql": """
-- Bloque PL/SQL de ejemplo
DECLARE
  v_nombre_empleado VARCHAR2(100) := 'Juan Perez';
  v_salario_actual NUMBER := 60000;
  V_FECHA_ALTA DATE;
  v_aumento_pct NUMBER := 0.05; -- 5% de aumento
BEGIN
  v_salario_actual := v_salario_actual * (1 + v_aumento_pct); 
  DBMS_OUTPUT.PUT_LINE('Empleado: ' || v_nombre_empleado);
  DBMS_OUTPUT.PUT_LINE('Salario Actualizado: ' || TO_CHAR(v_salario_actual, 'L999G999D99'));

  SELECT SYSDATE INTO V_FECHA_ALTA FROM DUAL;
  DBMS_OUTPUT.PUT_LINE('Fecha de Proceso: ' || TO_CHAR(V_FECHA_ALTA, 'DD-MON-YYYY HH24:MI:SS'));
  
  /* Ejemplo de un bucle simple
     FOR i IN 1..3 LOOP
       DBMS_OUTPUT.PUT_LINE('Iteración: ' || i);
     END LOOP;
  */
EXCEPTION
  WHEN NO_DATA_FOUND THEN
    DBMS_OUTPUT.PUT_LINE('Error: No se encontraron datos.');
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('Ocurrió un error inesperado: ' || SQLERRM);
END;
/
-- Sentencia SQL adicional fuera del bloque PL/SQL
SELECT * FROM DUAL;
        """,
        "prueba_tsql.sql": """
-- Script de T-SQL de ejemplo
PRINT 'Iniciando script de prueba para T-SQL';
GO

DECLARE @NombreCliente VARCHAR(100), @CiudadCliente VARCHAR(50);
DECLARE @TotalPedidos INT;

SET @NombreCliente = 'Cliente Ejemplo S.A.';
SET @CiudadCliente = 'Ciudad Gótica';
SET @TotalPedidos = 0;

IF EXISTS (SELECT 1 FROM sys.tables WHERE name = 'PedidosSimulados')
BEGIN
    PRINT 'La tabla PedidosSimulados ya existe.';
    SELECT @TotalPedidos = COUNT(*) FROM PedidosSimulados WHERE Cliente = @NombreCliente;
END
ELSE
BEGIN
    PRINT 'La tabla PedidosSimulados no existe. Creándola...';
    /*
    CREATE TABLE PedidosSimulados (
        PedidoID INT PRIMARY KEY IDENTITY(1,1),
        Cliente VARCHAR(100),
        FechaPedido DATETIME DEFAULT GETDATE(),
        Monto DECIMAL(10,2)
    );
    INSERT INTO PedidosSimulados (Cliente, Monto) VALUES (@NombreCliente, 150.75);
    SET @TotalPedidos = 1;
    */
    PRINT 'Tabla PedidosSimulados creada (simulado).';
END

PRINT 'Cliente: ' + @NombreCliente + ' de ' + @CiudadCliente;
PRINT 'Total de pedidos encontrados: ' + CAST(@TotalPedidos AS VARCHAR(10));
GO

SELECT @@VERSION AS VersionSQLServer;
        """,
        "prueba_javascript.js": """
// Comentario de una línea en JavaScript
/*
  Comentario multilínea
  en JavaScript.
*/
function calcularTotal(precio, cantidad) {
    let subtotal = precio * cantidad; // Cálculo simple
    const impuesto = 0.12; // 12% de impuesto
    let totalConImpuesto = subtotal * (1 + impuesto);
    return totalConImpuesto.toFixed(2); // Redondear a 2 decimales
}

var producto = "Laptop";
let precioUnitario = 750.99;
const cantidadComprada = 2;

let totalFactura = calcularTotal(precioUnitario, cantidadComprada);

console.log(`Producto: ${producto}`);
console.log(`Precio Unitario: $${precioUnitario}`);
console.log(`Cantidad: ${cantidadComprada}`);
console.log(`Total a Pagar: $${totalFactura}`);

if (cantidadComprada > 1) {
    document.getElementById("mensaje").innerHTML = "¡Gracias por comprar múltiples unidades!";
}

// Ejemplo de clase en ES6
class Usuario {
    constructor(nombre, email) {
        this.nombre = nombre;
        this.email = email;
    }

    presentarse() {
        console.log(`Hola, soy ${this.nombre} y mi email es ${this.email}.`);
    }
}
const user1 = new Usuario("Ana", "ana@example.com");
user1.presentarse();
async function obtenerDatos() { return "datos"; }
        """,
        "prueba_vacia.txt": """
""",
        "prueba_solo_espacios.txt": """
        
          
            
        """
    }

    # Crear o sobrescribir los archivos de ejemplo
    for nombre_archivo, contenido_archivo in archivos_de_prueba_contenido.items():
        ruta_completa_archivo = os.path.join(directorio_ejemplos, nombre_archivo)
        try:
            with open(ruta_completa_archivo, 'w', encoding='utf-8') as f_ej:
                f_ej.write(contenido_archivo.strip()) # strip() para quitar espacios/saltos al inicio/final del contenido
            print(f"Archivo de ejemplo '{nombre_archivo}' creado/actualizado.")
        except Exception as e_create:
            print(f"Error creando archivo de ejemplo '{nombre_archivo}': {e_create}")

    print("\n=== Iniciando análisis de archivos de ejemplo ===")
    # Analizar cada archivo de ejemplo
    for nombre_archivo in archivos_de_prueba_contenido.keys():
        ruta_completa_archivo = os.path.join(directorio_ejemplos, nombre_archivo)
        if os.path.exists(ruta_completa_archivo): # Solo analizar si el archivo realmente existe
            analizar_archivo_y_mostrar(ruta_completa_archivo)
        else:
            print(f"Advertencia: El archivo de ejemplo '{ruta_completa_archivo}' no se encontró para el análisis.")

    print("\n=== Prueba con entrada de texto directa ===")
    codigo_directo_html = "<!DOCTYPE html>\n<html><head><title>Test</title></head><body><h1>Test Directo</h1></body></html>"
    print(f"\n--- Analizando código directo (HTML) ---")
    lenguaje_html, confianza_html, _ = detectar_lenguaje(codigo_directo_html)
    print(f"Lenguaje Detectado: {lenguaje_html}")
    print(f"Confianza         : {confianza_html:.2f}%")
    print("--------------------------------------")
    
    codigo_directo_python = "def mi_funcion_directa(a, b):\n  resultado = a + b # Suma simple\n  return resultado\nprint(mi_funcion_directa(5,3))"
    print(f"\n--- Analizando código directo (Python) ---")
    lenguaje_py, confianza_py, _ = detectar_lenguaje(codigo_directo_python)
    print(f"Lenguaje Detectado: {lenguaje_py}")
    print(f"Confianza         : {confianza_py:.2f}%")
    print("--------------------------------------")

    codigo_muy_corto_ambiguo = "x = 10;"
    print(f"\n--- Analizando código directo (Corto y Ambiguo) ---")
    lenguaje_amb, confianza_amb, _ = detectar_lenguaje(codigo_muy_corto_ambiguo)
    print(f"Lenguaje Detectado: {lenguaje_amb}")
    print(f"Confianza         : {confianza_amb:.2f}%")
    print("--------------------------------------")

    print("\nPrueba del Detector de Lenguaje Finalizada.")