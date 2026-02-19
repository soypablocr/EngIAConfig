# Declaración de Alcance del SG-IA (AI System Scope Statement)

## 0. Propósito
Este documento define el alcance, contexto y partes interesadas del Sistema de Gestión de Inteligencia Artificial (SG-IA) para el proyecto **EngIA Config** (Generador de Configuraciones de Red Asistido por IA).

## 4. Contexto de la Organización

### 4.1 Comprensión de la Organización y su Contexto
**EngIA Config** es una organización ágil dedicada al desarrollo de software para la automatización de infraestructura de redes. La principal propuesta de valor es reducir el tiempo de configuración y minimizar errores humanos mediante el uso de Inteligencia Artificial Generativa.

**Factores Internos Relevantes:**
- Cultura de desarrollo rápido e innovador.
- Dependencia de modelos de lenguaje grandes (LLMs) de terceros (Google Gemini).
- Compromiso con la seguridad de la información (no almacenamiento de datos sensibles en prompts).

**Factores Externos Relevantes:**
- Evolución rápida de las tecnologías de IA y cambios en las APIs de proveedores.
- Regulaciones emergentes sobre el uso ético y transparente de la IA (EU AI Act, GDPR).
- Expectativas de alta disponibilidad y precisión por parte de los clientes empresariales.

### 4.2 Necesidades y Expectativas de las Partes Interesadas

| Parte Interesada (Stakeholder) | Rol | Necesidades y Expectativas |
| :--- | :--- | :--- |
| **Equipo de Desarrollo** | Responsable del Sistema | Eficiencia en el desarrollo, mantenibilidad del código, acceso confiable a APIs de IA. |
| **Ingenieros de Red (Usuarios Finales)** | Operadores del Sistema | Precisión técnica en las configuraciones generadas, facilidad de uso (UX/UI), respuesta rápida. |
| **Clientes Finales (Empresas)** | Beneficiarios | Redes seguras y funcionales, protección de su topología de red y secretos. |
| **Proveedores de IA (Google)** | Socio Tecnológico | Cumplimiento de términos de servicio, uso responsable de la API. |
| **Reguladores** | Autoridad de Control | Transparencia en el uso de IA, protección de datos personales, no discriminación. |

### 4.3 Alcance del Sistema de Gestión de IA
El SG-IA aplica específicamente al **módulo de generación asistida por IA ("Magic Fill")** dentro de la aplicación EngIA Config.

**Límites del Alcance:**
- **Incluye:**
    - El diseño, desarrollo y despliegue de los prompts utilizados para interactuar con el LLM.
    - La integración técnica con la API de Google Gemini.
    - La validación y verificación de las respuestas generadas por la IA antes de presentarlas al usuario.
    - La gestión de riesgos relacionados con alucinaciones de la IA y fugas de datos a través de los prompts.
- **Excluye:**
    - El entrenamiento o fine-tuning de modelos fundacionales (se utiliza el modelo pre-entrenado "as-is").
    - Los componentes deterministas del generador de configuraciones que no utilizan IA (validadores estáticos, plantillas Jinja2).
    - La infraestructura física de red de los clientes.

### 4.4 Sistema de Gestión de IA
EngIA Config establece, implementa, mantiene y mejora continuamente un sistema de gestión para la IA, incluidos los procesos necesarios y sus interacciones, de acuerdo con los principios de transparencia, explicabilidad y seguridad.
