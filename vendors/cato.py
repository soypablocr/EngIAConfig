from .base import VendorConfig
import json

class CatoConfig(VendorConfig):
    """Generador de configuración para CATO Networks"""
    
    VENDOR_NAME = "cato"
    OUTPUT_FORMAT = "json"
    SUPPORTED_MODELS = [
        "Socket X1500", "Socket X1600", "Socket X1700",
        "vSocket (AWS)", "vSocket (Azure)", "vSocket (GCP)"
    ]
    
    def __init__(self):
        super().__init__()
        self.api_mutations = []
    
    def generate_base_config(self, params: dict) -> str:
        self.params = params
        site = params.get('site_info', {})
        device = params.get('device', {})
        
        site_mutation = {
            "mutation": "addSite",
            "input": {
                "name": site.get('name', 'New Site'),
                "description": f"Customer: {site.get('customer', '')} | {site.get('location', '')}",
                "siteType": "BRANCH",
                "connectionType": "SOCKET",
                "countryCode": "US",  # Should be parameterized
                "timezone": site.get('timezone', 'America/New_York'),
                "siteLocation": {
                    "address": site.get('location', '')
                }
            }
        }
        self.api_mutations.append(site_mutation)
        
        config = f'''# ============================================
# CATO Networks Configuration
# Site: {site.get('name', 'UNNAMED')}
# Customer: {site.get('customer', 'UNNAMED')}
# Model: {device.get('model', 'Socket')}
# ============================================
# Note: CATO uses GraphQL API for configuration
# Below are the mutations needed

# --- Create Site ---
# GraphQL Mutation: addSite
{json.dumps(site_mutation, indent=2)}
'''
        self.config_sections.append(config)
        return config
    
    def apply_wan_config(self, wan_params: list) -> str:
        config = "\n# --- Socket WAN Configuration ---\n"
        
        interfaces = []
        for idx, wan in enumerate(wan_params):
            interface = {
                "mutation": "updateSocketInterface",
                "input": {
                    "interfaceId": f"WAN{idx + 1}",
                    "name": wan.get('isp_name', f'WAN-{idx + 1}'),
                    "destType": "CATO",
                    "bandwidth": {
                        "upstreamBandwidth": wan.get('bandwidth_mbps', 100),
                        "downstreamBandwidth": wan.get('bandwidth_mbps', 100),
                        "upstreamBandwidthPriority": 1 if wan.get('priority') == 'primary' else 2
                    },
                    "staticConfiguration": {
                        "ip": wan['ip_address'],
                        "subnet": wan['subnet_mask'],
                        "gateway": wan['gateway']
                    }
                }
            }
            interfaces.append(interface)
            self.api_mutations.append(interface)
        
        config += f'''{json.dumps({"interfaces": interfaces}, indent=2)}
'''
        self.config_sections.append(config)
        return config
    
    def apply_lan_config(self, lan_params: list) -> str:
        config = "\n# --- Native Range (LAN) Configuration ---\n"
        
        native_ranges = []
        for lan in lan_params:
            cidr = self._cidr_from_mask(lan['subnet_mask'])
            native_range = {
                "mutation": "addNetworkRange",
                "input": {
                    "name": lan.get('vlan_name', 'LAN'),
                    "rangeType": "Routed",
                    "subnet": f"{self._network_address(lan['ip_address'], lan['subnet_mask'])}/{cidr}",
                    "gateway": lan['ip_address'],
                    "vlan": lan.get('vlan_id', 0),
                    "dhcp": {
                        "dhcpType": "DHCP_RANGE" if lan.get('dhcp_enabled') else "DHCP_DISABLED",
                        "ipRange": f"{lan.get('dhcp_range_start', '')}-{lan.get('dhcp_range_end', '')}" if lan.get('dhcp_enabled') else None
                    }
                }
            }
            native_ranges.append(native_range)
            self.api_mutations.append(native_range)
        
        config += f'''{json.dumps({"nativeRanges": native_ranges}, indent=2)}
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
        wan_firewall = {
            "mutation": "addWanFirewallRule",
            "input": {
                "name": "Allow-Outbound",
                "enabled": True,
                "source": {"subnet": "ANY"},
                "destination": {"subnet": "ANY"},
                "service": {"protocol": "ANY"},
                "action": "ALLOW",
                "tracking": {
                    "event": {"enabled": True}
                }
            }
        }
        self.api_mutations.append(wan_firewall)
        
        return f'''\n# --- WAN Firewall (Basic) ---
{json.dumps(wan_firewall, indent=2)}
'''
    
    def _standard_policies(self) -> str:
        base = self._basic_policies()
        
        internet_firewall = {
            "mutation": "addInternetFirewallRule",
            "input": {
                "name": "Standard-Internet-Policy",
                "enabled": True,
                "source": {"subnet": "ANY"},
                "service": {"protocol": "ANY"},
                "action": "ALLOW",
                "categories": {
                    "blockedCategories": [
                        "Adult Content", "Gambling", "Malware",
                        "Phishing", "Botnets", "Spyware"
                    ]
                }
            }
        }
        self.api_mutations.append(internet_firewall)
        
        return base + f'''\n# --- Internet Firewall (Standard) ---
{json.dumps(internet_firewall, indent=2)}
'''
    
    def _advanced_policies(self) -> str:
        base = self._standard_policies()
        
        ips_policy = {
            "mutation": "setSiteIPS",
            "input": {
                "enabled": True,
                "mode": "PREVENT",
                "advancedSettings": {
                    "exploitProtection": True,
                    "malwareProtection": True,
                    "networkAttackProtection": True
                }
            }
        }
        self.api_mutations.append(ips_policy)
        
        return base + f'''\n# --- IPS Policy (Advanced) ---
{json.dumps(ips_policy, indent=2)}
'''
    
    def _cidr_from_mask(self, mask: str) -> int:
        return sum([bin(int(x)).count('1') for x in mask.split('.')])
    
    def _network_address(self, ip: str, mask: str) -> str:
        """Calcula la dirección de red"""
        ip_parts = [int(x) for x in ip.split('.')]
        mask_parts = [int(x) for x in mask.split('.')]
        network = [ip_parts[i] & mask_parts[i] for i in range(4)]
        return '.'.join(map(str, network))
