from typing import Dict, Optional
from validators import ConfigValidator
from vendors.fortinet import FortinetConfig
from vendors.meraki import MerakiConfig
from vendors.velocloud import VelocloudConfig
from vendors.bigleaf import BigleafConfig
from vendors.cato import CatoConfig

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
        self.validator = ConfigValidator()
    
    def generate(self, params: dict) -> dict:
        """
        Genera configuración completa para un dispositivo
        
        Args:
            params: Diccionario con parámetros de configuración
            
        Returns:
            dict con success, errors, warnings, config, vendor, site_name
        """
        # Paso 1: Validar inputs
        is_valid, errors, warnings = self.validator.validate_all(params)
        
        if not is_valid:
            return {
                'success': False,
                'errors': errors,
                'warnings': warnings,
                'config': None,
                'vendor': None,
                'site_name': params.get('site_info', {}).get('name', 'Unknown')
            }
        
        # Paso 2: Seleccionar vendor
        vendor_name = params['device']['vendor'].lower()
        vendor_class = self.VENDOR_CLASSES.get(vendor_name)
        
        if not vendor_class:
            return {
                'success': False,
                'errors': [f"Vendor '{vendor_name}' no está implementado"],
                'warnings': [],
                'config': None,
                'vendor': vendor_name,
                'site_name': params.get('site_info', {}).get('name', 'Unknown')
            }
        
        vendor_config = vendor_class()
        
        # Paso 3: Validar modelo
        model = params['device'].get('model', '')
        if not vendor_config.validate_model(model):
            warnings.append(f"Modelo '{model}' no está en la lista de modelos soportados para {vendor_name}")
        
        # Paso 4: Generar configuración
        try:
            vendor_config.generate_base_config(params)
            vendor_config.apply_wan_config(params.get('wan_interfaces', []))
            vendor_config.apply_lan_config(params.get('lan_interfaces', []))
            vendor_config.apply_policies(params.get('policy_template', 'basic'))
            
            config_output = vendor_config.export_config()
            
            return {
                'success': True,
                'errors': [],
                'warnings': warnings,
                'config': config_output,
                'vendor': vendor_name,
                'site_name': params['site_info']['name'],
                'output_format': vendor_config.OUTPUT_FORMAT
            }
            
        except Exception as e:
            return {
                'success': False,
                'errors': [f"Error generando configuración: {str(e)}"],
                'warnings': warnings,
                'config': None,
                'vendor': vendor_name,
                'site_name': params.get('site_info', {}).get('name', 'Unknown')
            }
    
    def get_supported_vendors(self) -> list:
        """Retorna lista de vendors soportados"""
        return list(self.VENDOR_CLASSES.keys())
    
    def get_supported_models(self, vendor: str) -> list:
        """Retorna lista de modelos soportados para un vendor"""
        vendor_class = self.VENDOR_CLASSES.get(vendor.lower())
        if vendor_class:
            return vendor_class.SUPPORTED_MODELS
        return []
