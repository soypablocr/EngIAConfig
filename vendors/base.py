from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import json

class VendorConfig(ABC):
    """Clase base abstracta para configuración de vendors"""
    
    SUPPORTED_MODELS: List[str] = []
    VENDOR_NAME: str = ""
    OUTPUT_FORMAT: str = "cli"  # cli, json, api
    
    def __init__(self):
        self.config_sections: List[str] = []
        self.errors: List[str] = []
        self.params: Dict = {}
    
    @abstractmethod
    def generate_base_config(self, params: dict) -> str:
        """Genera configuración base del dispositivo"""
        pass
    
    @abstractmethod
    def apply_wan_config(self, wan_params: list) -> str:
        """Aplica configuración de interfaces WAN"""
        pass
    
    @abstractmethod
    def apply_lan_config(self, lan_params: list) -> str:
        """Aplica configuración de interfaces LAN"""
        pass
    
    @abstractmethod
    def apply_policies(self, policy_set: str) -> str:
        """Aplica políticas de seguridad y QoS"""
        pass
    
    def validate_model(self, model: str) -> bool:
        """Valida si el modelo es soportado"""
        return model in self.SUPPORTED_MODELS
    
    def validate_config(self) -> bool:
        """Valida la configuración generada"""
        return len(self.errors) == 0
    
    def add_error(self, error: str):
        """Agrega un error a la lista"""
        self.errors.append(error)
    
    def export_config(self, format: str = None) -> str:
        """Exporta la configuración en el formato especificado"""
        return "\n".join(self.config_sections)
    
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
