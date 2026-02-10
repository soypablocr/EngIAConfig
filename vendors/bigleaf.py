from .base import VendorConfig
import json
from typing import List, Tuple, Any
from schemas import NetworkParams, WanInterface, LanInterface

class BigleafConfig(VendorConfig):
    """Generador de configuración para Bigleaf Networks"""
    
    VENDOR_NAME = "bigleaf"
    OUTPUT_FORMAT = "json"
    SUPPORTED_MODELS = [
        "Bigleaf Edge 100", "Bigleaf Edge 200", "Bigleaf Edge 500",
        "Bigleaf Edge 1000", "Bigleaf Edge 2500"
    ]
    SUPPORTED_FIRMWARES = [
        "v3.4.1", "v3.5.0"
    ]
    
    def __init__(self):
        super().__init__()
        self.portal_config = {}
    
    def generate_base_config(self, params: NetworkParams):
        self.params = params
        site = params.site_info
        
        self.portal_config["site_info"] = {
            "site_name": site.name,
            "customer_name": site.customer,
            "location": site.location,
            "timezone": site.timezone
        }
    
    def apply_wan_config(self, wan_params: List[WanInterface]):
        circuits = []
        for idx, wan in enumerate(wan_params):
            circuit = {
                "circuit_name": wan.isp_name or f"Circuit_{idx + 1}",
                "priority": wan.priority,
                "static_config": {
                    "ip_address": str(wan.ip_address),
                    "subnet_mask": wan.subnet_mask,
                    "gateway": str(wan.gateway)
                },
                "bandwidth": {
                    "mbps": wan.bandwidth_mbps or 100
                }
            }
            circuits.append(circuit)
        self.portal_config["wan_circuits"] = circuits

    def apply_lan_config(self, lan_params: List[LanInterface]):
        if not lan_params:
            return
            
        # Bigleaf usually has a single handoff LAN
        primary_lan = lan_params[0]
        self.portal_config["lan_handoff"] = {
            "ip_address": str(primary_lan.ip_address),
            "subnet_mask": primary_lan.subnet_mask,
            "dhcp_enabled": primary_lan.dhcp_enabled
        }
        
        if primary_lan.dhcp_enabled:
            self.portal_config["lan_handoff"]["dhcp_pool"] = {
                "start": str(primary_lan.dhcp_range_start),
                "end": str(primary_lan.dhcp_range_end)
            }

    def apply_policies(self, policy_set: str):
        self.portal_config["optimization_policy"] = {
            "mode": policy_set,
            "dynamic_qos": True,
            "voip_priority": True
        }

    def validate_custom_rules(self, params: NetworkParams) -> Tuple[bool, List[str], List[str]]:
        errors = []
        warnings = []
        for lan in params.lan_interfaces:
            if lan.vlan_id and lan.vlan_id > 0:
                warnings.append(f"Bigleaf no soporta VLANs directamente (VLAN {lan.vlan_id}).")
        return len(errors) == 0, errors, warnings

    def export_artifact(self) -> Any:
        from output.artifact import ConfigArtifact
        return ConfigArtifact(
            vendor=self.VENDOR_NAME,
            format=self.OUTPUT_FORMAT,
            content={"bigleaf_portal_provisioning": self.portal_config},
            site_name=self.params.site_info.name if self.params else "Unknown"
        )
