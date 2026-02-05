from .base import VendorConfig
import json

class BigleafConfig(VendorConfig):
    """Generador de configuración para Bigleaf Networks"""
    
    VENDOR_NAME = "bigleaf"
    OUTPUT_FORMAT = "json"
    SUPPORTED_MODELS = [
        "Bigleaf Edge 100", "Bigleaf Edge 200", "Bigleaf Edge 500",
        "Bigleaf Edge 1000", "Bigleaf Edge 2500"
    ]
    
    def __init__(self):
        super().__init__()
    
    def generate_base_config(self, params: dict) -> str:
        self.params = params
        site = params.get('site_info', {})
        
        site_config = {
            "site_name": site.get('name', 'New Site'),
            "customer_name": site.get('customer', ''),
            "location": site.get('location', ''),
            "timezone": site.get('timezone', 'America/Los_Angeles'),
            "notes": f"Configured via automation"
        }
        
        config = f'''# ============================================
# Bigleaf Networks Configuration
# Site: {site.get('name', 'UNNAMED')}
# Customer: {site.get('customer', 'UNNAMED')}
# Firmware: {params.get('device', {}).get('firmware_version', 'Unknown')}
# ============================================
# Note: Bigleaf uses Cloud Portal for most configuration
# Below is the configuration checklist and API calls

# --- Site Information ---
{json.dumps(site_config, indent=2)}
'''
        self.config_sections.append(config)
        return config
    
    def apply_wan_config(self, wan_params: list) -> str:
        config = "\n# --- WAN Circuit Configuration ---\n"
        config += "# Bigleaf automatically manages WAN failover and load balancing\n\n"
        
        circuits = []
        for idx, wan in enumerate(wan_params):
            circuit = {
                "circuit_name": wan.get('isp_name', f'Circuit {idx + 1}'),
                "circuit_type": "primary" if wan.get('priority') == 'primary' else "backup",
                "ip_assignment": "static",
                "static_config": {
                    "ip_address": wan['ip_address'],
                    "subnet_mask": wan['subnet_mask'],
                    "gateway": wan['gateway']
                },
                "bandwidth": {
                    "download_mbps": wan.get('bandwidth_mbps', 100),
                    "upload_mbps": wan.get('bandwidth_mbps', 100)
                },
                "isp_name": wan.get('isp_name', '')
            }
            circuits.append(circuit)
        
        config += f'''# Circuit Configuration
{json.dumps({"circuits": circuits}, indent=2)}
'''
        
        self.config_sections.append(config)
        return config
    
    def apply_lan_config(self, lan_params: list) -> str:
        config = "\n# --- LAN Configuration ---\n"
        
        lan_config = {
            "lan_ip": lan_params[0]['ip_address'] if lan_params else "192.168.1.1",
            "subnet_mask": lan_params[0]['subnet_mask'] if lan_params else "255.255.255.0",
            "dhcp_enabled": lan_params[0].get('dhcp_enabled', True) if lan_params else True
        }
        
        if lan_config['dhcp_enabled'] and lan_params:
            lan_config["dhcp_range"] = {
                "start": lan_params[0].get('dhcp_range_start', '192.168.1.100'),
                "end": lan_params[0].get('dhcp_range_end', '192.168.1.200')
            }
        
        config += f'''# LAN Settings
{json.dumps(lan_config, indent=2)}

# Note: Bigleaf does not support VLANs directly
# Configure VLANs on upstream switch if needed
'''
        
        self.config_sections.append(config)
        return config
    
    def apply_policies(self, policy_set: str) -> str:
        config = "\n# --- Traffic Policies ---\n"
        config += "# Bigleaf automatically optimizes traffic using Dynamic QoS\n\n"
        
        policies = {
            "dynamic_qos": True,
            "voip_optimization": True,
            "video_optimization": True,
            "cloud_app_optimization": True,
            "optimization_mode": policy_set  # basic, standard, advanced
        }
        
        config += f'''{json.dumps(policies, indent=2)}

# Application-specific policies (configured in Bigleaf Portal)
# - Real-time apps (VoIP, Video): Always prioritized
# - Business Critical: High priority
# - Default: Best effort
# - Bulk/Background: Low priority (when needed)
'''
        
        self.config_sections.append(config)
        return config
