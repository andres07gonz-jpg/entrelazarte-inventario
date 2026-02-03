from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
from dotenv import load_dotenv
from routes.productos import productos_bp
from routes.ventas import ventas_bp
from database import test_connection, init_database

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__, static_folder='.', template_folder='.')
CORS(app)

# Registrar blueprints (rutas)
app.register_blueprint(productos_bp, url_prefix='/productos')
app.register_blueprint(ventas_bp, url_prefix='/ventas')

# Servir archivos estáticos (HTML)
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

# Endpoint de salud
@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'inventario-api', 'database': 'SQLite'})

if __name__ == '__main__':
    # Probar conexión a la base de datos
    test_connection()
    
    # Iniciar servidor
    port = int(os.getenv('PORT', 3000))
    
    # En producción (Railway) usa 0.0.0.0, en local usa localhost
    host = '0.0.0.0' if os.getenv('RAILWAY_ENVIRONMENT') else '127.0.0.1'
    debug = not bool(os.getenv('RAILWAY_ENVIRONMENT'))
    
    print(f"\n🚀 Servidor iniciado en http://{host}:{port}")
    print(f"📊 Base de datos: SQLite (inventario.db)")
    print(f"⏹️  Presiona CTRL+C para detener el servidor\n")
    
    app.run(debug=debug, host=host, port=port)
