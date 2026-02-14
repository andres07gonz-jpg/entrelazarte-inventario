import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='.', template_folder='.')
app.url_map.strict_slashes = False
CORS(app)

from routes.productos import productos_bp
from routes.ventas import ventas_bp
app.register_blueprint(productos_bp, url_prefix='/productos')
app.register_blueprint(ventas_bp, url_prefix='/ventas')

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

try:
    from database import test_connection, init_database
    test_connection()
    init_database()
    print("Base de datos lista")
except Exception as e:
    print(f"Error BD: {e}")

if __name__ == '__main__':
    port = int(os.getenv('PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=False)