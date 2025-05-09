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