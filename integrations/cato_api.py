import requests
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class CatoIntegration:
    """Utility to interact with Cato Networks GraphQL API"""
    
    CATO_API_URL = "https://api.catonetworks.com/api/v1/graphql2"
    
    def __init__(self, api_key: str, account_id: str):
        self.api_key = api_key
        self.account_id = account_id
        self.headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
    
    def execute_mutation(self, mutation: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a GraphQL mutation against Cato API"""
        payload = {
            "query": mutation,
            "variables": variables
        }
        
        try:
            response = requests.post(
                self.CATO_API_URL, 
                headers=self.headers, 
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"Cato API HTTP Error: {str(e)} | Response: {e.response.text}")
            return {"errors": [{"message": str(e)}]}
        except Exception as e:
            logger.error(f"Unexpected error calling Cato API: {str(e)}")
            return {"errors": [{"message": str(e)}]}

    def push_site_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pushes a generated configuration to Cato as multiple mutations.
        Simplified PoC logic.
        """
        results = {"success": True, "details": []}
        
        if "cato_graphql_mutations" not in config:
             return {"success": False, "error": "Invalid Cato configuration format"}
             
        mutations = config["cato_graphql_mutations"]
        
        # In a real implementation, we would iterate and execute each mutation
        # For PoC, we expect a 'addSocketSite' mutation structure
        for item in mutations:
             mutation_name = item.get("name")
             mutation_query = item.get("query")
             variables = item.get("variables", {})
             # Inject account ID if needed
             variables["accountId"] = self.account_id
             
             logger.info(f"Executing Cato mutation: {mutation_name}")
             response = self.execute_mutation(mutation_query, variables)
             
             if "errors" in response:
                 results["success"] = False
                 results["details"].append(f"Error in {mutation_name}: {response['errors'][0].get('message')}")
             else:
                 results["details"].append(f"Successfully executed {mutation_name}")
                 
        return results
