from flask import Flask, request, jsonify, render_template, send_file
from config_generator import NetworkConfigGenerator
import io
import json

app = Flask(__name__)
generator = NetworkConfigGenerator()

@app.route('/')
def index():
    """Página principal con formulario"""
    return render_template('index.html')

@app.route('/api/vendors', methods=['GET'])
def get_vendors():
    """Lista de vendors soportados"""
    return jsonify({
        'vendors': generator.get_supported_vendors()
    })

@app.route('/api/models/<vendor>', methods=['GET'])
def get_models(vendor):
    """Lista de modelos para un vendor"""
    models = generator.get_supported_models(vendor)
    if models:
        return jsonify({'vendor': vendor, 'models': models})
    return jsonify({'error': f'Vendor {vendor} no encontrado'}), 404

@app.route('/api/generate', methods=['POST'])
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
def download_config():
    """Descarga configuración como archivo"""
    try:
        params = request.json
        result = generator.generate(params)
        
        if not result['success']:
            return jsonify(result), 400
        
        # Determinar extensión según vendor
        extensions = {
            'fortinet': '.conf',
            'meraki': '.json',
            'velocloud': '.json',
            'bigleaf': '.json',
            'cato': '.json'
        }
        ext = extensions.get(result['vendor'], '.txt')
        filename = f"{result['site_name']}_{result['vendor']}{ext}"
        
        # Crear archivo en memoria
        buffer = io.BytesIO()
        buffer.write(result['config'].encode('utf-8'))
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='text/plain'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/validate', methods=['POST'])
def validate_params():
    """Valida parámetros sin generar config"""
    try:
        params = request.json
        if not params:
            return jsonify({'error': 'No se recibieron parámetros'}), 400
        
        is_valid, errors, warnings = generator.validator.validate_all(params)
        return jsonify({
            'valid': is_valid,
            'errors': errors,
            'warnings': warnings
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
