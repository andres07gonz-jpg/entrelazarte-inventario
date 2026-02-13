import os
from contextlib import contextmanager

DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    @contextmanager
    def get_db_connection():
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
        query = query.replace('?', '%s')
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if fetch:
                cursor.execute(query, params) if params else cursor.execute(query)
                return [dict(row) for row in cursor.fetchall()]
            else:
                # Para INSERT usar RETURNING para obtener el ID
                if query.strip().upper().startswith('INSERT'):
                    if 'RETURNING' not in query.upper():
                        query = query.rstrip(';') + ' RETURNING *'
                    cursor.execute(query, params) if params else cursor.execute(query)
                    result = cursor.fetchone()
                    if result:
                        row = dict(result)
                        return list(row.values())[0]
                    return None
                else:
                    cursor.execute(query, params) if params else cursor.execute(query)
                    return cursor.rowcount

    def execute_transaction(operations):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            results = []
            for query, params in operations:
                query = query.replace('?', '%s')
                if query.strip().upper().startswith('SELECT'):
                    cursor.execute(query, params) if params else cursor.execute(query)
                    results.append([dict(row) for row in cursor.fetchall()])
                elif query.strip().upper().startswith('INSERT'):
                    q = query.rstrip(';') + ' RETURNING *' if 'RETURNING' not in query.upper() else query
                    cursor.execute(q, params) if params else cursor.execute(q)
                    result = cursor.fetchone()
                    if result:
                        row = dict(result)
                        results.append(list(row.values())[0])
                    else:
                        results.append(None)
                else:
                    cursor.execute(query, params) if params else cursor.execute(query)
                    results.append(cursor.rowcount)
            return results

else:
    import sqlite3
    DB_PATH = os.path.join(os.path.dirname(__file__), 'inventario.db')

    @contextmanager
    def get_db_connection():
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
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params) if params else cursor.execute(query)
            if fetch:
                return [dict(row) for row in cursor.fetchall()]
            else:
                return cursor.lastrowid if cursor.lastrowid else cursor.rowcount

    def execute_transaction(operations):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            results = []
            for query, params in operations:
                cursor.execute(query, params) if params else cursor.execute(query)
                if query.strip().upper().startswith('SELECT'):
                    results.append([dict(row) for row in cursor.fetchall()])
                else:
                    results.append(cursor.lastrowid if cursor.lastrowid else cursor.rowcount)
            return results


def init_database():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        is_pg = DATABASE_URL is not None

        if is_pg:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Categorias (
                    CategoriaID SERIAL PRIMARY KEY,
                    Nombre VARCHAR(50) NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Proveedores (
                    ProveedorID SERIAL PRIMARY KEY,
                    Nombre VARCHAR(100),
                    Contacto VARCHAR(100)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Productos (
                    ProductoID SERIAL PRIMARY KEY,
                    Nombre VARCHAR(100) NOT NULL,
                    Precio DECIMAL(10,2),
                    Stock INTEGER DEFAULT 0,
                    CategoriaID INTEGER REFERENCES Categorias(CategoriaID),
                    ProveedorID INTEGER REFERENCES Proveedores(ProveedorID),
                    FechaAlta DATE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS MovimientosInventario (
                    MovimientoID SERIAL PRIMARY KEY,
                    ProductoID INTEGER REFERENCES Productos(ProductoID),
                    Tipo TEXT CHECK(Tipo IN ('Entrada', 'Salida')),
                    Cantidad INTEGER,
                    Fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Usuarios (
                    UsuarioID SERIAL PRIMARY KEY,
                    Nombre VARCHAR(100),
                    CorreoElectronico VARCHAR(100),
                    Contrasena VARCHAR(100)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS FechasProductos (
                    FechaID SERIAL PRIMARY KEY,
                    ProductoID INTEGER REFERENCES Productos(ProductoID) ON DELETE CASCADE,
                    FechaAlta DATE
                )
            """)
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
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS DetalleVentas (
                    DetalleID SERIAL PRIMARY KEY,
                    VentaID INTEGER NOT NULL REFERENCES Ventas(VentaID) ON DELETE CASCADE,
                    ProductoID INTEGER NOT NULL REFERENCES Productos(ProductoID),
                    NombreProducto VARCHAR(100) NOT NULL,
                    Cantidad INTEGER NOT NULL,
                    PrecioUnitario DECIMAL(10,2) NOT NULL,
                    Subtotal DECIMAL(10,2) NOT NULL
                )
            """)
        else:
            cursor.execute("""CREATE TABLE IF NOT EXISTS Categorias (
                CategoriaID INTEGER PRIMARY KEY AUTOINCREMENT, Nombre VARCHAR(50) NOT NULL)""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS Proveedores (
                ProveedorID INTEGER PRIMARY KEY AUTOINCREMENT, Nombre VARCHAR(100), Contacto VARCHAR(100))""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS Productos (
                ProductoID INTEGER PRIMARY KEY AUTOINCREMENT, Nombre VARCHAR(100) NOT NULL,
                Precio DECIMAL(10,2), Stock INTEGER DEFAULT 0, CategoriaID INTEGER, ProveedorID INTEGER, FechaAlta DATE,
                FOREIGN KEY (CategoriaID) REFERENCES Categorias(CategoriaID),
                FOREIGN KEY (ProveedorID) REFERENCES Proveedores(ProveedorID))""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS MovimientosInventario (
                MovimientoID INTEGER PRIMARY KEY AUTOINCREMENT, ProductoID INTEGER,
                Tipo TEXT CHECK(Tipo IN ('Entrada', 'Salida')), Cantidad INTEGER,
                Fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ProductoID) REFERENCES Productos(ProductoID))""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS Usuarios (
                UsuarioID INTEGER PRIMARY KEY AUTOINCREMENT, Nombre VARCHAR(100),
                CorreoElectronico VARCHAR(100), Contrasena VARCHAR(100))""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS FechasProductos (
                FechaID INTEGER PRIMARY KEY AUTOINCREMENT, ProductoID INTEGER, FechaAlta DATE,
                FOREIGN KEY (ProductoID) REFERENCES Productos(ProductoID) ON DELETE CASCADE)""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS Ventas (
                VentaID INTEGER PRIMARY KEY AUTOINCREMENT, Fecha DATETIME NOT NULL,
                Total DECIMAL(10,2) NOT NULL, Recibido DECIMAL(10,2) NOT NULL,
                Cambio DECIMAL(10,2) NOT NULL, Descripcion TEXT)""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS DetalleVentas (
                DetalleID INTEGER PRIMARY KEY AUTOINCREMENT, VentaID INTEGER NOT NULL,
                ProductoID INTEGER NOT NULL, NombreProducto VARCHAR(100) NOT NULL,
                Cantidad INTEGER NOT NULL, PrecioUnitario DECIMAL(10,2) NOT NULL,
                Subtotal DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (VentaID) REFERENCES Ventas(VentaID) ON DELETE CASCADE,
                FOREIGN KEY (ProductoID) REFERENCES Productos(ProductoID))""")

        # Insertar datos de prueba si no existen
        if is_pg:
            cursor.execute("SELECT COUNT(*) as count FROM Categorias")
            count = cursor.fetchone()['count']
        else:
            cursor.execute("SELECT COUNT(*) FROM Categorias")
            count = cursor.fetchone()[0]

        if count == 0:
            cursor.execute("INSERT INTO Categorias (Nombre) VALUES ('Electronica')")
            cursor.execute("INSERT INTO Categorias (Nombre) VALUES ('Muebles')")
            cursor.execute("INSERT INTO Categorias (Nombre) VALUES ('Joyeria')")
            cursor.execute("INSERT INTO Proveedores (Nombre, Contacto) VALUES ('Proveedor A', 'proveedora@example.com')")
            cursor.execute("INSERT INTO Proveedores (Nombre, Contacto) VALUES ('Proveedor B', 'proveedorb@example.com')")
            cursor.execute("INSERT INTO Productos (Nombre, Precio, Stock, CategoriaID, ProveedorID) VALUES ('Laptop', 800.00, 15, 1, 1)")
            cursor.execute("INSERT INTO Productos (Nombre, Precio, Stock, CategoriaID, ProveedorID) VALUES ('Escritorio', 150.00, 20, 2, 2)")
            cursor.execute("INSERT INTO Productos (Nombre, Precio, Stock, CategoriaID, ProveedorID) VALUES ('Collar de plata', 250.00, 10, 3, 1)")
            cursor.execute("INSERT INTO Productos (Nombre, Precio, Stock, CategoriaID, ProveedorID) VALUES ('Silla', 75.00, 25, 2, 2)")
            cursor.execute("INSERT INTO Productos (Nombre, Precio, Stock, CategoriaID, ProveedorID) VALUES ('Monitor', 300.00, 18, 1, 1)")
            print("Datos de prueba insertados")

        conn.commit()
        db_type = "PostgreSQL" if is_pg else "SQLite"
        print(f"Base de datos {db_type} inicializada correctamente")


def test_connection():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if DATABASE_URL:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()['version']
                print(f"Conectado a PostgreSQL: {version}")
            else:
                cursor.execute("SELECT sqlite_version()")
                version = cursor.fetchone()[0]
                print(f"Conectado a SQLite version {version}")
            return True
    except Exception as err:
        print(f"Error de conexion: {err}")
        return False