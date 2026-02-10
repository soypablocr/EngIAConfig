import pytest
from unittest.mock import MagicMock, patch
from integrations.cato_api import CatoIntegration

@pytest.fixture
def mock_requests():
    with patch('requests.post') as mock:
        yield mock

def test_cato_push_site_success(mock_requests):
    # Setup mock response
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": {"addSocketSite": {"siteId": "s_123"}}}
    mock_response.status_code = 200
    mock_requests.return_value = mock_response
    
    integration = CatoIntegration(api_key="fake_key", account_id="acc_123")
    
    config = {
        "cato_graphql_mutations": [
            {
                "name": "addSocketSite",
                "query": "mutation { addSocketSite(...) }",
                "variables": {"name": "TestSite"}
            }
        ]
    }
    
    result = integration.push_site_configuration(config)
    
    assert result['success'] is True
    assert "Successfully executed addSocketSite" in result['details']
    
    # Verify requests.post called
    mock_requests.assert_called_once()
    args, kwargs = mock_requests.call_args
    assert kwargs['headers']['x-api-key'] == "fake_key"
    assert kwargs['json']['variables']['accountId'] == "acc_123"

def test_cato_push_error(mock_requests):
    # Setup mock response with errors
    mock_response = MagicMock()
    mock_response.json.return_value = {"errors": [{"message": "Invalid API Key"}]}
    mock_response.status_code = 200 # GraphQL often returns 200 even with errors
    mock_requests.return_value = mock_response
    
    integration = CatoIntegration(api_key="wrong_key", account_id="acc_123")
    config = {
        "cato_graphql_mutations": [
            {"name": "addSocketSite", "query": "mutation...", "variables": {}}
        ]
    }
    
    result = integration.push_site_configuration(config)
    
    assert result['success'] is False
    assert "Error in addSocketSite" in result['details'][0]
