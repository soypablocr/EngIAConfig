import pytest
from unittest.mock import MagicMock, patch
from integrations.meraki_api import MerakiIntegration

@pytest.fixture
def mock_meraki():
    with patch('meraki.DashboardAPI') as mock:
        yield mock

def test_meraki_push_success(mock_meraki):
    # Setup mock
    mock_dashboard = mock_meraki.return_value
    integration = MerakiIntegration(api_key="fake_key")
    
    config = {
        "appliance": {
            "l3FirewallRules": [{"policy": "allow", "protocol": "any"}],
            "vlans": [{"id": 10, "name": "TestVLAN"}]
        }
    }
    
    result = integration.push_configuration("n_123", config)
    
    assert result['success'] is True
    assert "Updated L3 Firewall rules" in result['details']
    assert "Updated VLAN 10" in result['details']
    
    # Verify calls
    mock_dashboard.appliance.updateNetworkApplianceFirewallL3FirewallRules.assert_called_once()
    mock_dashboard.appliance.updateNetworkApplianceVlan.assert_called_once_with(
        "n_123", 10, id=10, name="TestVLAN"
    )

def test_meraki_push_error(mock_meraki):
    # Setup mock to raise error
    mock_dashboard = mock_meraki.return_value
    mock_dashboard.appliance.updateNetworkApplianceFirewallL3FirewallRules.side_effect = Exception("API Down")
    
    integration = MerakiIntegration(api_key="fake_key")
    config = {"appliance": {"l3FirewallRules": []}}
    
    result = integration.push_configuration("n_123", config)
    
    assert result['success'] is False
    assert "API Down" in result['error']
