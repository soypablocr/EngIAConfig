from .base import VendorConfig
import json
from typing import List, Tuple, Any
from schemas import NetworkParams, WanInterface, LanInterface

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
    SUPPORTED_FIRMWARES = [
        "MX 18.107.2", "MX 18.2xx"
    ]
    
    def __init__(self):
        super().__init__()
        self.api_payloads = {}
    
    def generate_base_config(self, params: NetworkParams):
        self.params = params
        site = params.site_info
        
        self.api_payloads["network_settings"] = {
            "name": site.name,
            "timeZone": site.timezone,
            "notes": f"Customer: {site.customer}\nLocation: {site.location}"
        }
        
    def apply_wan_config(self, wan_params: List[WanInterface]):
        uplink_config = {}
        
        for idx, wan in enumerate(wan_params[:2]):  # Meraki MX has max 2 WAN
            uplink_key = f"wan{idx + 1}"
            uplink_config[uplink_key] = {
                "wanEnabled": "enabled",
                "usingStaticIp": True,
                "staticIp": str(wan.ip_address),
                "staticSubnetMask": wan.subnet_mask,
                "staticGatewayIp": str(wan.gateway),
                "staticDns": [str(d) for d in (self.params.services.dns_servers if self.params.services else ["8.8.8.8", "8.8.4.4"])],
                "vlan": wan.vlan_id if hasattr(wan, 'vlan_id') else None
            }
        
        self.api_payloads["uplink_settings"] = {"interfaces": uplink_config}
        
        if len(wan_params) > 1:
            self.api_payloads["uplink_selection"] = {
                "defaultUplink": "wan1",
                "activeActiveAutoVpnEnabled": False,
                "loadBalancingEnabled": True,
                "failoverAndFailback": {
                    "immediate": {
                        "enabled": True
                    }
                }
            }

    def apply_lan_config(self, lan_params: List[LanInterface]):
        vlans = []
        for lan in lan_params:
            vlan_id = lan.vlan_id or 1
            vlan_config = {
                "id": vlan_id,
                "name": f"LAN_{vlan_id}",
                "subnet": f"{lan.ip_address}/{self._cidr_from_mask(lan.subnet_mask)}",
                "applianceIp": str(lan.ip_address),
                "dhcpHandling": "Run a DHCP server" if lan.dhcp_enabled else "Do not respond to DHCP requests"
            }
            
            if lan.dhcp_enabled:
                vlan_config["dhcpLeaseTime"] = "1 day"
                vlan_config["dnsNameservers"] = "upstream_dns"
                vlan_config["reservedIpRanges"] = [
                    {
                        "start": str(lan.dhcp_range_start),
                        "end": str(lan.dhcp_range_end),
                        "comment": "DHCP Pool"
                    }
                ]
            vlans.append(vlan_config)
            
        self.api_payloads["vlans"] = vlans

    def apply_policies(self, policy_set: str):
        self.api_payloads["l3_firewall_rules"] = self._get_firewall_rules(policy_set)
        
        if policy_set in ['standard', 'advanced']:
            self.api_payloads["content_filtering"] = {
                "blockedUrlCategories": [
                    "meraki:contentFiltering/category/1",
                    "meraki:contentFiltering/category/3",
                    "meraki:contentFiltering/category/24"
                ]
            }
        
        if policy_set == 'advanced':
            self.api_payloads["intrusion_settings"] = {"mode": "prevention"}
            self.api_payloads["malware_settings"] = {"mode": "enabled"}

    def _get_firewall_rules(self, policy_set: str) -> dict:
        return {
            "rules": [
                {
                    "comment": f"Default allow for {policy_set} policy",
                    "policy": "allow",
                    "protocol": "any",
                    "srcPort": "any",
                    "srcCidr": "any",
                    "destPort": "any",
                    "destCidr": "any"
                }
            ]
        }

    def validate_custom_rules(self, params: NetworkParams) -> Tuple[bool, List[str], List[str]]:
        errors = []
        warnings = []
        
        if len(params.wan_interfaces) > 2:
            errors.append(f"Meraki MX solo soporta hasta 2 interfaces WAN (se recibieron {len(params.wan_interfaces)})")
            
        return len(errors) == 0, errors, warnings

    def export_artifact(self) -> Any:
        from output.artifact import ConfigArtifact
        return ConfigArtifact(
            vendor=self.VENDOR_NAME,
            format=self.OUTPUT_FORMAT,
            content={"meraki_dashboard_config": self.api_payloads},
            site_name=self.params.site_info.name if self.params else "Unknown"
        )
