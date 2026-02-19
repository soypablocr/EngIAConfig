import os
import json
import random
import re
import requests

class ChatAgent:
    def __init__(self, api_key=None):
        self.system_prompt = """You are an expert Network Engineering Assistant for EngIAConfig. 
        You help users configure network devices (Fortinet, Meraki, etc.) by explaining technical terms, 
        suggesting configurations, and troubleshooting.
        
        Style: Professional, concise, and helpful. Use markdown for formatting.
        Rules:
        - Prioritize safety and accuracy.
        - If the user asks about a specific configuration, refer to the context provided.
        - If you don't know the answer, admit it or suggest general troubleshooting.
        """
        self.api_key = api_key
        self.model = None
        
        # Robustness: Model Versioning & Fallback Configuration
        self.model_version = os.getenv("MODEL_VERSION", "gemini-flash-latest")
        self.local_llm_url = os.getenv("LOCAL_LLM_URL", "http://localhost:11434/api/generate")

        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                
                # Using a standard model via env var or default
                self.model = genai.GenerativeModel(self.model_version)
                print(f"DEBUG: Gemini AI initialized successfully using version: {self.model_version}")
            except ImportError:
                print("WARNING: google-generativeai not installed. Fallback modes enabled.")
            except Exception as e:
                print(f"ERROR: Failed to initialize Gemini AI: {e}")

    prompt_injection_terms = ["ignore previous instructions", "system prompt", "you are now"]

    def _sanitize_input(self, text):
        """Guardrail A: Input Validation & Sanitization"""
        # 1. Length Check
        if len(text) > 1000:
            raise ValueError("Input text too long (max 1000 chars)")
        
        # 2. Simple Injection Check (Heuristic)
        lowered = text.lower()
        for term in self.prompt_injection_terms:
            if term in lowered:
                raise ValueError("Potential prompt injection detected")
                
        # 3. Anonymization / Redaction (PII)
        # Redact IPv4 addresses
        text = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[IP_REDACTED]', text)
        # Redact Email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]', text)
        # Redact potential API Keys (simple heuristic: long alphanumeric strings)
        text = re.sub(r'\b[A-Za-z0-9]{20,}\b', '[KEY_REDACTED]', text)

        # 4. Strip control characters
        return "".join(ch for ch in text if ch.isprintable())

    def _call_local_llm(self, prompt):
        """Fallback method to call a local LLM (e.g., Ollama)"""
        try:
            print(f"DEBUG: Attempting fallback to local LLM at {self.local_llm_url}")
            # Ollama API format
            payload = {
                "model": "llama3",  # Default local model, could also be env var
                "prompt": prompt,
                "stream": False
            }
            response = requests.post(self.local_llm_url, json=payload, timeout=10)
            if response.status_code == 200:
                return response.json().get('response', 'Error: Empty response from local model')
            else:
                return f"Error: Local LLM returned status {response.status_code}"
        except Exception as e:
            print(f"ERROR: Local LLM fallback failed: {e}")
            return None

    def get_response(self, message, context=None):
        """
        Generates a response to the user's message, taking into account the current form context.
        """
        # Sanitize input first
        try:
            message = self._sanitize_input(message)
        except ValueError as e:
            return f"Security Alert: {str(e)}"

        # Construct prompt
        context_str = json.dumps(context, indent=2) if context else "No context provided."
        full_prompt = f"{self.system_prompt}\n\nCurrent Form Context:\n{context_str}\n\nUser Question: {message}"

        # Try Primary LLM (Gemini)
        if self.model:
            try:
                response = self.model.generate_content(full_prompt)
                if response and response.text:
                    return response.text
            except Exception as e:
                # Specific Error Handling
                if "429" in str(e):
                    return "I'm currently experiencing high traffic. Please try again later."
                if "403" in str(e):
                    print("ERROR: Invalid API Key.")
                
                print(f"ERROR: Gemini API call failed: {e}. Attempting fallback...")
                # Proceed to fallback below

        # Try Local LLM Fallback if Primary failed or is not configured
        local_response = self._call_local_llm(full_prompt)
        if local_response:
            return f"{local_response} (Generated via Local Fallback)"

        # Final Fallback to Rule-Based Logic
        return self._rule_based_fallback(message, context)

    def _rule_based_fallback(self, message, context):
        message = message.lower()
        context = context or {}
        vendor = context.get('vendor', 'Unknown Vendor')
        
        if 'hello' in message or 'hi' in message:
            return f"Hello! I am your EngIAConfig assistant. I see you are configuring a **{vendor}** device. How can I help you today? (Rule-Based Mode)"
        
        if 'wan' in message:
            return "WAN (Wide Area Network) interfaces connect your device to the internet. Please specify if you need Static, DHCP, or PPPoE help."

        if 'lan' in message or 'vlan' in message:
            return "LAN configurations involve setting up local subnets and DHCP servers. You can add multiple VLANs to segregate traffic."

        if 'what is' in message:
             return "I can explain technical terms! For example, 'SD-WAN' stands for Software-Defined Wide Area Network. What term would you like me to define?"
        
        return "I'm currently running in 'Offline Mode' (Rule-Based) because AI services are unavailable."

    def extract_config_from_text(self, text):
        """
        Uses the LLM to extract structured configuration from natural language.
        Includes Guardrail B: Output Validation (JSON Schema)
        """
        try:
            # Apply Input Guardrail
            clean_text = self._sanitize_input(text)
        except ValueError as ve:
            return {"error": str(ve)}

        # Schema definition for the LLM
        schema_prompt = """
        SYSTEM: You are a Network Configuration Converter. I will give you a natural language description of a network requirement.
        You must convert it into a JSON object that EXACTLY matches this structure (fill missing fields with reasonable defaults or null):

        {
            "site_info": { 
                "name": "SITE-001 (or inferred)", 
                "customer": "Customer Name (or null)", 
                "location": "Location (or null)", 
                "timezone": "America/Costa_Rica" 
            },
            "device": { 
                "vendor": "fortinet|meraki|velocloud|bigleaf|cato", 
                "model": "Gate-60F (inferred from vendor)", 
                "firmware_version": "7.0 (or similar)" 
            },
            "wan_interfaces": [
                { 
                    "interface_name": "wan1", "ip_address": "1.2.3.4", "subnet_mask": "255.255.255.252", 
                    "gateway": "1.2.3.1", "bandwidth_mbps": 100, "isp_name": "ISP1", "priority": "primary" 
                }
            ],
            "lan_interfaces": [
                { 
                    "interface_name": "lan", "ip_address": "192.168.1.1", "subnet_mask": "255.255.255.0", 
                    "vlan_id": null, "vlan_name": "LAN", "dhcp_enabled": true,
                    "dhcp_range_start": "192.168.1.100", "dhcp_range_end": "192.168.1.200",
                    "dhcp_gateway": "192.168.1.1", "dhcp_dns1": "8.8.8.8", "dhcp_lease_time": 86400
                }
            ],
            "services": { "dns_servers": ["8.8.8.8"], "ntp_servers": ["pool.ntp.org"] },
            "webfilter_categories": [2, 12],
            "policy_template": "basic|standard|advanced",
            "explanation": "Brief reasoning for the choices made."
        }

        Rules (Guardrail C: System Instructions):
        1. Return ONLY valid JSON. No markdown formatting.
        2. STRICTLY ONLY create the interfaces mentioned by the user.
        3. REFUSE requests unrelated to network configuration.
        """
        
        full_prompt = f"{schema_prompt}\n\nUser Description: {clean_text}"

        response_text = None

        # Try Primary LLM
        if self.model:
            try:
                response = self.model.generate_content(full_prompt)
                if response and response.text:
                    response_text = response.text
            except Exception as e:
                print(f"ERROR: Magic Fill Primary LLM failed: {e}")

        # Try Fallback if Primary failed
        if not response_text:
            response_text = self._call_local_llm(full_prompt)
        
        # Process Response
        if response_text:
            try:
                # Clean up markdown if present
                clean_response = response_text.replace('```json', '').replace('```', '').strip()
                # If local LLM returns extra text, try to find JSON block
                if "{" in clean_response:
                    start = clean_response.find("{")
                    end = clean_response.rfind("}") + 1
                    clean_response = clean_response[start:end]
                
                return json.loads(clean_response)
            except json.JSONDecodeError:
                 return {"error": "Failed to parse JSON from AI response."}
            except Exception as e:
                return {"error": str(e)}

        return {"error": "AI service unavailable. Failed to generate configuration."}

