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