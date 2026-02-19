import os
import json
import random

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

        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                
                # Using a standard model
                self.model = genai.GenerativeModel('gemini-flash-latest')
                print("DEBUG: Gemini AI initialized successfully.")
            except ImportError:
                print("WARNING: google-generativeai not installed. Using rule-based fallback.")
            except Exception as e:
                print(f"ERROR: Failed to initialize Gemini AI: {e}")

    def get_response(self, message, context=None):
        """
        Generates a response to the user's message, taking into account the current form context.
        """
        # Try LLM first if available
        if self.model:
            try:
                # Construct prompt with context
                context_str = json.dumps(context, indent=2) if context else "No context provided."
                full_prompt = f"{self.system_prompt}\n\nCurrent Form Context:\n{context_str}\n\nUser Question: {message}"
                
                response = self.model.generate_content(full_prompt)
                if response and response.text:
                    return response.text
            except Exception as e:
                # Check for Rate Limit (429)
                if "429" in str(e):
                    return "I'm currently experiencing high traffic (Rate Limit Exceeded). Please try again in a minute."
                
                # Check for Leaked/Invalid Key (403)
                if "403" in str(e) or "leaked" in str(e).lower():
                    return "ERROR: The API Key is invalid or has been revoked. Please check your GEMINI_API_KEY environment variable."

                print(f"ERROR: Gemini API call failed: {e}. Falling back to rules.")

        # Fallback to Rule-Based Logic
        message = message.lower()
        context = context or {}
        vendor = context.get('vendor', 'Unknown Vendor')
        
        if 'hello' in message or 'hi' in message:
            return f"Hello! I am your EngIAConfig assistant. I see you are configuring a **{vendor}** device. How can I help you today? (Rule-Based Mode)"
        
        if 'wan' in message:
            if vendor == 'Fortinet':
                return "For **Fortinet**, WAN interfaces are typically configured with static IPs or DHCP. In SD-WAN setups, multiple WANs are used for redundancy. Do you need help with SD-WAN rules?"
            elif vendor == 'Meraki':
                return "On **Meraki** MX appliances, WAN1 and WAN2 are automatically configured for load balancing or failover. You can set static IPs in the Local Status Page or via the dashboard."
            return "WAN (Wide Area Network) interfaces connect your device to the internet. Please specify if you need Static, DHCP, or PPPoE help."

        if 'lan' in message or 'vlan' in message:
            return "LAN configurations involve setting up local subnets and DHCP servers. You can add multiple VLANs to segregate traffic (e.g., Voice, Guest, Corporate)."

        if 'ip' in message and 'static' in message:
            return "To configure a Static IP, you'll need the IP Address, Subnet Mask, and Gateway. Make sure these match the details provided by your ISP."

        if 'what is' in message:
             return "I can explain technical terms! For example, 'SD-WAN' stands for Software-Defined Wide Area Network. What term would you like me to define?"
        
        return "I'm currently running in 'Offline Mode' (Rule-Based) because the AI service is unavailable. To unlock my full capabilities, please check the API Key configuration."

    def extract_config_from_text(self, text):
        """
        Interprets natural language text and returns a JSON object matching the form structure.
        """
        if not self.model:
            return {"error": "AI service unavailable. Check API Key."}

        # Schema definition for the LLM
        schema_prompt = """
        You are a Network Configuration Converter. I will give you a natural language description of a network requirement.
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
            "webfilter_categories": [2, 12] (IDs for Pornography/Malware if mentioned),
            "policy_template": "basic|standard|advanced",
            "explanation": "Brief reasoning for the choices made (e.g. why this model, why these interfaces)."
        }

        Rules:
        1. Return ONLY valid JSON. No markdown formatting.
        2. If the user mentions "Guest", create a VLAN (e.g., ID 10) for it on LAN interfaces.
        3. If the user mentions specific IPs, use them. Otherwise, generate realistic example IPs (RFC1918 for LAN, Public for WAN).
        4. Infer the Vendor if possible (e.g. "MX64" -> meraki). Default to "fortinet" if unsure.
        5. The 'explanation' field is MANADATORY. Explain your logic clearly to the user.
        6. STRICTLY ONLY create the interfaces mentioned by the user. Do NOT create default WAN/LAN interfaces if they are not requested.
           - If user says "WAN1 and WAN2", create ONLY those two.
           - If user says nothing about LAN, do NOT create a LAN interface.
           - If user says nothing about WAN, do NOT create a WAN interface.
        7. If you must create a default interface because the device requires one to function (e.g. LAN), create ONLY ONE.
        """

        try:
            full_prompt = f"{schema_prompt}\n\nUser Description: {text}"
            response = self.model.generate_content(full_prompt)
            
            if response and response.text:
                # Clean up markdown if present
                clean_text = response.text.replace('```json', '').replace('```', '').strip()
                return json.loads(clean_text)
        except Exception as e:
            print(f"ERROR: Magic Fill failed: {e}")
            return {"error": str(e)}
        
        return {"error": "Failed to generate configuration."}

