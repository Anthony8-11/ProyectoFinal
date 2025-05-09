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