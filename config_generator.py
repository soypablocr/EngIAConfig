from typing import Dict, Optional, List, Tuple
from schemas import NetworkParams
from output.artifact import ConfigArtifact
from vendors.fortinet import FortinetConfig
from vendors.meraki import MerakiConfig
from vendors.velocloud import VelocloudConfig
from vendors.bigleaf import BigleafConfig
from vendors.cato import CatoConfig
from pydantic import ValidationError

class NetworkConfigGenerator:
    """Motor principal para generación de configuraciones"""
    
    VENDOR_CLASSES = {
        'fortinet': FortinetConfig,
        'meraki': MerakiConfig,
        'velocloud': VelocloudConfig,
        'bigleaf': BigleafConfig,
        'cato': CatoConfig
    }
    
    def __init__(self):
        # We don't need ConfigValidator anymore as Pydantic handles it
        pass
    
    def validate_params(self, params_dict: dict) -> Tuple[bool, List[str], List[str]]:
        """Valida parámetros usando Pydantic"""
        try:
            NetworkParams(**params_dict)
            return True, [], []
        except ValidationError as e:
            errors = []
            for error in e.errors():
                loc = " -> ".join([str(x) for x in error['loc']])
                errors.append(f"{loc}: {error['msg']}")
            return False, errors, []
        except Exception as e:
            return False, [str(e)], []

    def generate(self, params_dict: dict) -> dict:
        """
        Genera configuración completa para un dispositivo
        """
        # Paso 1: Validar con Pydantic
        try:
            params = NetworkParams(**params_dict)
        except ValidationError as e:
            errors = []
            for error in e.errors():
                loc = " -> ".join([str(x) for x in error['loc']])
                errors.append(f"{loc}: {error['msg']}")
            return {
                'success': False,
                'errors': errors,
                'warnings': [],
                'config': None,
                'vendor': params_dict.get('device', {}).get('vendor'),
                'site_name': params_dict.get('site_info', {}).get('name', 'Unknown')
            }
        
        vendor_name = params.device.vendor.lower()
        vendor_class = self.VENDOR_CLASSES.get(vendor_name)
        
        if not vendor_class:
            return {
                'success': False,
                'errors': [f"Vendor '{vendor_name}' no está implementado"],
                'warnings': [],
                'config': None,
                'vendor': vendor_name,
                'site_name': params.site_info.name
            }
        
        vendor_config = vendor_class()
        vendor_config.params = params
        
        errors = []
        warnings = []
        
        # Paso 2: Validar modelo
        if not vendor_config.validate_model(params.device.model):
            warnings.append(f"Modelo '{params.device.model}' no está en la lista de modelos soportados para {vendor_name}")
        
        # Paso 3: Validaciones específicas del vendor
        is_custom_valid, custom_errors, custom_warnings = vendor_config.validate_custom_rules(params)
        errors.extend(custom_errors)
        warnings.extend(custom_warnings)
        
        if not is_custom_valid:
            return {
                'success': False,
                'errors': errors,
                'warnings': warnings,
                'config': None,
                'vendor': vendor_name,
                'site_name': params.site_info.name
            }
        
        # Paso 4: Generar configuración
        try:
            vendor_config.generate_base_config(params)
            vendor_config.apply_wan_config(params.wan_interfaces)
            vendor_config.apply_lan_config(params.lan_interfaces)
            vendor_config.apply_policies(params.policy_template)
            
            artifact = vendor_config.export_artifact()
            
            result = artifact.as_dict()
            result.update({
                'success': True,
                'errors': [],
                'warnings': warnings,
                'site_name': params.site_info.name
            })
            return result
            
        except Exception as e:
            return {
                'success': False,
                'errors': [f"Error generando configuración: {str(e)}"],
                'warnings': warnings,
                'config': None,
                'vendor': vendor_name,
                'site_name': params.site_info.name
            }
    
    def get_supported_vendors(self) -> list:
        return list(self.VENDOR_CLASSES.keys())
    
    def get_catalog(self) -> dict:
        """Retorna el catálogo completo de vendors, modelos y firmwares"""
        catalog = {}
        for name, cls in self.VENDOR_CLASSES.items():
            catalog[name] = {
                'models': cls.SUPPORTED_MODELS,
                'firmwares': cls.SUPPORTED_FIRMWARES
            }
        return catalog
