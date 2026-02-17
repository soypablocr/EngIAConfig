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

