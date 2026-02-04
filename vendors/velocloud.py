from .base import VendorConfig
import json

class VelocloudConfig(VendorConfig):
    """Generador de configuración para VMware SD-WAN (Velocloud)"""
    
    VENDOR_NAME = "velocloud"
    OUTPUT_FORMAT = "json"
    SUPPORTED_MODELS = [
        "Edge 510", "Edge 520", "Edge 540",
        "Edge 610", "Edge 620", "Edge 640",
        "Edge 710", "Edge 720", "Edge 740",
        "Edge 840", "Edge 860",
        "Edge 1000", "Edge 3400", "Edge 3800"
    ]
    
    def __init__(self):
        super().__init__()
        self.edge_config = {}
    
    def generate_base_config(self, params: dict) -> str:
        self.params = params
        site = params.get('site_info', {})
        device = params.get('device', {})
        
        self.edge_config = {
            "name": site.get('name', 'New Edge'),
            "description": f"Customer: {site.get('customer', '')} | Location: {site.get('location', '')}",
            "modelNumber": device.get('model', 'Edge 620'),
            "site": {
                "name": site.get('name'),
                "contactName": "",
                "contactPhone": "",
                "contactEmail": "",
                "streetAddress": site.get('location', ''),
                "city": "",
                "country": "",
                "lat": 0.0,
                "lon": 0.0
            },
            "haEnabled": False,
            "haState": "UNCONFIGURED"
        }
        
        config = f'''# ============================================
# VMware SD-WAN (Velocloud) Configuration
# Site: {site.get('name', 'UNNAMED')}
# Customer: {site.get('customer', 'UNNAMED')}
# ============================================
# Note: Velocloud uses VCO API for configuration
# Below are the API calls and JSON payloads needed

# --- Edge Provisioning ---
# POST /edge/edgeProvision
{json.dumps(self.edge_config, indent=2)}
'''
        self.config_sections.append(config)
        return config
    
    def apply_wan_config(self, wan_params: list) -> str:
        config = "\n# --- WAN Link Configuration ---\n"
        
        wan_links = []
        for idx, wan in enumerate(wan_params):
            link = {
                "interface": f"GE{idx + 1}",
                "internalId": f"WAN{idx + 1}",
                "name": wan.get('isp_name', f'WAN Link {idx + 1}'),
                "publicIpAddress": wan['ip_address'],
                "mode": "STATIC",
                "staticIpConfig": {
                    "address": wan['ip_address'],
                    "netmask": wan['subnet_mask'],
                    "gateway": wan['gateway'],
                    "wanDns": self.params.get('services', {}).get('dns_servers', ['8.8.8.8'])
                },
                "bwMeasurement": "USER_DEFINED",
                "uploadMbps": wan.get('bandwidth_mbps', 100),
                "downloadMbps": wan.get('bandwidth_mbps', 100),
                "type": "WIRED",
                "isp": wan.get('isp_name', ''),
                "enabled": True,
                "backupOnly": wan.get('priority') != 'primary'
            }
            wan_links.append(link)
            
            config += f'''# POST /configuration/updateConfigurationModule (WAN Link {idx + 1})
{json.dumps({"links": [link]}, indent=2)}

'''
        
        self.config_sections.append(config)
        return config
    
    def apply_lan_config(self, lan_params: list) -> str:
        config = "\n# --- LAN/VLAN Configuration ---\n"
        
        routed_interfaces = []
        for lan in lan_params:
            interface = {
                "name": lan.get('vlan_name', 'LAN'),
                "vlanId": lan.get('vlan_id', 0),
                "disabled": False,
                "addressing": {
                    "type": "STATIC",
                    "cidrIp": f"{lan['ip_address']}/{self._cidr_from_mask(lan['subnet_mask'])}",
                    "cidrPrefix": self._cidr_from_mask(lan['subnet_mask']),
                    "netmask": lan['subnet_mask'],
                    "gateway": lan['ip_address']
                },
                "dhcp": {
                    "enabled": lan.get('dhcp_enabled', False),
                    "dhcpRelay": {"enabled": False}
                }
            }
            
            if lan.get('dhcp_enabled'):
                interface["dhcp"]["poolStart"] = lan['dhcp_range_start']
                interface["dhcp"]["poolEnd"] = lan['dhcp_range_end']
                interface["dhcp"]["leaseTime"] = 86400
                interface["dhcp"]["options"] = {
                    "dns1": self.params.get('services', {}).get('dns_servers', ['8.8.8.8'])[0]
                }
            
            routed_interfaces.append(interface)
        
        lan_config = {"routedInterfaces": routed_interfaces}
        config += f'''# POST /configuration/updateConfigurationModule (LAN)
{json.dumps(lan_config, indent=2)}
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
        business_policy = {
            "name": "Default-Allow",
            "match": {
                "appid": -1,
                "dip": "any",
                "dsm": "255.255.255.255",
                "sip": "any",
                "ssm": "255.255.255.255"
            },
            "action": {
                "edge2CloudRouting": {
                    "allowDirect": True,
                    "routeType": "GATEWAY_VIA_EDGE"
                },
                "edge2DataCenterRouting": {
                    "enabled": False
                },
                "QoS": {
                    "type": "transactional",
                    "class": "normal"
                }
            }
        }
        
        return f'''\n# --- Business Policy (Basic) ---
# POST /configuration/updateConfigurationModule (Business Policy)
{json.dumps({"rules": [business_policy]}, indent=2)}
'''
    
    def _standard_policies(self) -> str:
        base = self._basic_policies()
        
        qos_rules = [
            {
                "name": "VoIP-Priority",
                "match": {"appid": 130},  # Voice/Video apps
                "action": {
                    "QoS": {
                        "type": "realtime",
                        "class": "high"
                    },
                    "linkSteering": "LOAD_BALANCE"
                }
            },
            {
                "name": "Streaming-Throttle",
                "match": {"appid": 50},  # Streaming
                "action": {
                    "QoS": {
                        "type": "bulk",
                        "class": "low"
                    }
                }
            }
        ]
        
        return base + f'''\n# --- QoS Rules (Standard) ---
# POST /configuration/updateConfigurationModule (QoS)
{json.dumps({"rules": qos_rules}, indent=2)}
'''
    
    def _advanced_policies(self) -> str:
        base = self._standard_policies()
        
        firewall = {
            "inbound": [
                {
                    "name": "Block-All-Inbound",
                    "match": {"sip": "any", "dip": "any"},
                    "action": {"allow": False, "log": True}
                }
            ],
            "stateful": True,
            "logging": {"enabled": True}
        }
        
        return base + f'''\n# --- Firewall Rules (Advanced) ---
# POST /configuration/updateConfigurationModule (Firewall)
{json.dumps(firewall, indent=2)}
'''
