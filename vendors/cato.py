from .base import VendorConfig
import json
from typing import List, Tuple, Any
from schemas import NetworkParams, WanInterface, LanInterface

class CatoConfig(VendorConfig):
    """Generador de configuración para CATO Networks"""
    
    VENDOR_NAME = "cato"
    OUTPUT_FORMAT = "graphql"
    SUPPORTED_MODELS = [
        "Socket X1500", "Socket X1600", "Socket X1700",
        "vSocket (AWS)", "vSocket (Azure)", "vSocket (GCP)"
    ]
    SUPPORTED_FIRMWARES = [
        "18.0", "19.0", "20.0"
    ]
    
    def __init__(self):
        super().__init__()
        self.mutations = []
    
    def generate_base_config(self, params: NetworkParams):
        self.params = params
        site = params.site_info
        
        self.mutations.append({
            "mutation": "addSite",
            "variables": {
                "name": site.name,
                "description": f"Customer: {site.customer}",
                "siteType": "BRANCH",
                "timezone": site.timezone
            }
        })
    
    def apply_wan_config(self, wan_params: List[WanInterface]):
        for idx, wan in enumerate(wan_params):
            self.mutations.append({
                "mutation": "updateSocketInterface",
                "variables": {
                    "interfaceId": f"WAN{idx + 1}",
                    "bandwidth": {
                        "upstream": wan.bandwidth_mbps or 100,
                        "downstream": wan.bandwidth_mbps or 100
                    },
                    "staticConfiguration": {
                        "ip": str(wan.ip_address),
                        "subnet": wan.subnet_mask,
                        "gateway": str(wan.gateway)
                    }
                }
            })

    def apply_lan_config(self, lan_params: List[LanInterface]):
        for lan in lan_params:
            self.mutations.append({
                "mutation": "addNetworkRange",
                "variables": {
                    "name": f"LAN_{lan.vlan_id or 'BASE'}",
                    "subnet": f"{self._network_address(str(lan.ip_address), lan.subnet_mask)}/{self._cidr_from_mask(lan.subnet_mask)}",
                    "gateway": str(lan.ip_address),
                    "vlan": lan.vlan_id or 0,
                    "dhcp": {
                        "enabled": lan.dhcp_enabled
                    }
                }
            })

    def apply_policies(self, policy_set: str):
        self.mutations.append({
            "mutation": "setPolicyAlpha",
            "variables": {
                "mode": policy_set,
                "ips_enabled": policy_set == 'advanced'
            }
        })

    def validate_custom_rules(self, params: NetworkParams) -> Tuple[bool, List[str], List[str]]:
        errors = []
        warnings = []
        if not params.site_info.location:
            warnings.append("CATO requiere una dirección física para el Site Location para mayor precisión en el portal")
        return len(errors) == 0, errors, warnings

    def export_artifact(self) -> Any:
        from output.artifact import ConfigArtifact
        return ConfigArtifact(
            vendor=self.VENDOR_NAME,
            format=self.OUTPUT_FORMAT,
            content={"cato_graphql_mutations": self.mutations},
            site_name=self.params.site_info.name if self.params else "Unknown"
        )
