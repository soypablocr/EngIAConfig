from flask import Flask, request, jsonify, render_template, send_file
from config_generator import NetworkConfigGenerator
import io
import json
import os

app = Flask(__name__)
generator = NetworkConfigGenerator()

# Minimal Security
API_KEY = os.environ.get("ENGIA_API_KEY")

def require_api_key(f):
    def decorated(*args, **kwargs):
        if API_KEY:
            if request.headers.get("X-API-Key") != API_KEY:
                return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

@app.route('/')
def index():
    """Página principal con formulario"""
    return render_template('index.html')

@app.route('/api/catalog', methods=['GET'])
def get_catalog():
    """Retorna el catálogo completo de vendors, modelos y firmwares"""
    return jsonify(generator.get_catalog())

@app.route('/api/vendors', methods=['GET'])
def get_vendors():
    """Lista de vendors soportados"""
    return jsonify({
        'vendors': generator.get_supported_vendors()
    })

@app.route('/api/generate', methods=['POST'])
@require_api_key
def generate_config():
    """Genera configuración"""
    try:
        params = request.json
        if not params:
            return jsonify({'error': 'No se recibieron parámetros'}), 400
        
        result = generator.generate(params)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download', methods=['POST'])
@require_api_key
def download_config():
    """Descarga configuración como archivo"""
    try:
        params = request.json
        result = generator.generate(params)
        
        if not result.get('success'):
            return jsonify(result), 400
        
        filename = result.get('filename', 'config.txt')
        mimetype = result.get('mimetype', 'text/plain')
        
        # Crear archivo en memoria
        content = result['content']
        if result['format'] == 'json':
            content = json.dumps(content, indent=2)
        
        buffer = io.BytesIO()
        buffer.write(str(content).encode('utf-8'))
        buffer.seek(0)
        
        response = send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/validate', methods=['POST'])
@require_api_key
def validate_params():
    """Valida parámetros sin generar config"""
    try:
        params = request.json
        if not params:
            return jsonify({'error': 'No se recibieron parámetros'}), 400
        
        valid, errors, warnings = generator.validate_params(params)
        return jsonify({
            'valid': valid,
            'errors': errors,
            'warnings': warnings
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Limit max request size to 1MB
    app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024
    app.run(debug=True, host='0.0.0.0', port=5005)


