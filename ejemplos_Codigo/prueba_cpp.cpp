// // Ejemplo de Script C++
// #include <iostream>
// #include "mi_cabecera.h" // Cabecera de usuario

// /*
//   Comentario de bloque
//   para C++.
// */

// namespace MyNamespace {
//     class MiClase {
//     public:
//         int miMetodo(char param) {
//             return 0;
//         }
//     };
// }

// int main() {
//     std::cout << "Hola desde C++!" << std::endl;
//     int numero = 123;
//     float flotante = 3.14f;
//     char caracter = 'a';
//     // Directiva ifdef
//     #ifdef DEBUG
//         std::cout << "Modo DEBUG activado." << std::endl;
//     #endif
//     return 0;
// }

// Ejemplo de Script C++
#include <iostream>
#include "mi_cabecera.h" // Cabecera de usuario

/*
  Comentario de bloque
  para C++.
*/

using namespace std; // Directiva using

namespace MyNamespace {
    class MiClase {
    public:
        int miMetodo(char param) {
            // Cuerpo de método con if
            if (param == 'a') {
                cout << "Param es 'a'" << endl;
                return 1;
            } else {
                cout << "Param no es 'a'" << endl;
                return 0;
            }
        }
    }; // Fin de MiClase
} // Fin de MyNamespace

int main() {
    std::cout << "Hola desde C++!" << std::endl;
    int numero = 123 + (45 * 2); 
    float flotante = 3.14f;
    char caracter = 'a';
    bool condicion = true;

    if (numero > 200) {
        std::cout << "Numero es mayor que 200." << std::endl;
    }

    if (caracter == 'b') {
        std::cout << "Caracter es 'b'." << std::endl;
    } else {
        std::cout << "Caracter no es 'b', es: " << caracter << std::endl;
    }

    // Directiva ifdef
    #ifdef DEBUG
        std::cout << "Modo DEBUG activado." << std::endl;
    #endif
    
    MyNamespace::MiClase instanciaClase;
    instanciaClase.miMetodo('x');

    return 0;
}
