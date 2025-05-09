-- Script de T-SQL de ejemplo
PRINT 'Iniciando script de prueba para T-SQL';
GO

DECLARE @NombreCliente VARCHAR(100), @CiudadCliente VARCHAR(50);
DECLARE @TotalPedidos INT;

SET @NombreCliente = 'Cliente Ejemplo S.A.';
SET @CiudadCliente = 'Ciudad Gótica';
SET @TotalPedidos = 0;

IF EXISTS (SELECT 1 FROM sys.tables WHERE name = 'PedidosSimulados')
BEGIN
    PRINT 'La tabla PedidosSimulados ya existe.';
    SELECT @TotalPedidos = COUNT(*) FROM PedidosSimulados WHERE Cliente = @NombreCliente;
END
ELSE
BEGIN
    PRINT 'La tabla PedidosSimulados no existe. Creándola...';
    /*
    CREATE TABLE PedidosSimulados (
        PedidoID INT PRIMARY KEY IDENTITY(1,1),
        Cliente VARCHAR(100),
        FechaPedido DATETIME DEFAULT GETDATE(),
        Monto DECIMAL(10,2)
    );
    INSERT INTO PedidosSimulados (Cliente, Monto) VALUES (@NombreCliente, 150.75);
    SET @TotalPedidos = 1;
    */
    PRINT 'Tabla PedidosSimulados creada (simulado).';
END

PRINT 'Cliente: ' + @NombreCliente + ' de ' + @CiudadCliente;
PRINT 'Total de pedidos encontrados: ' + CAST(@TotalPedidos AS VARCHAR(10));
GO

SELECT @@VERSION AS VersionSQLServer;