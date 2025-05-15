-- -- Script de Prueba T-SQL Completo

-- PRINT '--- Iniciando Script de Simulación T-SQL ---';
-- GO

-- PRINT 'Paso 1: Creando Tablas';
-- CREATE TABLE Empleados (
--     EmpleadoID INT PRIMARY KEY,
--     Nombre NVARCHAR(100) NOT NULL,
--     Apellido NVARCHAR(100),
--     DepartamentoID INT,
--     Salario DECIMAL(10, 2),
--     FechaContratacion DATETIME DEFAULT GETDATE()
-- );

-- CREATE TABLE Departamentos (
--     DepartamentoID INT PRIMARY KEY,
--     NombreDepartamento VARCHAR(100) NOT NULL
-- );
-- GO

-- PRINT 'Tablas creadas.';
-- GO

-- PRINT 'Paso 2: Insertando Datos en Departamentos';
-- INSERT INTO Departamentos (DepartamentoID, NombreDepartamento) VALUES (1, 'Ventas');
-- INSERT INTO Departamentos (DepartamentoID, NombreDepartamento) VALUES (2, 'TI');
-- INSERT INTO Departamentos (DepartamentoID, NombreDepartamento) VALUES (3, 'Recursos Humanos');
-- GO

-- PRINT 'Paso 3: Insertando Datos en Empleados';
-- INSERT INTO Empleados (EmpleadoID, Nombre, Apellido, DepartamentoID, Salario, FechaContratacion)
-- VALUES 
-- (1, 'Ana', 'Lopez', 1, 55000.00, '2023-01-10'),
-- (2, 'Luis', 'Marin', 2, 72000.00, '2022-11-05'),
-- (3, 'Sara', 'Connor', 1, 58500.00, '2023-03-20'),
-- (4, 'Juan', 'Perez', 2, 65000.00, '2023-02-01');
-- GO

-- PRINT 'Datos insertados.';
-- GO

-- PRINT 'Paso 4: Realizando Consultas SELECT';
-- PRINT '--- Todos los Empleados ---';
-- SELECT * FROM Empleados;
-- GO

-- PRINT '--- Nombre y Salario de Empleados en Ventas (DepartamentoID = 1) ---';
-- SELECT Nombre, Apellido, Salario 
-- FROM Empleados 
-- WHERE DepartamentoID = 1;
-- GO

-- PRINT '--- Empleados con Salario mayor a 60000 ---';
-- SELECT EmpleadoID, Nombre, Salario
-- FROM Empleados
-- WHERE Salario > 60000;
-- GO

-- PRINT 'Paso 5: Realizando Actualizaciones (UPDATE)';
-- PRINT '--- Actualizando Salario de Ana Lopez (EmpleadoID = 1) ---';
-- UPDATE Empleados
-- SET Salario = Salario * 1.05  -- Aumento del 5%
-- WHERE EmpleadoID = 1;
-- GO

-- PRINT '--- Cambiando Departamento de Juan Perez (EmpleadoID = 4) a Ventas (DepartamentoID = 1) ---';
-- UPDATE Empleados
-- SET DepartamentoID = 1, Apellido = 'Perez Actualizado'
-- WHERE EmpleadoID = 4;
-- GO

-- PRINT '--- Empleados Después de Actualizaciones ---';
-- SELECT * FROM Empleados;
-- GO

-- PRINT 'Paso 6: Realizando Eliminaciones (DELETE)';
-- PRINT '--- Eliminando Empleados del Departamento de TI (DepartamentoID = 2) ---';
-- DELETE FROM Empleados 
-- WHERE DepartamentoID = 2;
-- GO

-- PRINT '--- Empleados Después de Eliminaciones ---';
-- SELECT * FROM Empleados;
-- GO

-- PRINT '--- Eliminando todos los registros restantes de Empleados (si los hay) ---';
-- DELETE Empleados; 
-- GO

-- PRINT '--- Tabla Empleados después de eliminar todos los registros ---';
-- SELECT * FROM Empleados;
-- GO

-- PRINT '--- Script de Simulación T-SQL Finalizado ---';

-- En ejemplos_codigo/prueba_tsql.sql
PRINT '--- Pruebas con DECLARE y SET ---';
GO

DECLARE @MiVariableEntera INT;
DECLARE @MiTexto VARCHAR(50) = 'Hola T-SQL';
DECLARE @OtraVariable INT = 100;
GO

SET @MiVariableEntera = 10 * (2 + 3);
SET @MiTexto = @MiTexto + ' Concatenado';
-- SET @OtraVariable = @MiVariableEntera / 2; -- Si ya tienes expresiones aritméticas en SET
GO

PRINT 'Valor de @MiVariableEntera:';
PRINT @MiVariableEntera;
PRINT 'Valor de @MiTexto:';
PRINT @MiTexto;
PRINT 'Valor de @OtraVariable:';
PRINT @OtraVariable;
GO
