from .base import VendorConfig
import json
from typing import List, Tuple, Any
from schemas import NetworkParams, WanInterface, LanInterface

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
    SUPPORTED_FIRMWARES = [
        "5.0.1", "5.1.0", "5.2.0"
    ]
    
    def __init__(self):
        super().__init__()
        self.payloads = {}
    
    def generate_base_config(self, params: NetworkParams):
        self.params = params
        site = params.site_info
        
        self.payloads["edge_provision"] = {
            "name": site.name,
            "description": f"Customer: {site.customer} | Location: {site.location}",
            "modelNumber": params.device.model,
            "site": {
                "name": site.name,
                "streetAddress": site.location,
            },
            "haEnabled": False
        }
    
    def apply_wan_config(self, wan_params: List[WanInterface]):
        wan_links = []
        for idx, wan in enumerate(wan_params):
            link = {
                "interface": f"GE{idx + 1}",
                "name": wan.isp_name or f"WAN_{idx + 1}",
                "publicIpAddress": str(wan.ip_address),
                "staticIpConfig": {
                    "address": str(wan.ip_address),
                    "netmask": wan.subnet_mask,
                    "gateway": str(wan.gateway),
                    "wanDns": [str(d) for d in (self.params.services.dns_servers if self.params.services else ["8.8.8.8"])]
                },
                "uploadMbps": wan.bandwidth_mbps or 100,
                "downloadMbps": wan.bandwidth_mbps or 100,
                "backupOnly": wan.priority != 'primary'
            }
            wan_links.append(link)
        self.payloads["wan_links"] = wan_links

    def apply_lan_config(self, lan_params: List[LanInterface]):
        routed_interfaces = []
        for lan in lan_params:
            interface = {
                "name": f"LAN_{lan.vlan_id or 'BASE'}",
                "vlanId": lan.vlan_id or 0,
                "addressing": {
                    "type": "STATIC",
                    "cidrIp": f"{lan.ip_address}/{self._cidr_from_mask(lan.subnet_mask)}",
                    "gateway": str(lan.ip_address)
                },
                "dhcp": {
                    "enabled": lan.dhcp_enabled,
                }
            }
            
            if lan.dhcp_enabled:
                interface["dhcp"]["poolStart"] = str(lan.dhcp_range_start)
                interface["dhcp"]["poolEnd"] = str(lan.dhcp_range_end)
            
            routed_interfaces.append(interface)
        self.payloads["lan_interfaces"] = routed_interfaces

    def apply_policies(self, policy_set: str):
        self.payloads["business_policies"] = [
            {
                "name": f"Default_{policy_set.capitalize()}",
                "action": {
                    "QoS": {
                        "type": "transactional" if policy_set == 'basic' else "realtime",
                        "priority": "high" if policy_set == 'advanced' else "normal"
                    }
                }
            }
        ]

    def validate_custom_rules(self, params: NetworkParams) -> Tuple[bool, List[str], List[str]]:
        errors = []
        warnings = []
        if not params.lan_interfaces:
            errors.append("Velocloud requiere al menos una interfaz LAN configurada")
        return len(errors) == 0, errors, warnings

    def export_artifact(self) -> Any:
        from output.artifact import ConfigArtifact
        return ConfigArtifact(
            vendor=self.VENDOR_NAME,
            format=self.OUTPUT_FORMAT,
            content={"velocloud_vco_config": self.payloads},
            site_name=self.params.site_info.name if self.params else "Unknown"
        )
