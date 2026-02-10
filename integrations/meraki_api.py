import meraki
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class MerakiIntegration:
    """Utility to interact with Meraki Dashboard API"""
    
    def __init__(self, api_key: str):
        self.dashboard = meraki.DashboardAPI(api_key, suppress_logging=True)
        
    def push_configuration(self, network_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pushes a generated JSON configuration to a Meraki Network.
        Note: This is a simplified implementation for proof-of-concept.
        """
        results = {"success": True, "details": []}
        
        try:
            # Example: Update appliance settings
            if "appliance" in config:
                # Update L3 Firewall rules
                if "l3FirewallRules" in config["appliance"]:
                    logger.info(f"Updating L3 Firewall rules for network {network_id}")
                    self.dashboard.appliance.updateNetworkApplianceFirewallL3FirewallRules(
                        network_id, 
                        rules=config["appliance"]["l3FirewallRules"]
                    )
                    results["details"].append("Updated L3 Firewall rules")
                
                # Update VLANs
                if "vlans" in config["appliance"]:
                    for vlan in config["appliance"]["vlans"]:
                        vlan_id = vlan.get("id")
                        logger.info(f"Updating/Creating VLAN {vlan_id} in network {network_id}")
                        try:
                            self.dashboard.appliance.updateNetworkApplianceVlan(
                                network_id, vlan_id, **vlan
                            )
                            results["details"].append(f"Updated VLAN {vlan_id}")
                        except meraki.APIError as e:
                            # If not found, create (simplified logic)
                            if e.status == 404:
                                self.dashboard.appliance.createNetworkApplianceVlan(
                                    network_id, **vlan
                                )
                                results["details"].append(f"Created VLAN {vlan_id}")
                            else:
                                raise e

            return results
            
        except meraki.APIError as e:
            logger.error(f"Meraki API Error: {str(e)}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error during Meraki push: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_networks(self, organization_id: str):
        """Helper to list networks in an organization"""
        return self.dashboard.organizations.getOrganizationNetworks(organization_id)
