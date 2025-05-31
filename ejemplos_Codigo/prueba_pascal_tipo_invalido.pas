program TestTipos;
var
   a : integer;
   b : string;
begin
   a := 5;
   b := 'hola';
   a := b;  { Esto debe causar error de tipo }
   writeln(a, b);
end.
