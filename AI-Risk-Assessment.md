# Evaluación y Matriz de Riesgos de IA (AI Risk Assessment)

## 1. Identificación y Análisis de Riesgos

Esta matriz identifica los riesgos asociados al uso de Modelos de Lenguaje (LLM) en el módulo "Magic Fill" de **EngIA Config** y define los controles mitigantes.

| ID | Riesgo | Descripción | Probabilidad | Impacto | Nivel de Riesgo | Estrategia de Mitigación / Controles |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **R-01** | **Alucinaciones (Generación de Configuración Inválida)** | La IA genera comandos o parámetros que no existen en la sintaxis del vendor (ej. un comando Cisco en un Fortigate). | Media | Alto | **Alto** | 1. **System Prompt Robusto:** Instrucciones explícitas para adherirse a esquemas JSON estrictos.<br>2. **Validación Determinista:** El backend valida el JSON generado contra esquemas definidos en `schemas.py` antes de procesarlo.<br>3. **Human-in-the-loop:** El usuario revisa la configuración generada antes de aplicarla. |
| **R-02** | **Prompt Injection (Jailbreak)** | Un usuario malintencionado intenta manipular la IA para que ignore sus instrucciones de seguridad o revele información del sistema. | Baja | Medio | **Medio** | 1. **Sanitización de Entrada:** Limpieza de caracteres de control y limitación de longitud del prompt.<br>2. **Delimitadores:** Uso de delimitadores claros en el prompt del sistema para separar instrucciones de datos del usuario.<br>3. **Menor Privilegio:** La IA solo tiene capacidad de generar texto (JSON), no de ejecutar comandos en el sistema. |
| **R-03** | **Fuga de Datos Sensibles (Data Leakage)** | El usuario ingresa datos confidenciales (contraseñas reales, IPs públicas sensibles) en el prompt y estos son enviados a la API pública de Google. | Media | Alto | **Alto** | 1. **Advertencia UI:** Mensaje claro al usuario indicando "No ingresar credenciales reales".<br>2. **Filtrado de Patrones:** (Futuro) Implementar detección de patrones de tarjetas de crédito o claves privadas antes de enviar a la API.<br>3. **Política de Privacidad:** Acuerdo de que los datos enviados a la API se rigen por las políticas de Google Cloud. |
| **R-04** | **Sesgo en la Generación** | La IA favorece ciertas configuraciones o vendors sobre otros debido a sesgos en sus datos de entrenamiento. | Baja | Bajo | **Bajo** | 1. **Neutralidad del Prompt:** El prompt del sistema no expresa preferencias por vendors específicos.<br>2. **Revisión Técnica:** Validar que las configuraciones sean técnicamente óptimas independientemente del vendor. |
| **R-05** | **Obsolescencia del Modelo** | El modelo base (Gemini Flash) es depreciado o cambia su comportamiento, rompiendo la funcionalidad. | Media | Medio | **Medio** | 1. **Abstracción de API:** Diseño modular (`chat_agent.py`) que permite cambiar de proveedor o modelo fácilmente.<br>2. **Monitoreo de API:** Alertas sobre errores de API (4xx/5xx) para detectar problemas de disponibilidad. |

## 2. Controles de Seguridad Implementados (Guardrails)

### Guardrail A: Validación de Entrada (Input Guardrail)
*   **Longitud Máxima:** Se limita el prompt de usuario a 1000 caracteres para evitar ataques de desbordamiento de contexto o denegación de servicio (DoS) económica.
*   **Limpieza:** Se eliminan caracteres no imprimibles que podrían alterar el procesamiento del prompt.

### Guardrail B: Validación de Salida (Output Guardrail)
*   **Formato Estricto:** Se fuerza a la IA a responder *únicamente* en formato JSON.
*   **Schema Validation:** Si la IA genera un JSON que no cumple con el esquema esperado (ej. falta el campo `device`), el sistema captura el error y no procesa la solicitud, devolviendo un mensaje de error controlado al usuario.

### Guardrail C: Instrucciones del Sistema (Simulated Safety)
*   El "System Prompt" incluye directivas claras de **identidad** ("Eres un experto en redes") y **negativa de servicio** para solicitudes fuera de dominio ("Si te piden algo que no sea configuración de redes, responde que no puedes ayudar").
