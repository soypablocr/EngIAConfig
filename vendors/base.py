from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from schemas import NetworkParams, WanInterface, LanInterface
from output.artifact import ConfigArtifact, Format
import json

class VendorConfig(ABC):
    """Clase base abstracta para configuración de vendors"""
    
    SUPPORTED_MODELS: List[str] = []
    SUPPORTED_FIRMWARES: List[str] = []
    VENDOR_NAME: str = ""
    OUTPUT_FORMAT: Format = "cli"
    
    def __init__(self):
        self.config_sections: List[Any] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.params: Optional[NetworkParams] = None
    
    @abstractmethod
    def generate_base_config(self, params: NetworkParams):
        """Genera configuración base del dispositivo"""
        raise NotImplementedError
    
    @abstractmethod
    def apply_wan_config(self, wan_params: List[WanInterface]):
        """Aplica configuración de interfaces WAN"""
        raise NotImplementedError
    
    @abstractmethod
    def apply_lan_config(self, lan_params: List[LanInterface]):
        """Aplica configuración de interfaces LAN"""
        raise NotImplementedError
    
    @abstractmethod
    def apply_policies(self, policy_set: str):
        """Aplica políticas de seguridad y QoS"""
        raise NotImplementedError
    
    @abstractmethod
    def validate_custom_rules(self, params: NetworkParams) -> Tuple[bool, List[str], List[str]]:
        """Hook para validaciones específicas del vendor"""
        raise NotImplementedError
    
    def validate_model(self, model: str) -> bool:
        """Valida si el modelo es soportado"""
        return model in self.SUPPORTED_MODELS
    
    def validate_config(self) -> bool:
        """Valida la configuración generada"""
        return len(self.errors) == 0
    
    def add_error(self, error: str):
        """Agrega un error a la lista"""
        self.errors.append(error)

    def add_warning(self, warning: str):
        """Agrega una advertencia a la lista"""
        self.warnings.append(warning)
    
    def export_artifact(self) -> ConfigArtifact:
        """Exporta la configuración como un ConfigArtifact"""
        content = ""
        if self.OUTPUT_FORMAT == "json":
            # For JSON, we might want to merge sections if they are dicts
            merged = {}
            for section in self.config_sections:
                if isinstance(section, dict):
                    merged.update(section)
            content = merged
        else:
            content = "\n".join([str(s) for s in self.config_sections])

        return ConfigArtifact(
            vendor=self.VENDOR_NAME,
            format=self.OUTPUT_FORMAT,
            content=content,
            site_name=self.params.site_info.name if self.params else "Unknown"
        )
    
    def get_timezone_offset(self, timezone: str) -> str:
        """Convierte timezone string a offset"""
        timezone_map = {
            "America/Costa_Rica": "-06:00",
            "America/New_York": "-05:00",
            "America/Chicago": "-06:00",
            "America/Denver": "-07:00",
            "America/Los_Angeles": "-08:00",
            "America/Bogota": "-05:00",
            "America/Mexico_City": "-06:00",
            "UTC": "+00:00"
        }
        return timezone_map.get(timezone, "+00:00")

    def _cidr_from_mask(self, mask: str) -> int:
        """Convierte subnet mask a notación CIDR"""
        try:
            import ipaddress
            return ipaddress.IPv4Network(f"0.0.0.0/{mask}").prefixlen
        except (ValueError, AttributeError):
            return 24

    def _network_address(self, ip: str, mask: str) -> str:
        """Calcula la dirección de red"""
        try:
            import ipaddress
            network = ipaddress.IPv4Network(f"{ip}/{mask}", strict=False)
            return str(network.network_address)
        except (ValueError, AttributeError, IndexError):
            return ip
