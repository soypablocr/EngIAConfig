import json
from config_generator import NetworkConfigGenerator

generator = NetworkConfigGenerator()

test_params = {
    "site_info": {
        "name": "ADVANCED-SITE",
        "customer": "Advanced Corp",
        "location": "Costa Rica",
        "timezone": "America/Costa_Rica"
    },
    "device": {
        "vendor": "fortinet",
        "model": "FortiGate 100F",
        "firmware_version": "7.4.1"
    },
    "wan_interfaces": [
        {
            "interface_name": "wan1",
            "ip_address": "1.1.1.1",
            "subnet_mask": "255.255.255.0",
            "gateway": "1.1.1.254",
            "bandwidth_mbps": 100,
            "isp_name": "ISP1",
            "priority": "primary"
        },
        {
            "interface_name": "wan2",
            "ip_address": "2.2.2.2",
            "subnet_mask": "255.255.255.0",
            "gateway": "2.2.2.254",
            "bandwidth_mbps": 50,
            "isp_name": "ISP2",
            "priority": "secondary"
        }
    ],
    "lan_interfaces": [
        {
            "interface_name": "lan",
            "ip_address": "192.168.1.1",
            "subnet_mask": "255.255.255.0",
            "vlan_id": 1,
            "dhcp_enabled": True,
            "dhcp_range_start": "192.168.1.100",
            "dhcp_range_end": "192.168.1.200"
        }
    ],
    "policy_template": "standard",
    "webfilter_categories": [2, 3, 57],
    "whitelist": [
        {"name": "WEB-SERVER-1", "address": "10.0.0.50/32"},
        {"name": "OFFICE-NETWORK", "address": "172.16.0.0/24"},
        {"name": "GOOGLE-AUTH", "address": "accounts.google.com"}
    ],
    "custom_policies": [
        {
            "name": "Permit-Admin-Access",
            "srcintf": "lan",
            "dstintf": "wan1",
            "srcaddr": ["OFFICE-NETWORK", "WEB-SERVER-1"],
            "dstaddr": "all",
            "action": "accept"
        }
    ],
    "sdwan_health_checks": [
        {
            "name": "Google-DNS",
            "server": "8.8.8.8",
            "protocol": "dns"
        }
    ]
}

result = generator.generate(test_params)

if result['success']:
    print("Generation successful!")
    print("\n--- Whitelist Section ---")
    if "# --- Whitelist / Address Objects ---" in result['content']:
        print("Found Whitelist section")
    
    print("\n--- Dynamic Webfilter Section ---")
    if "set category 2 3 57" in result['content']:
        print("Found Dynamic Webfilter with categories 2 3 57")
    
    print("\n--- Custom Policies Section ---")
    if "set srcaddr \"OFFICE-NETWORK\" \"WEB-SERVER-1\"" in result['content']:
        print("Found Custom Policy correctly referencing multiple Whitelist objects")
        
    print("\n--- SD-WAN Health Checks ---")
    if "edit \"Google-DNS\"" in result['content']:
        print("Found Custom Health Check")
    
    # Save for manual review if needed
    with open('test_fortinet_refined_result.txt', 'w') as f:
        f.write(result['content'])
        print("\nFull config saved to test_fortinet_refined_result.txt")
else:
    print("Generation failed!")
    print("\nErrors:", result['errors'])
