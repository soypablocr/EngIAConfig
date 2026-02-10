import pytest
from config_generator import NetworkConfigGenerator
from schemas import NetworkParams

def test_cidr_mask_validation(generator):
    """Test CIDR notation support in mask validation"""
    data = {
        "site_info": {"name": "CIDR-TEST"},
        "device": {"vendor": "fortinet", "model": "60F", "firmware_version": "7.4"},
        "wan_interfaces": [
            {
                "interface_name": "wan1",
                "ip_address": "1.1.1.10",
                "subnet_mask": "/24", # CIDR notation
                "gateway": "1.1.1.1"
            }
        ],
        "lan_interfaces": [
            {
                "interface_name": "lan1",
                "ip_address": "192.168.10.1",
                "subnet_mask": "24", # Numeric CIDR
                "dhcp_enabled": False
            }
        ]
    }
    
    valid, errors, warnings = generator.validate_params(data)
    assert valid is True
    
    # Verify it was converted to dotted decimal internally
    params = NetworkParams(**data)
    assert params.wan_interfaces[0].subnet_mask == "255.255.255.0"
    assert params.lan_interfaces[0].subnet_mask == "255.255.255.0"

def test_pydantic_validation_success(generator):
    """Test standard Pydantic validation with correct data"""
    valid_data = {
        "site_info": {
            "name": "TEST-SITE",
            "customer": "Test Customer",
            "location": "Test Location",
            "timezone": "UTC"
        },
        "device": {
            "vendor": "fortinet",
            "model": "FortiGate 60F",
            "firmware_version": "7.4.2"
        },
        "wan_interfaces": [
            {
                "interface_name": "wan1",
                "ip_address": "203.0.113.10",
                "subnet_mask": "255.255.255.252",
                "gateway": "203.0.113.9",
                "bandwidth_mbps": 100,
                "isp_name": "ISP1",
                "priority": "primary"
            }
        ],
        "lan_interfaces": [
            {
                "interface_name": "lan",
                "ip_address": "192.168.1.1",
                "subnet_mask": "255.255.255.0",
                "vlan_id": 10,
                "vlan_name": "DATA",
                "dhcp_enabled": True,
                "dhcp_range_start": "192.168.1.100",
                "dhcp_range_end": "192.168.1.200"
            }
        ],
        "services": {
            "dns_servers": ["8.8.8.8", "8.8.4.4"],
            "ntp_servers": ["pool.ntp.org"]
        },
        "policy_template": "standard"
    }
    
    valid, errors, warnings = generator.validate_params(valid_data)
    assert valid is True
    assert len(errors) == 0

def test_pydantic_validation_failure(generator):
    """Test Pydantic validation failure with invalid IP"""
    invalid_data = {
        "site_info": {"name": "TEST"},
        "device": {"vendor": "fortinet", "model": "60F", "firmware_version": "7.4"},
        "wan_interfaces": [
            {
                "interface_name": "wan1",
                "ip_address": "999.999.999.999", # Invalid IP
                "subnet_mask": "255.255.255.0",
                "gateway": "1.1.1.1"
            }
        ]
    }
    
    valid, errors, warnings = generator.validate_params(invalid_data)
    assert valid is False
    assert any("wan_interfaces" in e for e in errors)

def test_generate_fortinet(generator):
    """Test generating a Fortinet CLI config"""
    data = {
        "site_info": {"name": "SITE1"},
        "device": {"vendor": "fortinet", "model": "FortiGate 40F", "firmware_version": "7.4.2"},
        "wan_interfaces": [
            {
                "interface_name": "wan1",
                "ip_address": "203.0.113.10",
                "subnet_mask": "255.255.255.252",
                "gateway": "203.0.113.9"
            }
        ],
        "lan_interfaces": [
            {"interface_name": "internal", "ip_address": "192.168.1.1", "subnet_mask": "255.255.255.0"}
        ]
    }
    
    result = generator.generate(data)
    assert result['success'] is True
    assert result['format'] == 'cli'
    assert 'config system global' in result['content']
    assert 'SITE1' in result['content']

def test_generate_meraki(generator):
    """Test generating a Meraki JSON config"""
    data = {
        "site_info": {"name": "MERAKI-SITE"},
        "device": {"vendor": "meraki", "model": "MX67", "firmware_version": "MX 18.2"},
        "wan_interfaces": [
            {
                "interface_name": "wan1",
                "ip_address": "203.0.113.10",
                "subnet_mask": "255.255.255.252",
                "gateway": "203.0.113.9"
            }
        ],
        "lan_interfaces": []
    }
    
    result = generator.generate(data)
    assert result['success'] is True
    assert result['format'] == 'json'
    assert 'meraki_dashboard_config' in result['content']

def test_generate_velocloud(generator):
    """Test generating a Velocloud JSON config"""
    data = {
        "site_info": {"name": "VELO-SITE"},
        "device": {"vendor": "velocloud", "model": "Edge 610", "firmware_version": "5.2.0"},
        "wan_interfaces": [
            {
                "interface_name": "GE1",
                "ip_address": "203.0.113.10",
                "subnet_mask": "255.255.255.252",
                "gateway": "203.0.113.9"
            }
        ],
        "lan_interfaces": [
            {
                "interface_name": "LAN",
                "ip_address": "192.168.10.1",
                "subnet_mask": "255.255.255.0",
                "dhcp_enabled": False
            }
        ]
    }
    
    result = generator.generate(data)
    assert result['success'] is True
    assert result['format'] == 'json'
    assert 'velocloud_vco_config' in result['content']

def test_generate_bigleaf(generator):
    """Test generating a Bigleaf JSON config"""
    data = {
        "site_info": {"name": "BIG-SITE"},
        "device": {"vendor": "bigleaf", "model": "Bigleaf Edge 100", "firmware_version": "v3.5.0"},
        "wan_interfaces": [
            {
                "interface_name": "wan1",
                "ip_address": "203.0.113.10",
                "subnet_mask": "255.255.255.252",
                "gateway": "203.0.113.9"
            }
        ],
        "lan_interfaces": []
    }
    
    result = generator.generate(data)
    assert result['success'] is True
    assert result['format'] == 'json'
    assert 'bigleaf_portal_provisioning' in result['content']

def test_generate_cato(generator):
    """Test generating a Cato GraphQL config"""
    data = {
        "site_info": {"name": "CATO-SITE"},
        "device": {"vendor": "cato", "model": "Socket X1500", "firmware_version": "20.0"},
        "wan_interfaces": [
            {
                "interface_name": "wan1",
                "ip_address": "203.0.113.10",
                "subnet_mask": "255.255.255.252",
                "gateway": "203.0.113.9"
            }
        ],
        "lan_interfaces": []
    }
    
    result = generator.generate(data)
    assert result['success'] is True
    assert result['format'] == 'graphql'
    assert 'cato_graphql_mutations' in result['content']
