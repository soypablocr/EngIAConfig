from .base import VendorConfig

class FortinetConfig(VendorConfig):
    """Generador de configuración para FortiGate"""
    
    VENDOR_NAME = "fortinet"
    OUTPUT_FORMAT = "cli"
    SUPPORTED_MODELS = [
        "FortiGate 40F", "FortiGate 60F", "FortiGate 70F",
        "FortiGate 80F", "FortiGate 100F", "FortiGate 200F",
        "FortiGate 400F", "FortiGate 600F"
    ]
    
    TIMEZONE_CODES = {
        "America/Costa_Rica": "12",
        "America/New_York": "12",
        "America/Chicago": "11",
        "America/Denver": "02",
        "America/Los_Angeles": "04",
        "UTC": "80"
    }
    
    def __init__(self):
        super().__init__()
    
    def generate_base_config(self, params: dict) -> str:
        self.params = params
        site = params.get('site_info', {})
        services = params.get('services', {})
        
        tz_code = self.TIMEZONE_CODES.get(site.get('timezone', 'UTC'), '80')
        dns_primary = services.get('dns_servers', ['8.8.8.8'])[0]
        dns_secondary = services.get('dns_servers', ['8.8.8.8', '8.8.4.4'])[1] if len(services.get('dns_servers', [])) > 1 else '8.8.4.4'
        ntp_server = services.get('ntp_servers', ['pool.ntp.org'])[0]
        
        config = f'''# ============================================
# FortiGate Configuration
# Site: {site.get('name', 'UNNAMED')}
# Customer: {site.get('customer', 'UNNAMED')}
# Generated automatically - Review before applying
# ============================================

# --- System Global Settings ---
config system global
    set hostname "{site.get('name', 'FortiGate')}"
    set timezone {tz_code}
    set admin-sport 8443
    set admin-ssh-port 22
    set admintimeout 30
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
            set server {ntp_server}
        next
    end
end

# --- SNMP Configuration ---
config system snmp sysinfo
    set status enable
    set description "{site.get('customer', '')} - {site.get('name', '')}"
    set location "{site.get('location', '')}"
end
'''
        self.config_sections.append(config)
        return config
    
    def apply_wan_config(self, wan_params: list) -> str:
        config = "\n# --- WAN Interface Configuration ---\n"
        
        for idx, wan in enumerate(wan_params):
            iface = wan.get('interface_name', f'wan{idx + 1}')
            priority = 10 if wan.get('priority') == 'primary' else 20
            
            config += f'''
config system interface
    edit "{iface}"
        set mode static
        set ip {wan['ip_address']} {wan['subnet_mask']}
        set allowaccess ping https ssh snmp
        set alias "{wan.get('isp_name', f'WAN-{idx + 1}')}"
        set role wan
        set estimated-upstream-bandwidth {wan.get('bandwidth_mbps', 100) * 1000}
        set estimated-downstream-bandwidth {wan.get('bandwidth_mbps', 100) * 1000}
    next
end

config router static
    edit {idx + 1}
        set gateway {wan['gateway']}
        set device "{iface}"
        set priority {priority}
        set comment "{wan.get('isp_name', f'Route via WAN-{idx + 1}')}"
    next
end
'''
        
        # SD-WAN si hay múltiples WANs
        if len(wan_params) > 1:
            config += self._generate_sdwan_config(wan_params)
        
        self.config_sections.append(config)
        return config
    
    def _generate_sdwan_config(self, wan_params: list) -> str:
        members = ""
        for idx, wan in enumerate(wan_params):
            iface = wan.get('interface_name', f'wan{idx + 1}')
            members += f'''
        edit {idx + 1}
            set interface "{iface}"
            set gateway {wan['gateway']}
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
        edit "Default_DNS"
            set server "8.8.8.8"
            set protocol dns
            set interval 1000
            set failtime 5
            set recoverytime 5
            set members 0
        next
    end
end
'''
    
    def apply_lan_config(self, lan_params: list) -> str:
        config = "\n# --- LAN Interface Configuration ---\n"
        dhcp_id = 1
        
        for lan in lan_params:
            iface = lan.get('interface_name', 'lan')
            vlan_id = lan.get('vlan_id')
            
            if vlan_id and vlan_id > 1:
                # Configurar como VLAN interface
                config += f'''
config system interface
    edit "{lan.get('vlan_name', f'VLAN{vlan_id}')}"
        set vdom "root"
        set vlanid {vlan_id}
        set interface "lan"
        set ip {lan['ip_address']} {lan['subnet_mask']}
        set allowaccess ping https ssh
        set role lan
        set device-identification enable
    next
end
'''
                iface = lan.get('vlan_name', f'VLAN{vlan_id}')
            else:
                config += f'''
config system interface
    edit "{iface}"
        set mode static
        set ip {lan['ip_address']} {lan['subnet_mask']}
        set allowaccess ping https ssh
        set role lan
        set device-identification enable
    next
end
'''
            
            # DHCP Server
            if lan.get('dhcp_enabled'):
                dns_servers = self.params.get('services', {}).get('dns_servers', ['8.8.8.8', '8.8.4.4'])
                dns1 = dns_servers[0] if dns_servers else '8.8.8.8'
                
                config += f'''
config system dhcp server
    edit {dhcp_id}
        set interface "{iface}"
        set default-gateway {lan.get('ip_address', '192.168.1.1')}
        set dns-server1 {dns1}
        set lease-time 86400
        config ip-range
            edit 1
                set start-ip {lan.get('dhcp_range_start', '')}
                set end-ip {lan.get('dhcp_range_end', '')}
            next
        end
    next
end
'''
                dhcp_id += 1
        
        self.config_sections.append(config)
        return config
    
    def apply_policies(self, policy_set: str) -> str:
        policies = {
            'basic': self._basic_policies(),
            'standard': self._standard_policies(),
            'advanced': self._advanced_policies()
        }
        config = policies.get(policy_set, policies['basic'])
        self.config_sections.append(config)
        return config
    
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
        set srcintf "lan"
        set dstintf "virtual-wan-link"
        set srcaddr "all"
        set dstaddr "all"
        set action accept
        set schedule "always"
        set service "ALL"
        set nat enable
        set logtraffic all
    next
    edit 100
        set name "Deny-All"
        set srcintf "any"
        set dstintf "any"
        set srcaddr "all"
        set dstaddr "all"
        set action deny
        set schedule "always"
        set service "ALL"
        set logtraffic all
    next
end
'''
    
    def _standard_policies(self) -> str:
        return self._basic_policies() + '''
# --- Web Filter Profile ---
config webfilter profile
    edit "standard-webfilter"
        set comment "Standard web filtering profile"
        config ftgd-wf
            set options error-allow
            config filters
                edit 1
                    set category 2
                    set action block
                next
                edit 2
                    set category 7
                    set action block
                next
                edit 3
                    set category 8
                    set action block
                next
                edit 4
                    set category 9
                    set action block
                next
                edit 5
                    set category 11
                    set action block
                next
                edit 6
                    set category 14
                    set action block
                next
                edit 7
                    set category 15
                    set action block
                next
                edit 8
                    set category 16
                    set action block
                next
                edit 9
                    set category 57
                    set action block
                next
                edit 10
                    set category 63
                    set action block
                next
                edit 11
                    set category 64
                    set action block
                next
                edit 12
                    set category 65
                    set action block
                next
                edit 13
                    set category 66
                    set action block
                next
                edit 14
                    set category 67
                    set action block
                next
            end
        end
    next
end

# --- Application Control ---
config application list
    edit "standard-app-control"
        set comment "Standard application control"
        config entries
            edit 1
                set category 2
                set action block
            next
            edit 2
                set category 6
                set action block
            next
        end
    next
end
'''
    
    def _advanced_policies(self) -> str:
        return self._standard_policies() + '''
# --- IPS Sensor ---
config ips sensor
    edit "standard-ips"
        set comment "Standard IPS sensor"
        config entries
            edit 1
                set severity high critical
                set action block
                set status enable
            next
            edit 2
                set severity medium
                set action pass
                set log enable
                set status enable
            next
        end
    next
end

# --- Antivirus Profile ---
config antivirus profile
    edit "standard-av"
        set comment "Standard antivirus profile"
        config http
            set av-scan enable
        end
        config ftp
            set av-scan enable
        end
        config smtp
            set av-scan enable
        end
        config pop3
            set av-scan enable
        end
    next
end

# --- SSL Inspection ---
config firewall ssl-ssh-profile
    edit "certificate-inspection"
        set comment "Certificate inspection only"
        config https
            set ports 443
            set status certificate-inspection
        end
    next
end
'''
