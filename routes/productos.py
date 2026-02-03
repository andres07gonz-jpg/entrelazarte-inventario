from flask import Blueprint, jsonify, request
import os
from database import execute_query, execute_transaction

productos_bp = Blueprint('productos', __name__)

# Contraseña de administrador
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

def check_admin_password():
    """Verificar contraseña de administrador desde headers"""
    admin_pass = request.headers.get('x-admin-pass')
    return admin_pass == ADMIN_PASSWORD

# ===== PRODUCTOS =====

@productos_bp.route('/', methods=['GET'])
def get_productos():
    """Obtener todos los productos"""
    try:
        query = """
            SELECT 
                p.ProductoID,
                p.Nombre,
                p.Precio,
                p.Stock,
                p.CategoriaID,
                p.ProveedorID,
                p.FechaAlta
            FROM Productos p
            ORDER BY p.Nombre
        """
        productos = execute_query(query)
        return jsonify(productos), 200
    except Exception as e:
        print(f"Error al obtener productos: {e}")
        return jsonify({'error': 'Error al obtener productos'}), 500

@productos_bp.route('/<int:id>', methods=['GET'])
def get_producto(id):
    """Obtener un producto específico"""
    try:
        query = "SELECT * FROM Productos WHERE ProductoID = ?"
        productos = execute_query(query, (id,))
        
        if not productos:
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        return jsonify(productos[0]), 200
    except Exception as e:
        print(f"Error al obtener producto: {e}")
        return jsonify({'error': 'Error al obtener producto'}), 500

@productos_bp.route('/', methods=['POST'])
def create_producto():
    """Crear nuevo producto"""
    try:
        data = request.get_json()
        nombre = data.get('Nombre', '').strip()
        
        if not nombre:
            return jsonify({'error': 'El nombre es obligatorio'}), 400
        
        precio = data.get('Precio', 0)
        stock = data.get('Stock', 0)
        categoria_id = data.get('CategoriaID')
        proveedor_id = data.get('ProveedorID')
        fecha_alta = data.get('FechaAlta')
        
        query = """
            INSERT INTO Productos (Nombre, Precio, Stock, CategoriaID, ProveedorID, FechaAlta)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (nombre, precio, stock, categoria_id, proveedor_id, fecha_alta)
        
        producto_id = execute_query(query, params, fetch=False)
        
        return jsonify({
            'ProductoID': producto_id,
            'Nombre': nombre,
            'Precio': precio,
            'Stock': stock,
            'message': 'Producto creado exitosamente'
        }), 201
        
    except Exception as e:
        print(f"Error al crear producto: {e}")
        return jsonify({'error': 'Error al crear producto'}), 500

@productos_bp.route('/<int:id>', methods=['PUT'])
def update_producto(id):
    """Actualizar producto (requiere admin)"""
    if not check_admin_password():
        return jsonify({'error': 'Contraseña de administrador incorrecta'}), 403
    
    try:
        data = request.get_json()
        
        # Construir query dinámicamente solo con campos presentes
        fields = []
        values = []
        
        if 'Nombre' in data:
            fields.append('Nombre = ?')
            values.append(data['Nombre'])
        if 'Precio' in data:
            fields.append('Precio = ?')
            values.append(data['Precio'])
        if 'Stock' in data:
            fields.append('Stock = ?')
            values.append(data['Stock'])
        if 'CategoriaID' in data:
            fields.append('CategoriaID = ?')
            values.append(data['CategoriaID'])
        if 'ProveedorID' in data:
            fields.append('ProveedorID = ?')
            values.append(data['ProveedorID'])
        
        if not fields:
            return jsonify({'error': 'No hay campos para actualizar'}), 400
        
        values.append(id)
        query = f"UPDATE Productos SET {', '.join(fields)} WHERE ProductoID = ?"
        
        affected = execute_query(query, tuple(values), fetch=False)
        
        if affected == 0:
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        # Devolver producto actualizado
        updated = execute_query("SELECT * FROM Productos WHERE ProductoID = ?", (id,))
        
        return jsonify(updated[0]), 200
        
    except Exception as e:
        print(f"Error al actualizar producto: {e}")
        return jsonify({'error': 'Error al actualizar producto'}), 500

@productos_bp.route('/<int:id>', methods=['DELETE'])
def delete_producto(id):
    """Eliminar producto (requiere admin)"""
    if not check_admin_password():
        return jsonify({'error': 'Contraseña de administrador incorrecta'}), 403
    
    try:
        query = "DELETE FROM Productos WHERE ProductoID = ?"
        affected = execute_query(query, (id,), fetch=False)
        
        if affected == 0:
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        return jsonify({'message': 'Producto eliminado exitosamente'}), 200
        
    except Exception as e:
        print(f"Error al eliminar producto: {e}")
        return jsonify({'error': 'Error al eliminar producto'}), 500

# ===== FECHAS DE PRODUCTOS =====

@productos_bp.route('/<int:id>/fechas', methods=['GET'])
def get_fechas(id):
    """Obtener fechas de un producto"""
    try:
        query = """
            SELECT FechaID, FechaAlta 
            FROM FechasProductos 
            WHERE ProductoID = ?
            ORDER BY FechaAlta DESC
        """
        fechas = execute_query(query, (id,))
        return jsonify(fechas), 200
    except Exception as e:
        print(f"Error al obtener fechas: {e}")
        # Si la tabla no existe, devolver array vacío
        return jsonify([]), 200

@productos_bp.route('/<int:id>/fechas', methods=['POST'])
def add_fecha(id):
    """Agregar fecha (requiere admin)"""
    if not check_admin_password():
        return jsonify({'error': 'Contraseña de administrador incorrecta'}), 403
    
    try:
        data = request.get_json()
        fecha_alta = data.get('FechaAlta')
        
        if not fecha_alta:
            return jsonify({'error': 'La fecha es obligatoria'}), 400
        
        query = """
            INSERT INTO FechasProductos (ProductoID, FechaAlta)
            VALUES (?, ?)
        """
        fecha_id = execute_query(query, (id, fecha_alta), fetch=False)
        
        return jsonify({
            'FechaID': fecha_id,
            'ProductoID': id,
            'FechaAlta': fecha_alta,
            'message': 'Fecha agregada exitosamente'
        }), 201
        
    except Exception as e:
        print(f"Error al agregar fecha: {e}")
        return jsonify({'error': 'Error al agregar fecha'}), 500

@productos_bp.route('/<int:id>/fechas/<int:fecha_id>', methods=['DELETE'])
def delete_fecha(id, fecha_id):
    """Eliminar fecha (requiere admin)"""
    if not check_admin_password():
        return jsonify({'error': 'Contraseña de administrador incorrecta'}), 403
    
    try:
        query = "DELETE FROM FechasProductos WHERE FechaID = ? AND ProductoID = ?"
        affected = execute_query(query, (fecha_id, id), fetch=False)
        
        if affected == 0:
            return jsonify({'error': 'Fecha no encontrada'}), 404
        
        return jsonify({'message': 'Fecha eliminada exitosamente'}), 200
        
    except Exception as e:
        print(f"Error al eliminar fecha: {e}")
        return jsonify({'error': 'Error al eliminar fecha'}), 500