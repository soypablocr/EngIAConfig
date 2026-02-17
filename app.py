from flask import Flask, request, jsonify, render_template, send_file
from config_generator import NetworkConfigGenerator
from chat_agent import ChatAgent
import io
import json
import os

app = Flask(__name__)
generator = NetworkConfigGenerator()
# Minimal Security
API_KEY = os.environ.get("ENGIA_API_KEY")

# Initialize Chat Agent with LLM Key
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyBXztlBxZaOJz_MAK7erf20gYi0mEaiv-g") # Fallback to provided key if env var not set
chat_agent = ChatAgent(api_key=GEMINI_KEY)

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
        import traceback
        traceback.print_exc()
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
        import traceback
        traceback.print_exc()
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
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/push/meraki', methods=['POST'])
@require_api_key
def push_meraki():
    """Genera y empuja configuración a Meraki Dashboard"""
    try:
        data = request.json
        params = data.get('params')
        api_key = data.get('meraki_api_key')
        network_id = data.get('network_id')
        
        if not all([params, api_key, network_id]):
            return jsonify({'error': 'Faltan parámetros (params, meraki_api_key, network_id)'}), 400
            
        # 1. Generar la configuración
        result = generator.generate(params)
        if not result.get('success'):
            return jsonify(result), 400
            
        if result.get('format') != 'json':
            return jsonify({'error': 'La configuración generada no es de formato JSON (Meraki expected)'}), 400
            
        # 2. Empujar a la API
        from integrations.meraki_api import MerakiIntegration
        integration = MerakiIntegration(api_key)
        push_result = integration.push_configuration(network_id, result['content'])
        
        return jsonify({
            'success': push_result['success'],
            'push_details': push_result.get('details', []),
            'error': push_result.get('error'),
            'config_generated': True
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/push/cato', methods=['POST'])
@require_api_key
def push_cato():
    """Genera y empuja configuración a Cato Networks (GraphQL)"""
    try:
        data = request.json
        params = data.get('params')
        api_key = data.get('cato_api_key')
        account_id = data.get('account_id')
        
        if not all([params, api_key, account_id]):
            return jsonify({'error': 'Faltan parámetros (params, cato_api_key, account_id)'}), 400
            
        # 1. Generar la configuración
        result = generator.generate(params)
        if not result.get('success'):
            return jsonify(result), 400
            
        if result.get('format') != 'graphql':
            return jsonify({'error': 'La configuración generada no es de formato GraphQL (Cato expected)'}), 400
            
        # 2. Empujar a la API
        from integrations.cato_api import CatoIntegration
        integration = CatoIntegration(api_key, account_id)
        push_result = integration.push_site_configuration(result['content'])
        
        return jsonify({
            'success': push_result['success'],
            'push_details': push_result.get('details', []),
            'error': push_result.get('error'),
            'config_generated': True
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint para el chatbot"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        message = data.get('message')
        context = data.get('context', {})
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400

        response = chat_agent.get_response(message, context)
        return jsonify({'response': response})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Limit max request size to 1MB
    app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024
    app.run(debug=True, host='0.0.0.0', port=5005)


