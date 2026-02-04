from .base import VendorConfig
import json

class MerakiConfig(VendorConfig):
    """Generador de configuración para Cisco Meraki MX"""
    
    VENDOR_NAME = "meraki"
    OUTPUT_FORMAT = "json"
    SUPPORTED_MODELS = [
        "MX64", "MX64W", "MX67", "MX67W", "MX67C",
        "MX68", "MX68W", "MX68CW",
        "MX75", "MX84", "MX85",
        "MX95", "MX100", "MX105",
        "MX250", "MX450"
    ]
    
    def __init__(self):
        super().__init__()
        self.api_calls = []
    
    def generate_base_config(self, params: dict) -> str:
        self.params = params
        site = params.get('site_info', {})
        
        # Network settings
        network_settings = {
            "name": site.get('name', 'New Network'),
            "timeZone": site.get('timezone', 'America/Los_Angeles'),
            "notes": f"Customer: {site.get('customer', '')}\nLocation: {site.get('location', '')}"
        }
        
        self.api_calls.append({
            "endpoint": "PUT /networks/{networkId}",
            "description": "Update network settings",
            "payload": network_settings
        })
        
        config = f'''# ============================================
# Meraki MX Configuration
# Site: {site.get('name', 'UNNAMED')}
# Customer: {site.get('customer', 'UNNAMED')}
# ============================================
# Note: Meraki uses Dashboard API for configuration
# Below are the API calls needed to configure this device

# --- Network Settings ---
# PUT /networks/networkId
{json.dumps(network_settings, indent=2)}
'''
        self.config_sections.append(config)
        return config
    
    def apply_wan_config(self, wan_params: list) -> str:
        config = "\n# --- WAN/Uplink Configuration ---\n"
        
        uplink_config = {
            "wan1": None,
            "wan2": None
        }
        
        for idx, wan in enumerate(wan_params[:2]):  # Meraki MX has max 2 WAN
            uplink_key = f"wan{idx + 1}"
            uplink_config[uplink_key] = {
                "wanEnabled": "enabled",
                "usingStaticIp": True,
                "staticIp": wan['ip_address'],
                "staticSubnetMask": wan['subnet_mask'],
                "staticGatewayIp": wan['gateway'],
                "staticDns": self.params.get('services', {}).get('dns_servers', ['8.8.8.8', '8.8.4.4']),
                "vlan": wan.get('vlan_id', None)
            }
        
        self.api_calls.append({
            "endpoint": "PUT /networks/{networkId}/appliance/uplinks/settings",
            "description": "Configure WAN uplinks",
            "payload": {"interfaces": uplink_config}
        })
        
        config += f'''# PUT /networks/networkId/appliance/uplinks/settings
{json.dumps({"interfaces": uplink_config}, indent=2)}
'''
        
        # Load balancing if dual WAN
        if len(wan_params) > 1:
            traffic_shaping = {
                "defaultRulesEnabled": True,
                "rules": []
            }
            
            self.api_calls.append({
                "endpoint": "PUT /networks/{networkId}/appliance/trafficShaping/uplinkSelection",
                "description": "Configure uplink selection and failover",
                "payload": {
                    "defaultUplink": "wan1",
                    "activeActiveAutoVpnEnabled": False,
                    "loadBalancingEnabled": True,
                    "failoverAndFailback": {
                        "immediate": {
                            "enabled": True
                        }
                    }
                }
            })
            
            config += '''\n# PUT /networks/{networkId}/appliance/trafficShaping/uplinkSelection
''' + json.dumps({
                "defaultUplink": "wan1",
                "loadBalancingEnabled": True
            }, indent=2) + "\n"
        
        self.config_sections.append(config)
        return config
    
    def apply_lan_config(self, lan_params: list) -> str:
        config = "\n# --- LAN/VLAN Configuration ---\n"
        vlans = []
        
        for lan in lan_params:
            vlan_config = {
                "id": lan.get('vlan_id', 1),
                "name": lan.get('vlan_name', 'Default'),
                "subnet": f"{lan['ip_address']}/{self._cidr_from_mask(lan['subnet_mask'])}",
                "applianceIp": lan['ip_address'],
                "dhcpHandling": "Run a DHCP server" if lan.get('dhcp_enabled') else "Do not respond to DHCP requests"
            }
            
            if lan.get('dhcp_enabled'):
                vlan_config["dhcpLeaseTime"] = "1 day"
                vlan_config["dhcpBootOptionsEnabled"] = False
                vlan_config["dnsNameservers"] = "upstream_dns"
                vlan_config["reservedIpRanges"] = [
                    {
                        "start": lan['dhcp_range_start'],
                        "end": lan['dhcp_range_end'],
                        "comment": "DHCP Pool"
                    }
                ]
            
            vlans.append(vlan_config)
            
            self.api_calls.append({
                "endpoint": f"PUT /networks/networkId/appliance/vlans/{lan.get('vlan_id', 1)}",
                "description": f"Configure VLAN {lan.get('vlan_id', 1)}",
                "payload": vlan_config
            })
            
            config += f'''# PUT /networks/networkId/appliance/vlans/{lan.get('vlan_id', 1)}
{json.dumps(vlan_config, indent=2)}

'''
        
        self.config_sections.append(config)
        return config
    
    def apply_policies(self, policy_set: str) -> str:
        policies = {
            'basic': self._basic_policies(),
            'standard': self._standard_policies(),
            'advanced': self._advanced_policies()
        }
        config = policies.get(policy_set, policies['basic'])
        self.config_sections.append(config)
        return config
    
    def _basic_policies(self) -> str:
        firewall_rules = {
            "rules": [
                {
                    "comment": "Allow all outbound",
                    "policy": "allow",
                    "protocol": "any",
                    "srcPort": "any",
                    "srcCidr": "any",
                    "destPort": "any",
                    "destCidr": "any",
                    "syslogEnabled": True
                }
            ]
        }
        
        self.api_calls.append({
            "endpoint": "PUT /networks/{networkId}/appliance/firewall/l3FirewallRules",
            "description": "Configure L3 firewall rules",
            "payload": firewall_rules
        })
        
        return f'''\n# --- Basic Firewall Policies ---
# PUT /networks/networkId/appliance/firewall/l3FirewallRules
{json.dumps(firewall_rules, indent=2)}
'''
    
    def _standard_policies(self) -> str:
        base = self._basic_policies()
        
        content_filtering = {
            "allowedUrlPatterns": [],
            "blockedUrlPatterns": [],
            "blockedUrlCategories": [
                "meraki:contentFiltering/category/1",   # Adult
                "meraki:contentFiltering/category/3",   # Botnets
                "meraki:contentFiltering/category/14",  # Gambling
                "meraki:contentFiltering/category/24",  # Malware
                "meraki:contentFiltering/category/26"   # Phishing
            ],
            "urlCategoryListSize": "topSites"
        }
        
        self.api_calls.append({
            "endpoint": "PUT /networks/{networkId}/appliance/contentFiltering",
            "description": "Configure content filtering",
            "payload": content_filtering
        })
        
        return base + f'''\n# --- Content Filtering ---
# PUT /networks/networkId/appliance/contentFiltering
{json.dumps(content_filtering, indent=2)}
'''
    
    def _advanced_policies(self) -> str:
        base = self._standard_policies()
        
        threat_protection = {
            "mode": "prevention",
            "allowedRules": []
        }
        
        self.api_calls.append({
            "endpoint": "PUT /networks/{networkId}/appliance/security/intrusion",
            "description": "Configure IDS/IPS",
            "payload": threat_protection
        })
        
        malware_settings = {
            "mode": "enabled",
            "allowedUrls": [],
            "allowedFiles": []
        }
        
        self.api_calls.append({
            "endpoint": "PUT /networks/{networkId}/appliance/security/malware",
            "description": "Configure AMP",
            "payload": malware_settings
        })
        
        return base + f'''\n# --- Advanced Threat Protection ---
# PUT /networks/networkId/appliance/security/intrusion
{json.dumps(threat_protection, indent=2)}

# PUT /networks/networkId/appliance/security/malware
{json.dumps(malware_settings, indent=2)}
'''
    
    def _cidr_from_mask(self, mask: str) -> int:
        """Convierte subnet mask a notación CIDR"""
        return sum([bin(int(x)).count('1') for x in mask.split('.')])
    
    def export_config(self, format: str = "json") -> str:
        if format == "python":
            return self._generate_python_script()
        return "\n".join(self.config_sections)
    
    def _generate_python_script(self) -> str:
        script = '''#!/usr/bin/env python3
"""
Meraki MX Configuration Script
Generated automatically - Review before executing
"""
import meraki

# Initialize dashboard
API_KEY = 'YOUR_API_KEY_HERE'
NETWORK_ID = 'YOUR_NETWORK_ID_HERE'

dashboard = meraki.DashboardAPI(API_KEY)

'''
        for call in self.api_calls:
            script += f"\n# {call['description']}\n"
            script += f"# {call['endpoint']}\n"
            script += f"# Payload: {json.dumps(call['payload'])}\n"
        
        return script
