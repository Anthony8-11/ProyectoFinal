// Ejemplo de Script C++
#include <iostream>
#include "mi_cabecera.h" // Cabecera de usuario

/*
  Comentario de bloque
  para C++.
*/

namespace MyNamespace {
    class MiClase {
    public:
        int miMetodo(char param) {
            return 0;
        }
    };
}

int main() {
    std::cout << "Hola desde C++!" << std::endl;
    int numero = 123;
    float flotante = 3.14f;
    char caracter = 'a';
    // Directiva ifdef
    #ifdef DEBUG
        std::cout << "Modo DEBUG activado." << std::endl;
    #endif
    return 0;
}