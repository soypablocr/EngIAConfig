# EngIA Config - Generador de Configuraciones de Red Asistido por IA

## 🌟 Descripción General
**EngIA Config** es una plataforma avanzada de aprovisionamiento de redes que combina la automatización tradicional basada en plantillas con el poder de la Inteligencia Artificial Generativa (Google Gemini). 

Su objetivo principal es simplificar y acelerar la creación de "Day-0 configurations" para dispositivos de red empresariales (SD-WAN, Firewalls, Switches), reduciendo errores humanos y tiempos de implementación.

## 🚀 Características Principales

### 🧠 Magic Fill (AI-Powered)
Utiliza modelos de lenguaje (LLM) para interpretar instrucciones en lenguaje natural y completar automáticamente formularios técnicos complejos.
*   *Ejemplo:* "Configura un Fortigate para una sede en Madrid con 2 WANs (1Gbps y 500Mbps) y una VLAN de invitados."
*   **Modelo:** Google Gemini (1.5 Flash / Flash Latest).

### 📦 Soporte Multi-Vendor
Genera configuraciones específicas para múltiples fabricantes líderes del mercado:
*   **Fortinet:** FortiGate (SD-WAN, Policies, Security Profiles).
*   **Cisco Meraki:** MX Series (básico).
*   **Velocloud (VMware SD-WAN):** Edge configuration.
*   **Bigleaf:** SD-WAN optimization config.
*   **CATO Networks:** Socket configuration.

### 🔒 Seguridad y Gestión de Usuarios
*   **Autenticación Robusta:** Registro de usuarios con hash de contraseñas (SHA-256).
*   **Autorización de Administrador:** Los nuevos registros quedan en estado "Pendiente" hasta ser aprobados por un administrador.
*   **Persistencia:** Base de datos SQLite (`audit.db`) para almacenar usuarios y registros de auditoría de forma permanente.
*   **Gestión de Secretos:** Manejo seguro de API Keys mediante variables de entorno y archivos `.env`.

### 📜 Auditoría y Trazabilidad (Logs)
Sistema completo de logs que registra quién generó qué configuración, cuándo y con qué parámetros.
*   **Admin Dashboard:** Panel exclusivo para visualizar logs de actividad y gestionar usuarios.

### 📄 Salidas Flexibles
*   **Texto Plano (.txt):** Scripts CLI listos para copiar y pegar (ej. CLI de FortiOS).
*   **Archivos ZIP:** Paquetes descargables con todos los archivos generados.
*   **Documentación PDF:** Resumen ejecutivo de la configuración generada para entregar al cliente.

## 🛠 Arquitectura del Sistema

*   **Backend:** Python 3.13 con Flask.
*   **Frontend:** HTML5, CSS3 (Modern UI con Glassmorphism), JavaScript (Vanilla).
*   **Base de Datos:** SQLite 3.
*   **Motor de Plantillas:** Jinja2 para la generación determinista de configs.
*   **Integración IA:** `google-genai` (SDK de Google Gemini).

## 📋 Requisitos Previos

*   **Python 3.10+** instalado.
*   **Google Gemini API Key** (Obtener en [Google AI Studio](https://aistudio.google.com/)).

## ⚙️ Instalación y Uso

1.  **Clonar el repositorio:**
    ```bash
    git clone https://github.com/soypablocr/EngIAConfig.git
    cd EngIAConfig
    ```

2.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configurar Variables de Entorno:**
    Crea un archivo `.env` en la raíz del proyecto o configura las variables en tu terminal:
    ```powershell
    # .env
    GEMINI_API_KEY=tu_api_key_aqui
    ENGIA_API_KEY=devkey  # (Opcional, para funciones internas)
    ADMIN_USER=admin      # Usuario administrador por defecto
    ADMIN_PASSWORD=admin  # Contraseña inicial (¡Cambiar en producción!)
    SECRET_KEY=clave_secreta_flask
    ```

4.  **Ejecutar la aplicación:**
    ```bash
    python app.py
    ```

5.  **Acceder:**
    Abre tu navegador en `http://localhost:5005`.

## 🤖 Contexto y Gobernanza de IA (SG-IA)
Este proyecto opera bajo un **Sistema de Gestión de IA (SG-IA)** para asegurar un uso ético, transparente y seguro de la inteligencia artificial.
Para más detalles sobre el alcance, partes interesadas y políticas, consulta el archivo: [AI-Scope-Statement.md](./AI-Scope-Statement.md).

---
**Desarrollado por el Equipo EngIA Config** | *Automating the Future of Networks*
