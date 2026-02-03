import sqlite3
import os
from contextlib import contextmanager

# Ruta de la base de datos SQLite
DB_PATH = os.path.join(os.path.dirname(__file__), 'inventario.db')

@contextmanager
def get_db_connection():
    """Obtener una conexión a la base de datos SQLite"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Para obtener resultados como diccionarios
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_database():
    """Inicializar la base de datos con las tablas necesarias"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Crear tabla Categorias
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Categorias (
                CategoriaID INTEGER PRIMARY KEY AUTOINCREMENT,
                Nombre VARCHAR(50) NOT NULL
            )
        """)
        
        # Crear tabla Proveedores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Proveedores (
                ProveedorID INTEGER PRIMARY KEY AUTOINCREMENT,
                Nombre VARCHAR(100),
                Contacto VARCHAR(100)
            )
        """)
        
        # Crear tabla Productos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Productos (
                ProductoID INTEGER PRIMARY KEY AUTOINCREMENT,
                Nombre VARCHAR(100) NOT NULL,
                Precio DECIMAL(10,2),
                Stock INTEGER,
                CategoriaID INTEGER,
                ProveedorID INTEGER,
                FechaAlta DATE,
                FOREIGN KEY (CategoriaID) REFERENCES Categorias(CategoriaID),
                FOREIGN KEY (ProveedorID) REFERENCES Proveedores(ProveedorID)
            )
        """)
        
        # Crear tabla MovimientosInventario
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS MovimientosInventario (
                MovimientoID INTEGER PRIMARY KEY AUTOINCREMENT,
                ProductoID INTEGER,
                Tipo TEXT CHECK(Tipo IN ('Entrada', 'Salida')),
                Cantidad INTEGER,
                Fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ProductoID) REFERENCES Productos(ProductoID)
            )
        """)
        
        # Crear tabla Usuarios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Usuarios (
                UsuarioID INTEGER PRIMARY KEY AUTOINCREMENT,
                Nombre VARCHAR(100),
                CorreoElectronico VARCHAR(100),
                Contrasena VARCHAR(100)
            )
        """)
        
        # Crear tabla FechasProductos (opcional)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS FechasProductos (
                FechaID INTEGER PRIMARY KEY AUTOINCREMENT,
                ProductoID INTEGER,
                FechaAlta DATE,
                FOREIGN KEY (ProductoID) REFERENCES Productos(ProductoID) ON DELETE CASCADE
            )
        """)
        
        # ⭐ NUEVA: Crear tabla Ventas para registro completo
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Ventas (
                VentaID INTEGER PRIMARY KEY AUTOINCREMENT,
                Fecha DATETIME NOT NULL,
                Total DECIMAL(10,2) NOT NULL,
                Recibido DECIMAL(10,2) NOT NULL,
                Cambio DECIMAL(10,2) NOT NULL,
                Descripcion TEXT
            )
        """)
        
        # ⭐ NUEVA: Crear tabla DetalleVentas (items de cada venta)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS DetalleVentas (
                DetalleID INTEGER PRIMARY KEY AUTOINCREMENT,
                VentaID INTEGER NOT NULL,
                ProductoID INTEGER NOT NULL,
                NombreProducto VARCHAR(100) NOT NULL,
                Cantidad INTEGER NOT NULL,
                PrecioUnitario DECIMAL(10,2) NOT NULL,
                Subtotal DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (VentaID) REFERENCES Ventas(VentaID) ON DELETE CASCADE,
                FOREIGN KEY (ProductoID) REFERENCES Productos(ProductoID)
            )
        """)
        
        # Insertar datos de prueba si no existen
        cursor.execute("SELECT COUNT(*) FROM Categorias")
        if cursor.fetchone()[0] == 0:
            # Datos de prueba - Categorias
            cursor.execute("INSERT INTO Categorias (Nombre) VALUES ('Electrónica')")
            cursor.execute("INSERT INTO Categorias (Nombre) VALUES ('Muebles')")
            cursor.execute("INSERT INTO Categorias (Nombre) VALUES ('Joyería')")
            
            # Datos de prueba - Proveedores
            cursor.execute("INSERT INTO Proveedores (Nombre, Contacto) VALUES ('Proveedor A', 'proveedora@example.com')")
            cursor.execute("INSERT INTO Proveedores (Nombre, Contacto) VALUES ('Proveedor B', 'proveedorb@example.com')")
            
            # Datos de prueba - Productos
            cursor.execute("""
                INSERT INTO Productos (Nombre, Precio, Stock, CategoriaID, ProveedorID)
                VALUES ('Laptop', 800.00, 15, 1, 1)
            """)
            cursor.execute("""
                INSERT INTO Productos (Nombre, Precio, Stock, CategoriaID, ProveedorID)
                VALUES ('Escritorio', 150.00, 20, 2, 2)
            """)
            cursor.execute("""
                INSERT INTO Productos (Nombre, Precio, Stock, CategoriaID, ProveedorID)
                VALUES ('Collar de plata', 250.00, 10, 3, 1)
            """)
            cursor.execute("""
                INSERT INTO Productos (Nombre, Precio, Stock, CategoriaID, ProveedorID)
                VALUES ('Silla', 75.00, 25, 2, 2)
            """)
            cursor.execute("""
                INSERT INTO Productos (Nombre, Precio, Stock, CategoriaID, ProveedorID)
                VALUES ('Monitor', 300.00, 18, 1, 1)
            """)
            
            # Datos de prueba - Usuarios
            cursor.execute("""
                INSERT INTO Usuarios (Nombre, CorreoElectronico, Contrasena)
                VALUES ('Andrés', 'andres@empresa.com', '1234')
            """)
            cursor.execute("""
                INSERT INTO Usuarios (Nombre, CorreoElectronico, Contrasena)
                VALUES ('Admin', 'admin@empresa.com', 'adminpass')
            """)
            
            print("✅ Datos de prueba insertados")
        
        conn.commit()
        print("✅ Base de datos SQLite inicializada correctamente")

def test_connection():
    """Probar la conexión a la base de datos"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()[0]
            print(f"✅ Conectado a SQLite versión {version}")
            return True
    except Exception as err:
        print(f"❌ Error de conexión a SQLite: {err}")
        return False

def execute_query(query, params=None, fetch=True):
    """
    Ejecutar una consulta SQL
    
    Args:
        query: Consulta SQL
        params: Parámetros de la consulta (tupla o lista)
        fetch: Si True, devuelve resultados. Si False, solo ejecuta
    
    Returns:
        Lista de resultados o ID insertado/filas afectadas
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch:
            # Convertir Row objects a diccionarios
            results = [dict(row) for row in cursor.fetchall()]
            return results
        else:
            # Para INSERT, devolver el ID insertado
            if cursor.lastrowid:
                return cursor.lastrowid
            # Para UPDATE/DELETE, devolver filas afectadas
            return cursor.rowcount

def execute_transaction(operations):
    """
    Ejecutar múltiples operaciones en una transacción
    
    Args:
        operations: Lista de tuplas (query, params)
    
    Returns:
        Lista de resultados
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        results = []
        
        for query, params in operations:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Guardar resultado si es SELECT
            if query.strip().upper().startswith('SELECT'):
                results.append([dict(row) for row in cursor.fetchall()])
            else:
                results.append(cursor.lastrowid if cursor.lastrowid else cursor.rowcount)
        
        return results