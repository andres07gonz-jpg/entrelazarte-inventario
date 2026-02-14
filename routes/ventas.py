from flask import Blueprint, jsonify, request
from database import execute_query, execute_transaction
from datetime import datetime

ventas_bp = Blueprint('ventas', __name__)

@ventas_bp.route('', methods=['POST'])
@ventas_bp.route('/', methods=['POST'])
def registrar_venta():
    try:
        data = request.json
        items = data.get('items', [])
        if not items:
            return jsonify({'error': 'Debe haber al menos un producto'}), 400

        total = float(data.get('total', 0))
        recibido = float(data.get('recibido', 0))
        cambio = float(data.get('cambio', 0))
        fecha = data.get('fecha', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        descripcion = data.get('descripcion', '')

        for item in items:
            producto_id = item.get('ProductoID')
            cantidad = item.get('Cantidad', 0)
            if not producto_id or cantidad <= 0:
                return jsonify({'error': f'Datos invalidos para producto {item.get("Nombre", "desconocido")}'}), 400
            producto = execute_query("SELECT Stock, Nombre FROM Productos WHERE ProductoID = ?", (producto_id,))
            if not producto:
                return jsonify({'error': f'Producto ID {producto_id} no encontrado'}), 404
            if producto[0]['Stock'] < cantidad:
                return jsonify({'error': f'Stock insuficiente para {producto[0]["Nombre"]}'}), 400

        venta_id = execute_query(
            "INSERT INTO Ventas (Fecha, Total, Recibido, Cambio, Descripcion) VALUES (?, ?, ?, ?, ?)",
            (fecha, total, recibido, cambio, descripcion), fetch=False
        )

        operations = []
        for item in items:
            producto_id = item['ProductoID']
            nombre = item.get('Nombre', '')
            cantidad = item['Cantidad']
            precio_unitario = float(item.get('Precio', 0))
            subtotal = precio_unitario * cantidad
            operations.append((
                "INSERT INTO DetalleVentas (VentaID, ProductoID, NombreProducto, Cantidad, PrecioUnitario, Subtotal) VALUES (?, ?, ?, ?, ?, ?)",
                (venta_id, producto_id, nombre, cantidad, precio_unitario, subtotal)
            ))
            operations.append(("UPDATE Productos SET Stock = Stock - ? WHERE ProductoID = ?", (cantidad, producto_id)))
            operations.append(("INSERT INTO MovimientosInventario (ProductoID, Tipo, Cantidad) VALUES (?, 'Salida', ?)", (producto_id, cantidad)))

        execute_transaction(operations)
        return jsonify({'mensaje': 'Venta registrada exitosamente', 'VentaID': venta_id, 'total': total, 'cambio': cambio}), 201
    except Exception as e:
        print(f"Error registrar_venta: {e}")
        return jsonify({'error': str(e)}), 500

@ventas_bp.route('', methods=['GET'])
@ventas_bp.route('/', methods=['GET'])
def obtener_ventas():
    try:
        limite = request.args.get('limite', 50, type=int)
        query = """
            SELECT v.VentaID, v.Fecha, v.Total, v.Recibido, v.Cambio, v.Descripcion,
                COUNT(dv.DetalleID) as CantidadItems
            FROM Ventas v
            LEFT JOIN DetalleVentas dv ON v.VentaID = dv.VentaID
            GROUP BY v.VentaID, v.Fecha, v.Total, v.Recibido, v.Cambio, v.Descripcion
            ORDER BY v.Fecha DESC
            LIMIT ?
        """
        ventas = execute_query(query, (limite,))
        return jsonify(ventas), 200
    except Exception as e:
        print(f"Error obtener_ventas: {e}")
        return jsonify({'error': str(e)}), 500

@ventas_bp.route('/estadisticas', methods=['GET'])
def estadisticas():
    try:
        periodo = request.args.get('periodo', 'mes')
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')

        if not fecha_inicio or not fecha_fin:
            now = datetime.now()
            fecha_inicio = now.replace(day=1).strftime('%Y-%m-%d 00:00:00')
            fecha_fin = now.strftime('%Y-%m-%d 23:59:59')

        query_resumen = """
            SELECT 
                COUNT(v.VentaID) as total_ventas,
                COALESCE(SUM(v.Total), 0) as ingresos_totales,
                COALESCE(AVG(v.Total), 0) as promedio_venta,
                COALESCE(SUM(dv.Cantidad), 0) as productos_vendidos
            FROM Ventas v
            LEFT JOIN DetalleVentas dv ON v.VentaID = dv.VentaID
            WHERE v.Fecha BETWEEN ? AND ?
        """
        resumen = execute_query(query_resumen, (fecha_inicio, fecha_fin))

        query_por_dia = """
            SELECT 
                DATE(v.Fecha) as fecha,
                COUNT(v.VentaID) as ventas,
                COALESCE(SUM(v.Total), 0) as ingresos
            FROM Ventas v
            WHERE v.Fecha BETWEEN ? AND ?
            GROUP BY DATE(v.Fecha)
            ORDER BY fecha ASC
        """
        por_dia = execute_query(query_por_dia, (fecha_inicio, fecha_fin))

        query_productos = """
            SELECT 
                p.Nombre as nombre,
                COALESCE(SUM(dv.Cantidad), 0) as cantidad_vendida,
                COALESCE(SUM(dv.Subtotal), 0) as ingresos
            FROM DetalleVentas dv
            JOIN Productos p ON dv.ProductoID = p.ProductoID
            JOIN Ventas v ON dv.VentaID = v.VentaID
            WHERE v.Fecha BETWEEN ? AND ?
            GROUP BY p.ProductoID, p.Nombre
            ORDER BY cantidad_vendida DESC
            LIMIT 10
        """
        productos_top = execute_query(query_productos, (fecha_inicio, fecha_fin))

        estadisticas_data = resumen[0] if resumen else {
            'total_ventas': 0, 'ingresos_totales': 0,
            'promedio_venta': 0, 'productos_vendidos': 0
        }

        return jsonify({
            'estadisticas': estadisticas_data,
            'por_dia': por_dia,
            'productos_top': productos_top
        }), 200
    except Exception as e:
        print(f"Error estadisticas: {e}")
        return jsonify({'error': str(e)}), 500

@ventas_bp.route('/comparativa', methods=['GET'])
def comparativa():
    try:
        tipo = request.args.get('tipo', 'mensual')
        now = datetime.now()

        if tipo == 'mensual':
            query = """
                SELECT 
                    TO_CHAR(v.Fecha, 'YYYY-MM') as periodo,
                    COUNT(v.VentaID) as total_ventas,
                    COALESCE(SUM(v.Total), 0) as total_monto
                FROM Ventas v
                GROUP BY TO_CHAR(v.Fecha, 'YYYY-MM')
                ORDER BY periodo DESC
                LIMIT 12
            """
        else:
            query = """
                SELECT 
                    TO_CHAR(v.Fecha, 'IYYY-IW') as periodo,
                    COUNT(v.VentaID) as total_ventas,
                    COALESCE(SUM(v.Total), 0) as total_monto
                FROM Ventas v
                GROUP BY TO_CHAR(v.Fecha, 'IYYY-IW')
                ORDER BY periodo DESC
                LIMIT 12
            """
        comparativa_data = execute_query(query)
        return jsonify(comparativa_data), 200
    except Exception as e:
        print(f"Error comparativa: {e}")
        return jsonify([]), 200

@ventas_bp.route('/<int:id>', methods=['GET'])
def obtener_venta_detalle(id):
    try:
        venta = execute_query("SELECT VentaID, Fecha, Total, Recibido, Cambio, Descripcion FROM Ventas WHERE VentaID = ?", (id,))
        if not venta:
            return jsonify({'error': 'Venta no encontrada'}), 404
        items = execute_query("SELECT DetalleID, ProductoID, NombreProducto, Cantidad, PrecioUnitario, Subtotal FROM DetalleVentas WHERE VentaID = ?", (id,))
        resultado = venta[0]
        resultado['items'] = items
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ventas_bp.route('/<int:id>', methods=['DELETE'])
def eliminar_venta(id):
    try:
        filas = execute_query("DELETE FROM Ventas WHERE VentaID = ?", (id,), fetch=False)
        if filas == 0:
            return jsonify({'error': 'Venta no encontrada'}), 404
        return jsonify({'mensaje': 'Venta eliminada exitosamente'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500