from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for, flash
from config_generator import NetworkConfigGenerator
from chat_agent import ChatAgent
import io
import json
import os
import random
import re
import sqlite3
from datetime import datetime
from functools import wraps

app = Flask(__name__)
generator = NetworkConfigGenerator()

# Load .env file manually (minimal dependency)
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

# Security Configuration
API_KEY = os.environ.get("ENGIA_API_KEY")

# Initialize Chat Agent with LLM Key
GEMINI_KEY = os.environ.get("GEMINI_API_KEY") 
chat_agent = ChatAgent(api_key=GEMINI_KEY)

# Authentication Config
# Ensure strong secret keys in production
app.secret_key = os.environ.get("SECRET_KEY", "change-this-to-a-secure-random-key-in-production")
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
# Default admin password should be changed on first deployment via Environment Variables
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "ChangeMeNow!")

def validate_password_strength(password):
    """
    Validates that the password meets strong security requirements:
    - At least 12 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one number
    - Contains at least one special character
    """
    if len(password) < 12:
        return False, "La contraseña debe tener al menos 12 caracteres."
    if not re.search(r"[A-Z]", password):
        return False, "La contraseña debe contener al menos una letra mayúscula."
    if not re.search(r"[a-z]", password):
        return False, "La contraseña debe contener al menos una letra minúscula."
    if not re.search(r"\d", password):
        return False, "La contraseña debe contener al menos un número."
    if not re.search(r"[ !@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        return False, "La contraseña debe contener al menos un carácter especial."
    return True, ""

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

from werkzeug.security import generate_password_hash, check_password_hash

# --- Audit Log System & User Management ---
DB_NAME = "audit.db"

def init_db():
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            # Audit Logs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT
                )
            ''')
            # Users Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_authorized INTEGER DEFAULT 0,
                    is_admin INTEGER DEFAULT 0,
                    created_at TEXT
                )
            ''')
            
            # Seed Admin User if table is empty
            cursor.execute('SELECT COUNT(*) FROM users')
            if cursor.fetchone()[0] == 0:
                print(f"Seeding admin user: {ADMIN_USER}")
                hashed_pw = generate_password_hash(ADMIN_PASSWORD)
                cursor.execute(
                    "INSERT INTO users (username, password_hash, is_authorized, is_admin, created_at) VALUES (?, ?, 1, 1, ?)",
                    (ADMIN_USER, hashed_pw, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                )
            conn.commit()
    except Exception as e:
        print(f"DB Init Error: {e}")

def log_action(user, action, details=None):
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('INSERT INTO logs (timestamp, user, action, details) VALUES (?, ?, ?, ?)',
                           (timestamp, user, action, str(details) if details else ""))
            conn.commit()
    except Exception as e:
        print(f"Logging Error: {e}")

# Initialize DB on startup
init_db()

def require_api_key(f):
    def decorated(*args, **kwargs):
        if API_KEY:
            if request.headers.get("X-API-Key") != API_KEY:
                return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not password:
            flash('Usuario y contraseña requeridos', 'error')
            return redirect(url_for('register'))
            
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return redirect(url_for('register'))

        # Enforce Strong Password Policy
        is_valid, msg = validate_password_strength(password)
        if not is_valid:
            flash(msg, 'error')
            return redirect(url_for('register'))
            
        try:
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                # Check if user exists
                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                if cursor.fetchone():
                    flash('El usuario ya existe', 'error')
                    return redirect(url_for('register'))
                
                # Create user
                hashed_pw = generate_password_hash(password)
                cursor.execute(
                    "INSERT INTO users (username, password_hash, is_authorized, created_at) VALUES (?, ?, 0, ?)",
                    (username, hashed_pw, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                )
                conn.commit()
                
                log_action(username, "REGISTER", "New user registered")
                flash('Cuenta creada exitosamente. Esperando aprobación del administrador.', 'success')
                return redirect(url_for('login'))
                
        except Exception as e:
            flash(f'Error registrando usuario: {e}', 'error')
            return redirect(url_for('register'))
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 1. Check Hardcoded Admin (Always Authorized)
        if username == ADMIN_USER and password == ADMIN_PASSWORD:
            session['user'] = username
            session['is_admin'] = True # Mark as super admin
            log_action(username, "LOGIN", "Admin logged in successfully")
            return redirect(url_for('index'))
            
        # 2. Check Database Users
        try:
            with sqlite3.connect(DB_NAME) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
                user = cursor.fetchone()
                
                if user and check_password_hash(user['password_hash'], password):
                    if user['is_authorized']:
                        session['user'] = username
                        session['is_admin'] = bool(user['is_admin'])
                        log_action(username, "LOGIN", "User logged in successfully")
                        return redirect(url_for('index'))
                    else:
                        log_action(username, "LOGIN_FAILED", "User not authorized")
                        flash('Tu cuenta está pendiente de aprobación por el administrador.', 'warning')
                        return render_template('login.html')
                        
                log_action(username or "unknown", "LOGIN_FAILED", "Invalid credentials")
                flash('Credenciales incorrectas', 'error')
                
        except Exception as e:
            flash(f'Error de sistema: {e}', 'error')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    user = session.get('user', 'unknown')
    log_action(user, "LOGOUT", "User logged out")
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/admin/logs')
@login_required
def view_logs():
    if not session.get('is_admin'):
        flash('Acceso denegado', 'error')
        return redirect(url_for('index'))
        
    try:
        with sqlite3.connect(DB_NAME) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM logs ORDER BY id DESC LIMIT 100')
            logs = cursor.fetchall()
        return render_template('logs.html', logs=logs)
    except Exception as e:
        return f"Error accessing logs: {e}"

@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
def manage_users():
    if not session.get('is_admin'):
        flash('Acceso denegado', 'error')
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        action = request.form.get('action')
        user_id = request.form.get('user_id')
        
        try:
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                
                if action == 'approve':
                    cursor.execute("UPDATE users SET is_authorized = 1 WHERE id = ?", (user_id,))
                    log_action(session.get('user'), "APPROVE_USER", f"Approved user ID {user_id}")
                    flash('Usuario autorizado', 'success')
                    
                elif action == 'delete':
                    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                    log_action(session.get('user'), "DELETE_USER", f"Deleted user ID {user_id}")
                    flash('Usuario eliminado', 'success')
                    
                conn.commit()
        except Exception as e:
            flash(f'Error: {e}', 'error')
            
    # GET: List users
    try:
        with sqlite3.connect(DB_NAME) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
            users = cursor.fetchall()
        return render_template('users.html', users=users)
    except Exception as e:
        return f"Error accessing users: {e}"

@app.route('/')
@login_required
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
@login_required
@require_api_key
def generate_config():
    """Genera configuración"""
    try:
        params = request.json
        if not params:
            log_action(session.get('user', 'api'), "GENERATE_ERROR", "No parameters received")
            return jsonify({'error': 'No se recibieron parámetros'}), 400
        
        result = generator.generate(params)
        
        if result.get('success'):
            log_action(session.get('user', 'api'), "GENERATE_CONFIG", f"Generated config for {params.get('device', {}).get('vendor', 'unknown')}")
        else:
            error_msg = result.get('error')
            if not error_msg and result.get('errors'):
                error_msg = "; ".join(result['errors'])
            log_action(session.get('user', 'api'), "GENERATE_ERROR", f"Config generation failed: {error_msg}")
            
        return jsonify(result)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        log_action(session.get('user', 'api'), "GENERATE_EXCEPTION", str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/download', methods=['POST'])
@login_required
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
@login_required
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
@login_required
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
@login_required
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

@app.route('/api/magic-fill', methods=['POST'])
@login_required
@require_api_key
def magic_fill():
    """Genera JSON de configuración desde texto natural"""
    try:
        data = request.json
        text = data.get('text')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400

        config_json = chat_agent.extract_config_from_text(text)
        
        if "error" in config_json:
             log_action(session.get('user', 'api'), "MAGIC_FILL_ERROR", config_json["error"])
             return jsonify({'error': config_json["error"]}), 500

        log_action(session.get('user', 'api'), "MAGIC_FILL", f"Processed prompt: {text[:50]}...")
        return jsonify({'success': True, 'config': config_json})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
@login_required
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


