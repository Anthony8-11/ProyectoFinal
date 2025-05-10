program TestLogicos;
var
   a, b : integer;
   cond1, cond2, resultado_logico : boolean;
   entrada: char;
   contador: integer;
begin
   a := 10;
   b := 5;

   cond1 := (a > b) and (b > 0);          (* Verdadero and Verdadero -> Verdadero *)
   cond2 := (a < b) or not (b = 5);       (* Falso or not Verdadero -> Falso or Falso -> Falso *)
   resultado_logico := cond1 and not cond2; (* Verdadero and not Falso -> Verdadero and Verdadero -> Verdadero *)

   writeln('cond1 ( (a > b) and (b > 0) ): ', cond1);
   writeln('cond2 ( (a < b) or not (b = 5) ): ', cond2);
   writeln('resultado_logico ( cond1 and not cond2 ): ', resultado_logico);

   writeln('--- Prueba Repeat con OR y AND ---');
   contador := 0;
   repeat
      contador := contador + 1;
      writeln('Iteracion: ', contador);
      write('Continuar? (s/n): ');
      readln(entrada);
   until (contador >= 3) or ((entrada = 'n') and (contador > 0)); 
   (* El (contador > 0) es para asegurar que 'and' se evalúe con booleanos *)

end.