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