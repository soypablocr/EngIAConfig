from .base import VendorConfig
from typing import List, Tuple
from schemas import NetworkParams, WanInterface, LanInterface

class FortinetConfig(VendorConfig):
    """Generador de configuración para FortiGate"""
    
    VENDOR_NAME = "fortinet"
    OUTPUT_FORMAT = "cli"
    SUPPORTED_MODELS = [
        "FortiGate 40F", "FortiGate 60F", "FortiGate 70F",
        "FortiGate 80F", "FortiGate 100F", "FortiGate 200F",
        "FortiGate 400F", "FortiGate 600F"
    ]
    SUPPORTED_FIRMWARES = [
        "7.0.12", "7.2.5", "7.4.1"
    ]
    
    TIMEZONE_CODES = {
        "America/Costa_Rica": "12",
        "America/New_York": "12",
        "America/Chicago": "11",
        "America/Denver": "02",
        "America/Los_Angeles": "04",
        "UTC": "80"
    }
    
    def generate_base_config(self, params: NetworkParams):
        self.params = params
        site = params.site_info
        services = params.services
        
        tz_code = self.TIMEZONE_CODES.get(site.timezone, '80')
        dns_servers = services.dns_servers if services.dns_servers else ["8.8.8.8", "8.8.4.4"]
        dns_primary = dns_servers[0]
        dns_secondary = dns_servers[1] if len(dns_servers) > 1 else "8.8.4.4"
        ntp_server = services.ntp_servers[0] if services.ntp_servers else "pool.ntp.org"
        
        config = f'''# ============================================
# FortiGate Configuration
# Site: {site.name}
# Customer: {site.customer}
# Firmware: {params.device.firmware_version}
# Generated automatically - Review before applying
# ============================================

# --- System Global Settings ---
config system global
    set hostname "{site.name}"
    set timezone {tz_code}
    set admin-sport 8443
    set admin-ssh-port 22
    set admintimeout 30
    set gui-theme mariner
end

# --- DNS Configuration ---
config system dns
    set primary {dns_primary}
    set secondary {dns_secondary}
end

# --- NTP Configuration ---
config system ntp
    set ntpsync enable
    set server-mode disable
    config ntpserver
        edit 1
            set server "{ntp_server}"
        next
    end
end

# --- SNMP Configuration ---
config system snmp sysinfo
    set status enable
    set description "{site.customer} - {site.name}"
    set location "{site.location}"
end
'''
        self.config_sections.append(config)

    def apply_wan_config(self, wan_params: List[WanInterface]):
        config = "\n# --- WAN Interface Configuration ---\n"
        
        for idx, wan in enumerate(wan_params):
            iface = wan.interface_name
            priority = 10 if wan.priority == 'primary' else 20
            
            config += f'''
config system interface
    edit "{iface}"
        set mode static
        set ip {wan.ip_address} {wan.subnet_mask}
        set allowaccess ping https ssh snmp
        set alias "{wan.isp_name or f'WAN-{idx + 1}'}"
        set role wan
        set estimated-upstream-bandwidth {int(wan.bandwidth_mbps or 100) * 1000}
        set estimated-downstream-bandwidth {int(wan.bandwidth_mbps or 100) * 1000}
    next
end

config router static
    edit {idx + 1}
        set gateway {wan.gateway}
        set device "{iface}"
        set priority {priority}
        set comment "{wan.isp_name or f'Route via WAN-{idx + 1}'}"
    next
end
'''
        
        # SD-WAN si hay múltiples WANs o si se definieron health checks
        if len(wan_params) > 1 or getattr(self.params, 'sdwan_health_checks', []):
            config += self._generate_enhanced_sdwan_config(wan_params)
        
        self.config_sections.append(config)

    def _generate_enhanced_sdwan_config(self, wan_params: List[WanInterface]) -> str:
        members = ""
        for idx, wan in enumerate(wan_params):
            iface = wan.interface_name
            members += f'''
        edit {idx + 1}
            set interface "{iface}"
            set gateway {wan.gateway}
        next
'''
        
        health_checks = ""
        hc_params = getattr(self.params, 'sdwan_health_checks', [])
        if not hc_params:
            # Default health check
            health_checks = '''
        edit "Default_DNS"
            set server "8.8.8.8"
            set protocol dns
            set interval 1000
            set failtime 5
            set recoverytime 5
            set members 0
        next
'''
        else:
            for hc in hc_params:
                health_checks += f'''
        edit "{hc.name}"
            set server "{hc.server}"
            set protocol {hc.protocol}
            set interval {hc.interval}
            set failtime {hc.failtime}
            set recoverytime {hc.recoverytime}
            set members 0
        next
'''

        return f'''
# --- SD-WAN Configuration ---
config system sdwan
    set status enable
    config zone
        edit "virtual-wan-link"
        next
    end
    config members
{members}    end
    config health-check
{health_checks}    end
end
'''

    def apply_lan_config(self, lan_params: List[LanInterface]):
        config = "\n# --- LAN Interface Configuration ---\n"
        dhcp_id = 1
        
        for lan in lan_params:
            iface = lan.interface_name
            vlan_id = lan.vlan_id
            
            if vlan_id and vlan_id > 1:
                vlan_name = f"VLAN{vlan_id}"
                config += f'''
config system interface
    edit "{vlan_name}"
        set vdom "root"
        set vlanid {vlan_id}
        set interface "{lan.interface_name}"
        set ip {lan.ip_address} {lan.subnet_mask}
        set allowaccess ping https ssh
        set role lan
        set device-identification enable
    next
end
'''
                iface = vlan_name
            else:
                config += f'''
config system interface
    edit "{iface}"
        set mode static
        set ip {lan.ip_address} {lan.subnet_mask}
        set allowaccess ping https ssh
        set role lan
        set device-identification enable
    next
end
'''
            
            # DHCP Server
            if lan.dhcp_enabled:
                dns_list = getattr(self.params.services, 'dns_servers', []) if self.params.services else []
                dns1 = dns_list[0] if dns_list else "8.8.8.8"
                
                config += f'''
config system dhcp server
    edit {dhcp_id}
        set interface "{iface}"
        set default-gateway {lan.ip_address}
        set netmask {lan.subnet_mask}
        set dns-server1 {dns1}
        set lease-time 86400
        config ip-range
            edit 1
                set start-ip {lan.dhcp_range_start}
                set end-ip {lan.dhcp_range_end}
            next
        end
    next
end
'''
                dhcp_id += 1
        
        self.config_sections.append(config)

    def apply_policies(self, policy_set: str):
        # 1. Whitelist (Address Objects)
        whitelist_config = ""
        whitelist_items = getattr(self.params, 'whitelist', [])
        if whitelist_items:
            whitelist_config = "\n# --- Whitelist / Address Objects ---\nconfig firewall address\n"
            for item in whitelist_items:
                # Basic detection for FQDN vs Subnet
                if any(char.isalpha() for char in item.address) and not " " in item.address:
                    whitelist_config += f'''    edit "{item.name}"
        set type fqdn
        set fqdn "{item.address}"
    next
'''
                else:
                    addr = item.address
                    if "/" in addr:
                        # Convert CIDR
                        import ipaddress
                        net = ipaddress.IPv4Network(addr, strict=False)
                        addr = f"{net.network_address} {net.netmask}"
                    elif " " not in addr:
                        # Assume host /32
                        addr = f"{addr} 255.255.255.255"
                    
                    whitelist_config += f'''    edit "{item.name}"
        set subnet {addr}
    next
'''
            whitelist_config += "end\n"
            self.config_sections.append(whitelist_config)

        # 2. Template Policies (including dynamic webfilter if needed)
        base_configs = {
            'basic': self._basic_policies(),
            'standard': self._standard_policies(),
            'advanced': self._advanced_policies(),
            'custom': ""
        }
        
        config = base_configs.get(policy_set, base_configs['basic'])
        
        # Override webfilter if custom categories are provided
        wf_categories = getattr(self.params, 'webfilter_categories', [])
        if wf_categories and policy_set in ['standard', 'advanced']:
            # Replace the static profile if it exists in the template or just append a new one
            wf_config = self._generate_dynamic_webfilter(wf_categories)
            config += wf_config
            
        self.config_sections.append(config)

        # 3. Custom Custom Policies
        custom_policies = getattr(self.params, 'custom_policies', [])
        if custom_policies:
            custom_config = "\n# --- User Defined Custom Policies ---\nconfig firewall policy\n"
            policy_id = 1000 
            for p in custom_policies:
                # Handle lists for source/destination addresses
                srcaddr = p.srcaddr if isinstance(p.srcaddr, list) else [p.srcaddr]
                dstaddr = p.dstaddr if isinstance(p.dstaddr, list) else [p.dstaddr]
                
                src_str = " ".join([f'"{s}"' for s in srcaddr])
                dst_str = " ".join([f'"{d}"' for d in dstaddr])

                custom_config += f'''    edit {policy_id}
        set name "{p.name}"
        set srcintf "{p.srcintf}"
        set dstintf "{p.dstintf}"
        set srcaddr {src_str}
        set dstaddr {dst_str}
        set action {p.action}
        set schedule "always"
        set service "{p.service}"
        set nat {"enable" if p.nat else "disable"}
        set logtraffic all
    next
'''
                policy_id += 1
            custom_config += "end\n"
            self.config_sections.append(custom_config)

    def _generate_dynamic_webfilter(self, categories: List[int]) -> str:
        cat_str = " ".join(map(str, categories))
        return f'''
# --- Dynamic Web Filtering Profile ---
config webfilter profile
    edit "standard-webfilter"
        set comment "Customized dynamic web filtering"
        config ftgd-wf
            config filters
                edit 1
                    set category {cat_str}
                    set action block
                next
            end
        end
    next
end
'''

    def _basic_policies(self) -> str:
        return '''
# --- Basic Firewall Policies ---
config firewall address
    edit "RFC1918_10"
        set subnet 10.0.0.0 255.0.0.0
    next
    edit "RFC1918_172"
        set subnet 172.16.0.0 255.240.0.0
    next
    edit "RFC1918_192"
        set subnet 192.168.0.0 255.255.0.0
    next
end

config firewall addrgrp
    edit "RFC1918_ALL"
        set member "RFC1918_10" "RFC1918_172" "RFC1918_192"
    next
end

config firewall policy
    edit 1
        set name "LAN-to-WAN-Allow"
        set srcintf "any"
        set dstintf "any"
        set srcaddr "all"
        set dstaddr "all"
        set action accept
        set schedule "always"
        set service "ALL"
        set nat enable
        set logtraffic all
    next
end
'''

    def _standard_policies(self) -> str:
        return self._basic_policies() + '''
# --- Standard Security Profiles ---
config webfilter profile
    edit "standard-webfilter"
        set comment "Standard web filtering profile"
        config ftgd-wf
            config filters
                edit 1
                    set category 2 7 8 9 11 14 15 16 57 63 64 65 66 67
                    set action block
                next
            end
        end
    next
end
'''

    def _advanced_policies(self) -> str:
        return self._standard_policies() + '''
# --- Advanced Security Profiles ---
config ips sensor
    edit "standard-ips"
        config entries
            edit 1
                set severity high critical
                set action block
                set status enable
            next
        end
    next
end
'''

    def validate_custom_rules(self, params: NetworkParams) -> Tuple[bool, List[str], List[str]]:
        errors = []
        warnings = []
        
        if len(params.wan_interfaces) > 4:
            errors.append(f"Fortinet soporta un máximo de 4 interfaces WAN (se recibieron {len(params.wan_interfaces)})")
        
        if "40F" in params.device.model and len(params.wan_interfaces) > 2:
            warnings.append(f"El modelo {params.device.model} típicamente tiene recursos limitados para más de 2 WANs")
            
        return len(errors) == 0, errors, warnings
