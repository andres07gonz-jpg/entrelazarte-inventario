from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from database import get_db_connection, execute_query
from collections import defaultdict

ventas_bp = Blueprint('ventas', __name__)

@ventas_bp.route('/', methods=['POST'])
def registrar_venta():
    """Registrar una venta desde el carrito"""
    
    try:
        data = request.get_json()
        items = data.get('items', [])
        total = data.get('total')
        recibido = data.get('recibido')
        cambio = data.get('cambio')
        fecha = data.get('fecha')
        descripcion = data.get('descripcion', '')
        
        # Validaciones
        if not items or not isinstance(items, list) or len(items) == 0:
            return jsonify({'error': 'No hay productos en la venta'}), 400
        
        if not isinstance(total, (int, float)) or total <= 0:
            return jsonify({'error': 'Total inválido'}), 400
        
        if not isinstance(recibido, (int, float)) or recibido < total:
            return jsonify({'error': 'Dinero recibido insuficiente'}), 400
        
        # Usar transacción
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Insertar venta principal
            fecha_movimiento = fecha if fecha else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(
                """INSERT INTO Ventas (Fecha, Total, Recibido, Cambio, Descripcion)
                   VALUES (?, ?, ?, ?, ?)""",
                (fecha_movimiento, total, recibido, cambio, descripcion)
            )
            venta_id = cursor.lastrowid
            
            # Verificar stock y actualizar para cada producto
            for item in items:
                producto_id = item.get('ProductoID')
                cantidad = item.get('Cantidad')
                nombre = item.get('Nombre')
                precio = item.get('Precio')
                subtotal = precio * cantidad
                
                # Verificar stock actual
                cursor.execute(
                    'SELECT Stock, Nombre FROM Productos WHERE ProductoID = ?',
                    (producto_id,)
                )
                resultado = cursor.fetchone()
                
                if not resultado:
                    raise Exception(f'Producto {producto_id} no encontrado')
                
                stock_actual = resultado['Stock']
                nombre_producto = resultado['Nombre']
                
                if stock_actual < cantidad:
                    raise Exception(
                        f'Stock insuficiente para {nombre_producto}. '
                        f'Disponible: {stock_actual}, Solicitado: {cantidad}'
                    )
                
                # Insertar detalle de venta
                cursor.execute(
                    """INSERT INTO DetalleVentas 
                       (VentaID, ProductoID, NombreProducto, Cantidad, PrecioUnitario, Subtotal)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (venta_id, producto_id, nombre, cantidad, precio, subtotal)
                )
                
                # Actualizar stock (restar cantidad vendida)
                cursor.execute(
                    'UPDATE Productos SET Stock = Stock - ? WHERE ProductoID = ?',
                    (cantidad, producto_id)
                )
                
                # Registrar movimiento de inventario (Salida)
                cursor.execute(
                    """INSERT INTO MovimientosInventario (ProductoID, Tipo, Cantidad, Fecha)
                       VALUES (?, 'Salida', ?, ?)""",
                    (producto_id, cantidad, fecha_movimiento)
                )
            
            # La transacción se confirma automáticamente al salir del context manager
        
        # Devolver ticket con la misma estructura
        return jsonify({
            'ventaID': venta_id,
            'items': items,
            'total': total,
            'recibido': recibido,
            'cambio': cambio,
            'fecha': fecha if fecha else datetime.now().isoformat(),
            'message': 'Venta registrada exitosamente'
        }), 200
        
    except Exception as e:
        print(f"Error al registrar venta: {e}")
        return jsonify({'error': str(e)}), 500

@ventas_bp.route('/', methods=['GET'])
def get_ventas():
    """Obtener historial de ventas con paginación"""
    try:
        limite = request.args.get('limite', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        query = """
            SELECT 
                v.VentaID,
                v.Fecha,
                v.Total,
                v.Recibido,
                v.Cambio,
                v.Descripcion,
                COUNT(dv.DetalleID) as NumeroItems
            FROM Ventas v
            LEFT JOIN DetalleVentas dv ON v.VentaID = dv.VentaID
            GROUP BY v.VentaID
            ORDER BY v.Fecha DESC
            LIMIT ? OFFSET ?
        """
        ventas = execute_query(query, (limite, offset))
        
        # Obtener total de ventas
        total_query = "SELECT COUNT(*) as total FROM Ventas"
        total_result = execute_query(total_query)
        total_ventas = total_result[0]['total'] if total_result else 0
        
        return jsonify({
            'ventas': ventas,
            'total': total_ventas,
            'limite': limite,
            'offset': offset
        }), 200
        
    except Exception as e:
        print(f"Error al obtener ventas: {e}")
        return jsonify({'error': 'Error al obtener historial de ventas'}), 500

@ventas_bp.route('/<int:venta_id>', methods=['GET'])
def get_venta_detalle(venta_id):
    """Obtener detalle completo de una venta"""
    try:
        # Obtener venta principal
        venta_query = "SELECT * FROM Ventas WHERE VentaID = ?"
        venta = execute_query(venta_query, (venta_id,))
        
        if not venta:
            return jsonify({'error': 'Venta no encontrada'}), 404
        
        # Obtener items de la venta
        items_query = """
            SELECT * FROM DetalleVentas 
            WHERE VentaID = ?
            ORDER BY DetalleID
        """
        items = execute_query(items_query, (venta_id,))
        
        return jsonify({
            'venta': venta[0],
            'items': items
        }), 200
        
    except Exception as e:
        print(f"Error al obtener detalle de venta: {e}")
        return jsonify({'error': 'Error al obtener detalle de venta'}), 500

@ventas_bp.route('/estadisticas', methods=['GET'])
def get_estadisticas():
    """Obtener estadísticas de ventas por período"""
    try:
        periodo = request.args.get('periodo', 'mes')  # dia, semana, mes, año
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        
        # Calcular fechas si no se proporcionan
        if not fecha_inicio or not fecha_fin:
            fecha_fin = datetime.now()
            if periodo == 'dia':
                fecha_inicio = fecha_fin - timedelta(days=1)
            elif periodo == 'semana':
                fecha_inicio = fecha_fin - timedelta(days=7)
            elif periodo == 'mes':
                fecha_inicio = fecha_fin - timedelta(days=30)
            elif periodo == 'año':
                fecha_inicio = fecha_fin - timedelta(days=365)
            
            fecha_inicio = fecha_inicio.strftime('%Y-%m-%d 00:00:00')
            fecha_fin = fecha_fin.strftime('%Y-%m-%d 23:59:59')
        
        # Estadísticas generales
        stats_query = """
            SELECT 
                COUNT(*) as total_ventas,
                COALESCE(SUM(Total), 0) as ingresos_totales,
                COALESCE(AVG(Total), 0) as promedio_venta,
                COALESCE(MAX(Total), 0) as venta_maxima,
                COALESCE(MIN(Total), 0) as venta_minima
            FROM Ventas
            WHERE Fecha BETWEEN ? AND ?
        """
        stats = execute_query(stats_query, (fecha_inicio, fecha_fin))
        
        # Ventas por día
        ventas_diarias_query = """
            SELECT 
                DATE(Fecha) as fecha,
                COUNT(*) as num_ventas,
                SUM(Total) as total_dia
            FROM Ventas
            WHERE Fecha BETWEEN ? AND ?
            GROUP BY DATE(Fecha)
            ORDER BY DATE(Fecha)
        """
        ventas_diarias = execute_query(ventas_diarias_query, (fecha_inicio, fecha_fin))
        
        # Productos más vendidos
        productos_query = """
            SELECT 
                dv.NombreProducto,
                SUM(dv.Cantidad) as cantidad_vendida,
                SUM(dv.Subtotal) as ingresos_producto
            FROM DetalleVentas dv
            JOIN Ventas v ON dv.VentaID = v.VentaID
            WHERE v.Fecha BETWEEN ? AND ?
            GROUP BY dv.ProductoID, dv.NombreProducto
            ORDER BY cantidad_vendida DESC
            LIMIT 10
        """
        productos_top = execute_query(productos_query, (fecha_inicio, fecha_fin))
        
        return jsonify({
            'estadisticas': stats[0] if stats else {},
            'ventas_diarias': ventas_diarias,
            'productos_top': productos_top,
            'periodo': {
                'inicio': fecha_inicio,
                'fin': fecha_fin,
                'tipo': periodo
            }
        }), 200
        
    except Exception as e:
        print(f"Error al generar estadísticas: {e}")
        return jsonify({'error': 'Error al generar estadísticas'}), 500

@ventas_bp.route('/<int:venta_id>', methods=['DELETE'])
def eliminar_venta(venta_id):
    """Eliminar una venta (requiere contraseña de admin)"""
    import os
    
    # Verificar contraseña de admin
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    admin_pass = request.headers.get('x-admin-pass')
    
    if admin_pass != ADMIN_PASSWORD:
        return jsonify({'error': 'Contraseña de administrador incorrecta'}), 403
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar que la venta existe y obtener los detalles
            cursor.execute('SELECT * FROM Ventas WHERE VentaID = ?', (venta_id,))
            venta = cursor.fetchone()
            
            if not venta:
                return jsonify({'error': 'Venta no encontrada'}), 404
            
            # Obtener los productos de la venta para restaurar el stock
            cursor.execute("""
                SELECT ProductoID, Cantidad 
                FROM DetalleVentas 
                WHERE VentaID = ?
            """, (venta_id,))
            detalles = cursor.fetchall()
            
            # Restaurar el stock de cada producto
            for detalle in detalles:
                cursor.execute(
                    'UPDATE Productos SET Stock = Stock + ? WHERE ProductoID = ?',
                    (detalle['Cantidad'], detalle['ProductoID'])
                )
                
                # Registrar movimiento de entrada (devolución)
                cursor.execute(
                    """INSERT INTO MovimientosInventario (ProductoID, Tipo, Cantidad, Fecha)
                       VALUES (?, 'Entrada', ?, datetime('now'))""",
                    (detalle['ProductoID'], detalle['Cantidad'])
                )
            
            # Eliminar los detalles de la venta (esto eliminará automáticamente por CASCADE)
            cursor.execute('DELETE FROM DetalleVentas WHERE VentaID = ?', (venta_id,))
            
            # Eliminar la venta
            cursor.execute('DELETE FROM Ventas WHERE VentaID = ?', (venta_id,))
        
        return jsonify({
            'message': 'Venta eliminada exitosamente',
            'ventaID': venta_id
        }), 200
        
    except Exception as e:
        print(f"Error al eliminar venta: {e}")
        return jsonify({'error': str(e)}), 500