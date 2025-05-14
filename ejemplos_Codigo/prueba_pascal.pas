program TestBucles;
var
   contador : integer;
   limite : integer;
begin
   contador := 1;
   limite := 5;
   writeln('Iniciando bucle while:');
   
   while contador <= limite do
   begin
      write('Contador = ', contador);
      if contador mod 2 = 0 then
         writeln(' (par)')
      else
         writeln(' (impar)');
      contador := contador + 1;
   end;
   
   writeln('Bucle while finalizado.');
   writeln('Valor final del contador: ', contador);
end.