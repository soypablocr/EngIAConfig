import re
import ipaddress
from typing import Dict, List, Tuple

class ConfigValidator:
    """Validador de parámetros de entrada"""
    
    VALID_VENDORS = ["fortinet", "velocloud", "meraki", "bigleaf", "cato"]
    VALID_POLICIES = ["basic", "standard", "advanced", "custom"]
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_all(self, params: dict) -> Tuple[bool, List[str], List[str]]:
        """Valida todos los parámetros"""
        self.errors = []
        self.warnings = []
        
        self._validate_site_info(params.get('site_info', {}))
        self._validate_device(params.get('device', {}))
        self._validate_wan_interfaces(params.get('wan_interfaces', []))
        self._validate_lan_interfaces(params.get('lan_interfaces', []))
        self._validate_services(params.get('services', {}))
        self._validate_policy_template(params.get('policy_template', 'basic'))
        
        return len(self.errors) == 0, self.errors, self.warnings
    
    def _validate_site_info(self, site_info: dict):
        if not site_info:
            self.errors.append("site_info es requerido")
            return
        
        if not site_info.get('name'):
            self.errors.append("site_info.name es requerido")
        elif len(site_info['name']) > 64:
            self.errors.append("site_info.name debe tener máximo 64 caracteres")
        elif not re.match(r'^[a-zA-Z0-9_-]+$', site_info['name']):
            self.warnings.append("site_info.name contiene caracteres especiales que podrían causar problemas")
        
        if not site_info.get('customer'):
            self.warnings.append("site_info.customer está vacío")
    
    def _validate_device(self, device: dict):
        if not device:
            self.errors.append("device es requerido")
            return
        
        vendor = device.get('vendor', '').lower()
        if vendor not in self.VALID_VENDORS:
            self.errors.append(f"Vendor inválido '{vendor}'. Opciones: {', '.join(self.VALID_VENDORS)}")
        
        if not device.get('model'):
            self.errors.append("device.model es requerido")
    
    def _validate_wan_interfaces(self, wan_interfaces: list):
        if not wan_interfaces:
            self.errors.append("Al menos una interfaz WAN es requerida")
            return
        
        has_primary = False
        used_ips = set()
        
        for idx, wan in enumerate(wan_interfaces):
            prefix = f"wan_interfaces[{idx}]"
            
            # Validar IP
            ip = wan.get('ip_address')
            if not ip:
                self.errors.append(f"{prefix}.ip_address es requerido")
            elif not self._is_valid_ip(ip):
                self.errors.append(f"{prefix}.ip_address '{ip}' no es válida")
            elif ip in used_ips:
                self.errors.append(f"{prefix}.ip_address '{ip}' está duplicada")
            else:
                used_ips.add(ip)
            
            # Validar subnet mask
            mask = wan.get('subnet_mask')
            if not mask:
                self.errors.append(f"{prefix}.subnet_mask es requerido")
            elif not self._is_valid_subnet_mask(mask):
                self.errors.append(f"{prefix}.subnet_mask '{mask}' no es válida")
            
            # Validar gateway
            gw = wan.get('gateway')
            if not gw:
                self.errors.append(f"{prefix}.gateway es requerido")
            elif not self._is_valid_ip(gw):
                self.errors.append(f"{prefix}.gateway '{gw}' no es válida")
            elif ip and mask and gw:
                if not self._is_in_same_subnet(ip, gw, mask):
                    self.errors.append(f"{prefix}.gateway '{gw}' no está en la misma subred que la IP")
            
            # Validar prioridad
            if wan.get('priority') == 'primary':
                has_primary = True
            
            # Validar bandwidth
            bw = wan.get('bandwidth_mbps')
            if bw and (not isinstance(bw, (int, float)) or bw <= 0):
                self.errors.append(f"{prefix}.bandwidth_mbps debe ser un número positivo")
        
        if not has_primary and len(wan_interfaces) > 1:
            self.warnings.append("No hay interfaz WAN marcada como 'primary'")
    
    def _validate_lan_interfaces(self, lan_interfaces: list):
        if not lan_interfaces:
            self.warnings.append("No hay interfaces LAN configuradas")
            return
        
        used_vlans = set()
        
        for idx, lan in enumerate(lan_interfaces):
            prefix = f"lan_interfaces[{idx}]"
            
            # Validar IP
            ip = lan.get('ip_address')
            if not ip:
                self.errors.append(f"{prefix}.ip_address es requerido")
            elif not self._is_valid_ip(ip):
                self.errors.append(f"{prefix}.ip_address '{ip}' no es válida")
            
            # Validar subnet mask
            mask = lan.get('subnet_mask')
            if not mask:
                self.errors.append(f"{prefix}.subnet_mask es requerido")
            elif not self._is_valid_subnet_mask(mask):
                self.errors.append(f"{prefix}.subnet_mask '{mask}' no es válida")
            
            # Validar VLAN
            vlan = lan.get('vlan_id')
            if vlan is not None:
                if not isinstance(vlan, int) or vlan < 1 or vlan > 4094:
                    self.errors.append(f"{prefix}.vlan_id debe estar entre 1 y 4094")
                elif vlan in used_vlans:
                    self.errors.append(f"{prefix}.vlan_id {vlan} está duplicado")
                else:
                    used_vlans.add(vlan)
            
            # Validar DHCP
            if lan.get('dhcp_enabled'):
                if not lan.get('dhcp_range_start'):
                    self.errors.append(f"{prefix}.dhcp_range_start es requerido cuando DHCP está habilitado")
                if not lan.get('dhcp_range_end'):
                    self.errors.append(f"{prefix}.dhcp_range_end es requerido cuando DHCP está habilitado")
                
                # Validar que el rango DHCP esté en la misma subred
                if ip and mask and lan.get('dhcp_range_start') and lan.get('dhcp_range_end'):
                    if not self._is_in_same_subnet(lan['dhcp_range_start'], ip, mask):
                        self.errors.append(f"{prefix}.dhcp_range_start no está en la misma subred")
                    if not self._is_in_same_subnet(lan['dhcp_range_end'], ip, mask):
                        self.errors.append(f"{prefix}.dhcp_range_end no está en la misma subred")
    
    def _validate_services(self, services: dict):
        # Validar DNS servers
        for idx, dns in enumerate(services.get('dns_servers', [])):
            if not self._is_valid_ip(dns) and not self._is_valid_hostname(dns):
                self.errors.append(f"services.dns_servers[{idx}] '{dns}' no es válido")
        
        # Validar NTP servers
        for idx, ntp in enumerate(services.get('ntp_servers', [])):
            if not self._is_valid_ip(ntp) and not self._is_valid_hostname(ntp):
                self.errors.append(f"services.ntp_servers[{idx}] '{ntp}' no es válido")
    
    def _validate_policy_template(self, policy_template: str):
        if policy_template not in self.VALID_POLICIES:
            self.errors.append(f"policy_template '{policy_template}' no es válido. Opciones: {', '.join(self.VALID_POLICIES)}")
    
    # Helpers
    def _is_valid_ip(self, ip: str) -> bool:
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def _is_valid_subnet_mask(self, mask: str) -> bool:
        try:
            parts = [int(x) for x in mask.split('.')]
            if len(parts) != 4:
                return False
            binary = ''.join([bin(x)[2:].zfill(8) for x in parts])
            return '01' not in binary  # Valid masks have all 1s then all 0s
        except (ValueError, AttributeError):
            return False
    
    def _is_valid_hostname(self, hostname: str) -> bool:
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-\.]*[a-zA-Z0-9])?$'
        return bool(re.match(pattern, hostname))
    
    def _is_in_same_subnet(self, ip1: str, ip2: str, mask: str) -> bool:
        try:
            ip1_int = int(ipaddress.ip_address(ip1))
            ip2_int = int(ipaddress.ip_address(ip2))
            mask_parts = [int(x) for x in mask.split('.')]
            mask_int = (mask_parts[0] << 24) + (mask_parts[1] << 16) + (mask_parts[2] << 8) + mask_parts[3]
            return (ip1_int & mask_int) == (ip2_int & mask_int)
        except ValueError:
            return False
