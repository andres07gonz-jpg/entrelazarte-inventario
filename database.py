import os
from contextlib import contextmanager

# Detectar si estamos en Railway (PostgreSQL) o local (SQLite)
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL:
    # Producción - PostgreSQL
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    # Railway usa postgres:// pero psycopg2 necesita postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    @contextmanager
    def get_db_connection():
        """Obtener conexión a PostgreSQL"""
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def execute_query(query, params=None, fetch=True):
        """Ejecutar query en PostgreSQL"""
        # Convertir ? a %s para PostgreSQL
        query = query.replace('?', '%s')
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch:
                results = [dict(row) for row in cursor.fetchall()]
                return results
            else:
                if cursor.lastrowid if hasattr(cursor, 'lastrowid') else None:
                    return cursor.lastrowid
                return cursor.rowcount
    
else:
    # Local - SQLite
    import sqlite3
    
    DB_PATH = os.path.join(os.path.dirname(__file__), 'inventario.db')
    
    @contextmanager
    def get_db_connection():
        """Obtener conexión a SQLite"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def execute_query(query, params=None, fetch=True):
        """Ejecutar query en SQLite"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch:
                results = [dict(row) for row in cursor.fetchall()]
                return results
            else:
                if cursor.lastrowid:
                    return cursor.lastrowid
                return cursor.rowcount

def execute_transaction(operations):
    """Ejecutar múltiples operaciones en transacción"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        results = []
        
        for query, params in operations:
            # Para PostgreSQL, convertir ? a %s
            if DATABASE_URL:
                query = query.replace('?', '%s')
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                results.append([dict(row) for row in cursor.fetchall()])
            else:
                last_id = cursor.lastrowid if hasattr(cursor, 'lastrowid') and cursor.lastrowid else None
                results.append(last_id if last_id else cursor.rowcount)
        
        return results

def init_database():
    """Inicializar base de datos"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Detectar tipo de base de datos para usar sintaxis correcta
        if DATABASE_URL:
            # PostgreSQL
            autoincrement = "SERIAL PRIMARY KEY"
            datetime_default = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            decimal_type = "DECIMAL(10,2)"
        else:
            # SQLite
            autoincrement = "INTEGER PRIMARY KEY AUTOINCREMENT"
            datetime_default = "DATETIME DEFAULT CURRENT_TIMESTAMP"
            decimal_type = "DECIMAL(10,2)"
        
        # Crear tabla Categorias
        if DATABASE_URL:
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS Categorias (
                    CategoriaID SERIAL PRIMARY KEY,
                    Nombre VARCHAR(50) NOT NULL
                )
            """)
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Categorias (
                    CategoriaID INTEGER PRIMARY KEY AUTOINCREMENT,
                    Nombre VARCHAR(50) NOT NULL
                )
            """)
        
        # Crear tabla Proveedores
        if DATABASE_URL:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Proveedores (
                    ProveedorID SERIAL PRIMARY KEY,
                    Nombre VARCHAR(100),
                    Contacto VARCHAR(100)
                )
            """)
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Proveedores (
                    ProveedorID INTEGER PRIMARY KEY AUTOINCREMENT,
                    Nombre VARCHAR(100),
                    Contacto VARCHAR(100)
                )
            """)
        
        # Crear tabla Productos
        if DATABASE_URL:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Productos (
                    ProductoID SERIAL PRIMARY KEY,
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
        else:
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
        if DATABASE_URL:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS MovimientosInventario (
                    MovimientoID SERIAL PRIMARY KEY,
                    ProductoID INTEGER,
                    Tipo TEXT CHECK(Tipo IN ('Entrada', 'Salida')),
                    Cantidad INTEGER,
                    Fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ProductoID) REFERENCES Productos(ProductoID)
                )
            """)
        else:
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
        if DATABASE_URL:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Usuarios (
                    UsuarioID SERIAL PRIMARY KEY,
                    Nombre VARCHAR(100),
                    CorreoElectronico VARCHAR(100),
                    Contrasena VARCHAR(100)
                )
            """)
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Usuarios (
                    UsuarioID INTEGER PRIMARY KEY AUTOINCREMENT,
                    Nombre VARCHAR(100),
                    CorreoElectronico VARCHAR(100),
                    Contrasena VARCHAR(100)
                )
            """)
        
        # Crear tabla FechasProductos
        if DATABASE_URL:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS FechasProductos (
                    FechaID SERIAL PRIMARY KEY,
                    ProductoID INTEGER,
                    FechaAlta DATE,
                    FOREIGN KEY (ProductoID) REFERENCES Productos(ProductoID) ON DELETE CASCADE
                )
            """)
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS FechasProductos (
                    FechaID INTEGER PRIMARY KEY AUTOINCREMENT,
                    ProductoID INTEGER,
                    FechaAlta DATE,
                    FOREIGN KEY (ProductoID) REFERENCES Productos(ProductoID) ON DELETE CASCADE
                )
            """)
        
        # Crear tabla Ventas
        if DATABASE_URL:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Ventas (
                    VentaID SERIAL PRIMARY KEY,
                    Fecha TIMESTAMP NOT NULL,
                    Total DECIMAL(10,2) NOT NULL,
                    Recibido DECIMAL(10,2) NOT NULL,
                    Cambio DECIMAL(10,2) NOT NULL,
                    Descripcion TEXT
                )
            """)
        else:
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
        
        # Crear tabla DetalleVentas
        if DATABASE_URL:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS DetalleVentas (
                    DetalleID SERIAL PRIMARY KEY,
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
        else:
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
        
        # Insertar datos de prueba solo si no existen
        cursor.execute("SELECT COUNT(*) as count FROM Categorias")
        result = cursor.fetchone()
        count = result['count'] if DATABASE_URL else result[0]
        
        if count == 0:
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
        db_type = "PostgreSQL" if DATABASE_URL else "SQLite"
        print(f"✅ Base de datos {db_type} inicializada correctamente")

def test_connection():
    """Probar conexión a la base de datos"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if DATABASE_URL:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()['version']
                print(f"✅ Conectado a PostgreSQL: {version}")
            else:
                cursor.execute("SELECT sqlite_version()")
                version = cursor.fetchone()[0]
                print(f"✅ Conectado a SQLite versión {version}")
            return True
    except Exception as err:
        print(f"❌ Error de conexión: {err}")
        return False
    
    