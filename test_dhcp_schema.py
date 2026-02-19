from schemas import NetworkParams, LanInterface, SiteInfo, Device, WanInterface
from config_generator import NetworkConfigGenerator

def test_dhcp_fields():
    print("Testing DHCP Schema...")
    
    # Valid Data with new fields
    data = {
        "site_info": {"name": "TestSite"},
        "device": {"vendor": "fortinet", "model": "60F", "firmware_version": "7.0"},
        "wan_interfaces": [
            {"interface_name": "wan1", "ip_address": "1.1.1.1", "subnet_mask": "255.255.255.252", "gateway": "1.1.1.2"}
        ],
        "lan_interfaces": [
            {
                "interface_name": "lan",
                "ip_address": "192.168.1.1",
                "subnet_mask": "255.255.255.0",
                "dhcp_enabled": True,
                "dhcp_range_start": "192.168.1.100",
                "dhcp_range_end": "192.168.1.200",
                "dhcp_gateway": "192.168.1.254",
                "dhcp_dns1": "1.1.1.1",
                "dhcp_dns2": "1.0.0.1",
                "dhcp_lease_time": 7200,
                "dhcp_options": "Option 43 ascii 'test'"
            }
        ]
    }
    
    gen = NetworkConfigGenerator()
    result = gen.generate(data)
    
    if result['success']:
        print("SUCCESS: Valid DHCP configuration passed.")
        # check if it is in the config output (Fortinet)
        config_text = result['config_data'] # Assuming result has this structure or I need to check artifact
        # Wait, generate returns dict with 'raw_config' or something?
        # Let's check config_generator.py again. It returns result.update({...}) + artifact.as_dict()
        # artifact.as_dict() returns {'content': ..., 'filename': ...}
        
        if "set default-gateway 192.168.1.254" in result['content']:
             print("VERIFIED: Gateway present in config.")
        else:
             print("FAILED: Gateway NOT found in config.")
             
        if "set dns-server1 1.1.1.1" in result['content']:
             print("VERIFIED: DNS1 present in config.")
        else:
             print("FAILED: DNS1 NOT found in config.")

    else:
        print("FAILED: Schema validation failed.")
        print(result['errors'])

if __name__ == "__main__":
    test_dhcp_fields()
