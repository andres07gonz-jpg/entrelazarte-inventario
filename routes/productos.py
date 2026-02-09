from flask import Blueprint, jsonify, request
from database import execute_query, execute_transaction
from datetime import datetime
import os

productos_bp = Blueprint('productos', __name__)

# Contraseña de administrador desde .env o por defecto
ADMIN_PASS = os.getenv('ADMIN_PASSWORD', 'admin123')

def verificar_admin(req):
    """Verificar contraseña de administrador desde header"""
    password = req.headers.get('x-admin-pass')
    if password != ADMIN_PASS:
        return False
    return True

@productos_bp.route('/', methods=['GET'])
def obtener_productos():
    """Obtener todos los productos con información completa"""
    try:
        query = """
            SELECT 
                p.ProductoID,
                p.Nombre,
                p.Precio,
                p.Stock,
                p.FechaAlta,
                c.Nombre as Categoria,
                prov.Nombre as Proveedor
            FROM Productos p
            LEFT JOIN Categorias c ON p.CategoriaID = c.CategoriaID
            LEFT JOIN Proveedores prov ON p.ProveedorID = prov.ProveedorID
            ORDER BY p.ProductoID DESC
        """
        productos = execute_query(query)
        return jsonify(productos), 200
    except Exception as e:
        print(f"❌ Error en obtener_productos: {e}")
        return jsonify({'error': str(e)}), 500

@productos_bp.route('/<int:id>', methods=['GET'])
def obtener_producto(id):
    """Obtener un producto específico"""
    try:
        query = """
            SELECT 
                p.ProductoID,
                p.Nombre,
                p.Precio,
                p.Stock,
                p.FechaAlta,
                p.CategoriaID,
                p.ProveedorID,
                c.Nombre as Categoria,
                prov.Nombre as Proveedor
            FROM Productos p
            LEFT JOIN Categorias c ON p.CategoriaID = c.CategoriaID
            LEFT JOIN Proveedores prov ON p.ProveedorID = prov.ProveedorID
            WHERE p.ProductoID = ?
        """
        resultado = execute_query(query, (id,))
        
        if not resultado:
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        return jsonify(resultado[0]), 200
    except Exception as e:
        print(f"❌ Error en obtener_producto: {e}")
        return jsonify({'error': str(e)}), 500

@productos_bp.route('/', methods=['POST'])
def crear_producto():
    """Crear un nuevo producto"""
    try:
        data = request.json
        
        # Validaciones
        if not data.get('Nombre'):
            return jsonify({'error': 'El nombre es obligatorio'}), 400
        
        # Valores por defecto
        nombre = data['Nombre']
        precio = data.get('Precio', 0)
        stock = data.get('Stock', 0)
        categoria_id = data.get('CategoriaID', None)
        proveedor_id = data.get('ProveedorID', None)
        fecha_alta = data.get('FechaAlta', datetime.now().strftime('%Y-%m-%d'))
        
        query = """
            INSERT INTO Productos (Nombre, Precio, Stock, CategoriaID, ProveedorID, FechaAlta)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        
        producto_id = execute_query(
            query,
            (nombre, precio, stock, categoria_id, proveedor_id, fecha_alta),
            fetch=False
        )
        
        print(f"✅ Producto creado: ID={producto_id}, Nombre={nombre}")
        
        return jsonify({
            'mensaje': 'Producto creado exitosamente',
            'ProductoID': producto_id
        }), 201
        
    except Exception as e:
        print(f"❌ Error en crear_producto: {e}")
        return jsonify({'error': str(e)}), 500

@productos_bp.route('/<int:id>', methods=['PUT'])
def actualizar_producto(id):
    """Actualizar un producto"""
    try:
        data = request.json
        print(f"📝 Actualizando producto {id} con datos: {data}")
        
        # Verificar que el producto existe
        producto_existe = execute_query("SELECT ProductoID FROM Productos WHERE ProductoID = ?", (id,))
        if not producto_existe:
            print(f"❌ Producto {id} no encontrado")
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        # Construir query dinámica
        campos = []
        valores = []
        
        if 'Nombre' in data:
            campos.append('Nombre = ?')
            valores.append(data['Nombre'])
        
        if 'Precio' in data:
            campos.append('Precio = ?')
            valores.append(data['Precio'])
        
        if 'Stock' in data:
            campos.append('Stock = ?')
            valores.append(data['Stock'])
            print(f"📦 Nuevo stock para producto {id}: {data['Stock']}")
        
        if 'CategoriaID' in data:
            campos.append('CategoriaID = ?')
            valores.append(data['CategoriaID'])
        
        if 'ProveedorID' in data:
            campos.append('ProveedorID = ?')
            valores.append(data['ProveedorID'])
        
        if not campos:
            print("⚠️ No hay campos para actualizar")
            return jsonify({'error': 'No hay campos para actualizar'}), 400
        
        valores.append(id)
        query = f"UPDATE Productos SET {', '.join(campos)} WHERE ProductoID = ?"
        
        print(f"🔍 Query: {query}")
        print(f"🔍 Valores: {valores}")
        
        filas_afectadas = execute_query(query, tuple(valores), fetch=False)
        
        print(f"✅ Filas afectadas: {filas_afectadas}")
        
        if filas_afectadas == 0:
            print(f"⚠️ No se actualizó ninguna fila para producto {id}")
            # Aunque no se actualizó, devolvemos éxito si el producto existe
            return jsonify({'mensaje': 'Producto actualizado exitosamente'}), 200
        
        return jsonify({'mensaje': 'Producto actualizado exitosamente'}), 200
        
    except Exception as e:
        print(f"❌ Error en actualizar_producto: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@productos_bp.route('/<int:id>', methods=['DELETE'])
def eliminar_producto(id):
    """Eliminar un producto (requiere contraseña de admin)"""
    try:
        # Verificar contraseña de administrador
        if not verificar_admin(request):
            return jsonify({'error': 'Contraseña de administrador incorrecta'}), 403
        
        # Eliminar producto
        query = "DELETE FROM Productos WHERE ProductoID = ?"
        filas_afectadas = execute_query(query, (id,), fetch=False)
        
        if filas_afectadas == 0:
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        print(f"✅ Producto {id} eliminado")
        
        return jsonify({'mensaje': 'Producto eliminado exitosamente'}), 200
        
    except Exception as e:
        print(f"❌ Error en eliminar_producto: {e}")
        return jsonify({'error': str(e)}), 500

# ========== FECHAS ESPECIALES ==========

@productos_bp.route('/<int:id>/fechas', methods=['GET'])
def obtener_fechas(id):
    """Obtener todas las fechas especiales de un producto"""
    try:
        query = """
            SELECT FechaID, ProductoID, FechaAlta
            FROM FechasProductos
            WHERE ProductoID = ?
            ORDER BY FechaAlta DESC
        """
        fechas = execute_query(query, (id,))
        return jsonify(fechas), 200
    except Exception as e:
        print(f"❌ Error en obtener_fechas: {e}")
        return jsonify({'error': str(e)}), 500

@productos_bp.route('/<int:id>/fechas', methods=['POST'])
def agregar_fecha(id):
    """Agregar una fecha especial a un producto (requiere contraseña de admin)"""
    try:
        # Verificar contraseña de administrador
        if not verificar_admin(request):
            return jsonify({'error': 'Contraseña de administrador incorrecta'}), 403
        
        data = request.json
        fecha_alta = data.get('FechaAlta')
        
        if not fecha_alta:
            return jsonify({'error': 'La fecha es obligatoria'}), 400
        
        # Verificar que el producto existe
        producto = execute_query("SELECT ProductoID FROM Productos WHERE ProductoID = ?", (id,))
        if not producto:
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        # Insertar fecha
        query = "INSERT INTO FechasProductos (ProductoID, FechaAlta) VALUES (?, ?)"
        fecha_id = execute_query(query, (id, fecha_alta), fetch=False)
        
        print(f"✅ Fecha especial agregada: ID={fecha_id}, Producto={id}, Fecha={fecha_alta}")
        
        return jsonify({
            'mensaje': 'Fecha agregada exitosamente',
            'FechaID': fecha_id
        }), 201
        
    except Exception as e:
        print(f"❌ Error en agregar_fecha: {e}")
        return jsonify({'error': str(e)}), 500

@productos_bp.route('/<int:producto_id>/fechas/<int:fecha_id>', methods=['DELETE'])
def eliminar_fecha(producto_id, fecha_id):
    """Eliminar una fecha especial (requiere contraseña de admin)"""
    try:
        # Verificar contraseña de administrador
        if not verificar_admin(request):
            return jsonify({'error': 'Contraseña de administrador incorrecta'}), 403
        
        query = "DELETE FROM FechasProductos WHERE FechaID = ? AND ProductoID = ?"
        filas_afectadas = execute_query(query, (fecha_id, producto_id), fetch=False)
        
        if filas_afectadas == 0:
            return jsonify({'error': 'Fecha no encontrada'}), 404
        
        print(f"✅ Fecha {fecha_id} eliminada del producto {producto_id}")
        
        return jsonify({'mensaje': 'Fecha eliminada exitosamente'}), 200
        
    except Exception as e:
        print(f"❌ Error en eliminar_fecha: {e}")
        return jsonify({'error': str(e)}), 500

# ========== MOVIMIENTOS DE INVENTARIO ==========

@productos_bp.route('/<int:id>/movimientos', methods=['GET'])
def obtener_movimientos(id):
    """Obtener historial de movimientos de un producto"""
    try:
        query = """
            SELECT MovimientoID, ProductoID, Tipo, Cantidad, Fecha
            FROM MovimientosInventario
            WHERE ProductoID = ?
            ORDER BY Fecha DESC
        """
        movimientos = execute_query(query, (id,))
        return jsonify(movimientos), 200
    except Exception as e:
        print(f"❌ Error en obtener_movimientos: {e}")
        return jsonify({'error': str(e)}), 500

@productos_bp.route('/<int:id>/movimientos', methods=['POST'])
def registrar_movimiento(id):
    """Registrar entrada o salida de inventario"""
    try:
        data = request.json
        tipo = data.get('Tipo')  # 'Entrada' o 'Salida'
        cantidad = data.get('Cantidad', 0)
        
        if tipo not in ['Entrada', 'Salida']:
            return jsonify({'error': 'Tipo debe ser "Entrada" o "Salida"'}), 400
        
        if cantidad <= 0:
            return jsonify({'error': 'La cantidad debe ser mayor a 0'}), 400
        
        # Obtener stock actual
        producto = execute_query("SELECT Stock FROM Productos WHERE ProductoID = ?", (id,))
        if not producto:
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        stock_actual = producto[0]['Stock']
        
        # Calcular nuevo stock
        if tipo == 'Entrada':
            nuevo_stock = stock_actual + cantidad
        else:  # Salida
            if cantidad > stock_actual:
                return jsonify({'error': 'Stock insuficiente'}), 400
            nuevo_stock = stock_actual - cantidad
        
        # Ejecutar en transacción
        operations = [
            ("INSERT INTO MovimientosInventario (ProductoID, Tipo, Cantidad) VALUES (?, ?, ?)",
             (id, tipo, cantidad)),
            ("UPDATE Productos SET Stock = ? WHERE ProductoID = ?",
             (nuevo_stock, id))
        ]
        
        execute_transaction(operations)
        
        print(f"✅ Movimiento registrado: Producto={id}, Tipo={tipo}, Cantidad={cantidad}, Stock: {stock_actual} → {nuevo_stock}")
        
        return jsonify({
            'mensaje': 'Movimiento registrado exitosamente',
            'stock_anterior': stock_actual,
            'stock_nuevo': nuevo_stock
        }), 201
        
    except Exception as e:
        print(f"❌ Error en registrar_movimiento: {e}")
        return jsonify({'error': str(e)}), 500