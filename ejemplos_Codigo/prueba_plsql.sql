-- -- Ejemplo de bloque PL/SQL
-- DECLARE
--   v_nombre VARCHAR2(50) := 'Mundo';
--   v_contador NUMBER := 0;
-- BEGIN
--   DBMS_OUTPUT.PUT_LINE('Hola ' || v_nombre || ' desde PL/SQL!'); -- Concatenación

--   LOOP
--     v_contador := v_contador + 1;
--     DBMS_OUTPUT.PUT_LINE('Contador: ' || TO_CHAR(v_contador));
--     EXIT WHEN v_contador >= 3;
--   END LOOP;

--   IF v_contador = 3 THEN
--     DBMS_OUTPUT.PUT_LINE('El bucle se ejecutó 3 veces.');
--   END IF;

--   -- Esto es un comentario de una línea
--   /* Esto es un
--     comentario de bloque.
--   */
-- EXCEPTION
--   WHEN OTHERS THEN
--     DBMS_OUTPUT.PUT_LINE('Ocurrió un error: ' || SQLERRM);
-- END;
-- / 
-- -- Otro bloque anónimo o sentencia SQL podría ir aquí
-- SELECT * FROM DUAL;

-- -- Ejemplo de bloque PL/SQL
-- DECLARE
--   v_nombre VARCHAR2(50) := 'Mundo';
--   v_contador NUMBER := 0;
--   v_resultado_loop VARCHAR2(200) := '';
--   v_resultado_for VARCHAR2(200) := '';
-- BEGIN
--   DBMS_OUTPUT.PUT_LINE('Hola ' || v_nombre || ' desde PL/SQL!'); -- Concatenación

--   LOOP
--     v_contador := v_contador + 1;
--     v_resultado_loop := v_resultado_loop || 'Iteracion LOOP: ' || TO_CHAR(v_contador) || CHR(10);
--     EXIT WHEN v_contador >= 3;
--   END LOOP;
--   DBMS_OUTPUT.PUT_LINE(v_resultado_loop);
--   DBMS_OUTPUT.PUT_LINE('Bucle LOOP finalizado. Contador: ' || TO_CHAR(v_contador));

--   IF v_contador = 3 THEN
--     DBMS_OUTPUT.PUT_LINE('El bucle LOOP se ejecutó 3 veces.');
--   END IF;

--   -- Nuevo bucle FOR
--   DBMS_OUTPUT.PUT_LINE('Iniciando bucle FOR...');
--   FOR i IN 1..3 LOOP
--     v_resultado_for := v_resultado_for || 'Iteracion FOR: ' || TO_CHAR(i) || CHR(10);
--   END LOOP;
--   DBMS_OUTPUT.PUT_LINE(v_resultado_for);
--   DBMS_OUTPUT.PUT_LINE('Bucle FOR finalizado.');

-- EXCEPTION
--   WHEN OTHERS THEN
--     DBMS_OUTPUT.PUT_LINE('Ocurrió un error: ' || SQLERRM);
-- END;
-- / 
-- SELECT * FROM DUAL;

-- Prueba de FOR LOOP, SYSDATE, NVL, CHR, manejo de excepciones y RAISE
DECLARE
  v_sum NUMBER := 0;
  v_text VARCHAR2(100);
  v_null_val VARCHAR2(10);
  v_result VARCHAR2(100);
  v_char CHAR(1);
  v_fecha VARCHAR2(30);
BEGIN
  -- FOR LOOP normal
  FOR i IN 1..5 LOOP
    v_sum := v_sum + i;
  END LOOP;
  DBMS_OUTPUT.PUT_LINE('Suma del 1 al 5 (FOR): ' || TO_CHAR(v_sum));

  -- FOR LOOP REVERSE
  v_sum := 0;
  FOR i IN REVERSE 1..3 LOOP
    v_sum := v_sum + i;
  END LOOP;
  DBMS_OUTPUT.PUT_LINE('Suma REVERSE 3 a 1 (FOR): ' || TO_CHAR(v_sum));

  -- SYSDATE
  v_fecha := SYSDATE;
  DBMS_OUTPUT.PUT_LINE('Fecha actual (SYSDATE): ' || v_fecha);

  -- NVL
  v_result := NVL(v_null_val, 'Valor por defecto');
  DBMS_OUTPUT.PUT_LINE('Resultado NVL: ' || v_result);

  -- CHR
  v_char := CHR(65);
  DBMS_OUTPUT.PUT_LINE('CHR(65): ' || v_char);

  -- Manejo de excepciones por nombre y RAISE
  BEGIN
    RAISE_APPLICATION_ERROR(-20001, 'Error personalizado de prueba');
  EXCEPTION
    WHEN OTHERS THEN
      DBMS_OUTPUT.PUT_LINE('Excepción capturada (OTHERS): ' || SQLERRM);
  END;

  BEGIN
    RAISE;
  EXCEPTION
    WHEN OTHERS THEN
      DBMS_OUTPUT.PUT_LINE('Excepción capturada (RAISE): ' || SQLERRM);
  END;

END;
/