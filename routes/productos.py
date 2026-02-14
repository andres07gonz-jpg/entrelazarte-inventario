from flask import Blueprint, jsonify, request
from database import execute_query, execute_transaction
from datetime import datetime
import os

productos_bp = Blueprint('productos', __name__)
ADMIN_PASS = os.getenv('ADMIN_PASSWORD', 'admin123')

def verificar_admin(req):
    password = req.headers.get('x-admin-pass')
    return password == ADMIN_PASS

@productos_bp.route('', methods=['GET'])
@productos_bp.route('/', methods=['GET'])
def obtener_productos():
    try:
        query = """
            SELECT p.ProductoID, p.Nombre, p.Precio, p.Stock, p.FechaAlta,
                c.Nombre as Categoria, prov.Nombre as Proveedor
            FROM Productos p
            LEFT JOIN Categorias c ON p.CategoriaID = c.CategoriaID
            LEFT JOIN Proveedores prov ON p.ProveedorID = prov.ProveedorID
            ORDER BY p.ProductoID DESC
        """
        return jsonify(execute_query(query)), 200
    except Exception as e:
        print(f"Error obtener_productos: {e}")
        return jsonify({'error': str(e)}), 500

@productos_bp.route('/<int:id>', methods=['GET'])
def obtener_producto(id):
    try:
        query = """
            SELECT p.ProductoID, p.Nombre, p.Precio, p.Stock, p.FechaAlta,
                p.CategoriaID, p.ProveedorID,
                c.Nombre as Categoria, prov.Nombre as Proveedor
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
        return jsonify({'error': str(e)}), 500

@productos_bp.route('', methods=['POST'])
@productos_bp.route('/', methods=['POST'])
def crear_producto():
    try:
        data = request.json
        if not data.get('Nombre'):
            return jsonify({'error': 'El nombre es obligatorio'}), 400
        nombre = data['Nombre']
        precio = data.get('Precio', 0)
        stock = data.get('Stock', 0)
        categoria_id = data.get('CategoriaID', None)
        proveedor_id = data.get('ProveedorID', None)
        fecha_alta = data.get('FechaAlta', datetime.now().strftime('%Y-%m-%d'))
        query = """INSERT INTO Productos (Nombre, Precio, Stock, CategoriaID, ProveedorID, FechaAlta)
            VALUES (?, ?, ?, ?, ?, ?)"""
        producto_id = execute_query(query, (nombre, precio, stock, categoria_id, proveedor_id, fecha_alta), fetch=False)
        return jsonify({'mensaje': 'Producto creado exitosamente', 'ProductoID': producto_id}), 201
    except Exception as e:
        print(f"Error crear_producto: {e}")
        return jsonify({'error': str(e)}), 500

@productos_bp.route('/<int:id>', methods=['PUT'])
def actualizar_producto(id):
    try:
        data = request.json
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
        if 'CategoriaID' in data:
            campos.append('CategoriaID = ?')
            valores.append(data['CategoriaID'])
        if 'ProveedorID' in data:
            campos.append('ProveedorID = ?')
            valores.append(data['ProveedorID'])
        if not campos:
            return jsonify({'error': 'No hay campos para actualizar'}), 400
        valores.append(id)
        query = f"UPDATE Productos SET {', '.join(campos)} WHERE ProductoID = ?"
        execute_query(query, tuple(valores), fetch=False)
        return jsonify({'mensaje': 'Producto actualizado exitosamente'}), 200
    except Exception as e:
        print(f"Error actualizar_producto: {e}")
        return jsonify({'error': str(e)}), 500

@productos_bp.route('/<int:id>', methods=['DELETE'])
def eliminar_producto(id):
    try:
        if not verificar_admin(request):
            return jsonify({'error': 'Contrasena de administrador incorrecta'}), 403
        filas = execute_query("DELETE FROM Productos WHERE ProductoID = ?", (id,), fetch=False)
        if filas == 0:
            return jsonify({'error': 'Producto no encontrado'}), 404
        return jsonify({'mensaje': 'Producto eliminado exitosamente'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@productos_bp.route('/<int:id>/fechas', methods=['GET'])
def obtener_fechas(id):
    try:
        query = "SELECT FechaID, ProductoID, FechaAlta FROM FechasProductos WHERE ProductoID = ? ORDER BY FechaAlta DESC"
        return jsonify(execute_query(query, (id,))), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@productos_bp.route('/<int:id>/fechas', methods=['POST'])
def agregar_fecha(id):
    try:
        if not verificar_admin(request):
            return jsonify({'error': 'Contrasena de administrador incorrecta'}), 403
        data = request.json
        fecha_alta = data.get('FechaAlta')
        if not fecha_alta:
            return jsonify({'error': 'La fecha es obligatoria'}), 400
        producto = execute_query("SELECT ProductoID FROM Productos WHERE ProductoID = ?", (id,))
        if not producto:
            return jsonify({'error': 'Producto no encontrado'}), 404
        fecha_id = execute_query("INSERT INTO FechasProductos (ProductoID, FechaAlta) VALUES (?, ?)", (id, fecha_alta), fetch=False)
        return jsonify({'mensaje': 'Fecha agregada exitosamente', 'FechaID': fecha_id}), 201
    except Exception as e:
        print(f"Error agregar_fecha: {e}")
        return jsonify({'error': str(e)}), 500

@productos_bp.route('/<int:producto_id>/fechas/<int:fecha_id>', methods=['DELETE'])
def eliminar_fecha(producto_id, fecha_id):
    try:
        if not verificar_admin(request):
            return jsonify({'error': 'Contrasena de administrador incorrecta'}), 403
        filas = execute_query("DELETE FROM FechasProductos WHERE FechaID = ? AND ProductoID = ?", (fecha_id, producto_id), fetch=False)
        if filas == 0:
            return jsonify({'error': 'Fecha no encontrada'}), 404
        return jsonify({'mensaje': 'Fecha eliminada exitosamente'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@productos_bp.route('/<int:id>/movimientos', methods=['GET'])
def obtener_movimientos(id):
    try:
        query = "SELECT MovimientoID, ProductoID, Tipo, Cantidad, Fecha FROM MovimientosInventario WHERE ProductoID = ? ORDER BY Fecha DESC"
        return jsonify(execute_query(query, (id,))), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@productos_bp.route('/<int:id>/movimientos', methods=['POST'])
def registrar_movimiento(id):
    try:
        data = request.json
        tipo = data.get('Tipo')
        cantidad = data.get('Cantidad', 0)
        if tipo not in ['Entrada', 'Salida']:
            return jsonify({'error': 'Tipo debe ser Entrada o Salida'}), 400
        if cantidad <= 0:
            return jsonify({'error': 'La cantidad debe ser mayor a 0'}), 400
        producto = execute_query("SELECT Stock FROM Productos WHERE ProductoID = ?", (id,))
        if not producto:
            return jsonify({'error': 'Producto no encontrado'}), 404
        stock_actual = producto[0]['Stock']
        if tipo == 'Entrada':
            nuevo_stock = stock_actual + cantidad
        else:
            if cantidad > stock_actual:
                return jsonify({'error': 'Stock insuficiente'}), 400
            nuevo_stock = stock_actual - cantidad
        execute_transaction([
            ("INSERT INTO MovimientosInventario (ProductoID, Tipo, Cantidad) VALUES (?, ?, ?)", (id, tipo, cantidad)),
            ("UPDATE Productos SET Stock = ? WHERE ProductoID = ?", (nuevo_stock, id))
        ])
        return jsonify({'mensaje': 'Movimiento registrado', 'stock_anterior': stock_actual, 'stock_nuevo': nuevo_stock}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500