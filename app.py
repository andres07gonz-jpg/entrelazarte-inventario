from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Cargar variables de entorno PRIMERO
load_dotenv()

# Crear la app ANTES de cualquier otra cosa
app = Flask(__name__, static_folder='.', template_folder='.')
CORS(app)

# Registrar blueprints
from routes.productos import productos_bp
from routes.ventas import ventas_bp
app.register_blueprint(productos_bp, url_prefix='/productos')
app.register_blueprint(ventas_bp, url_prefix='/ventas')

# Rutas estáticas
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'inventario-api'})

# Inicializar base de datos DESPUÉS de crear la app
from database import test_connection, init_database
try:
    print("Inicializando base de datos...")
    test_connection()
    init_database()
    print("Base de datos lista")
except Exception as e:
    print(f"Error inicializando base de datos: {e}")

if __name__ == '__main__':
    port = int(os.getenv('PORT', 3000))
    app.run(debug=False, host='0.0.0.0', port=port)