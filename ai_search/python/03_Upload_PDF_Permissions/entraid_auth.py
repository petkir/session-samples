"""
Entra ID authentication and authorization module for group-based document permissions.
Handles user authentication, group membership validation, and permission filtering.
"""
import asyncio
from typing import List, Dict, Optional, Set
import json
from datetime import datetime, timedelta
import time

import requests
from msal import ConfidentialClientApplication
from azure.identity import ClientSecretCredential
import structlog

from config import settings

logger = structlog.get_logger(__name__)


class EntraIDAuthManager:
    """Handles Entra ID authentication and group-based authorization."""
    
    def __init__(self):
        """Initialize the Entra ID auth manager."""
        self.tenant_id = settings.azure_tenant_id
        self.client_id = settings.azure_client_id
        self.client_secret = settings.azure_client_secret
        self.authority = settings.azure_authority
        
        # Initialize MSAL client
        self.app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority
        )
        
        # Initialize Azure credential for Graph API
        self.credential = ClientSecretCredential(
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            client_secret=self.client_secret
        )
        
        # Cache for group memberships (to avoid repeated API calls)
        self._group_cache: Dict[str, Dict] = {}
        self._cache_expiry = timedelta(minutes=30)
    
    async def get_access_token(self) -> str:
        """
        Get access token for Microsoft Graph API using client credentials flow.
        
        Returns:
            Access token string
            
        Raises:
            Exception: If token acquisition fails
        """
        try:
            # Use client credentials flow for service-to-service authentication
            result = self.app.acquire_token_for_client(scopes=settings.graph_scopes)
            
            if "access_token" in result:
                logger.info("Successfully acquired access token")
                return result["access_token"]
            else:
                error_msg = result.get("error_description", "Unknown error")
                logger.error("Failed to acquire access token", error=error_msg)
                raise Exception(f"Token acquisition failed: {error_msg}")
                
        except Exception as e:
            logger.error("Exception during token acquisition", error=str(e))
            raise
    
    async def get_user_groups(self, user_id: str) -> List[str]:
        """
        Get list of group IDs that a user belongs to.
        
        Args:
            user_id: User's object ID or UPN
            
        Returns:
            List of group IDs the user belongs to
        """
        try:
            # Check cache first
            cache_key = f"user_groups_{user_id}"
            if cache_key in self._group_cache:
                cached_data = self._group_cache[cache_key]
                if datetime.now() - cached_data["timestamp"] < self._cache_expiry:
                    logger.debug("Using cached group data", user_id=user_id)
                    return cached_data["groups"]
            
            # Get fresh access token
            token = await self.get_access_token()
            
            # Call Microsoft Graph API to get user's groups
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Get groups using the member-of endpoint
            url = f"https://graph.microsoft.com/v1.0/users/{user_id}/memberOf"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                groups = []
                
                # Extract group IDs from the response
                for item in data.get("value", []):
                    if item.get("@odata.type") == "#microsoft.graph.group":
                        groups.append(item["id"])
                
                # Cache the result
                self._group_cache[cache_key] = {
                    "groups": groups,
                    "timestamp": datetime.now()
                }
                
                logger.info("Retrieved user groups", user_id=user_id, group_count=len(groups))
                return groups
                
            else:
                error_msg = f"Failed to get user groups: {response.status_code} - {response.text}"
                logger.error(error_msg, user_id=user_id)
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error("Exception getting user groups", user_id=user_id, error=str(e))
            raise
    
    async def validate_user_access(self, user_id: str, required_groups: List[str]) -> bool:
        """
        Validate if a user has access to documents based on group membership.
        
        Args:
            user_id: User's object ID or UPN
            required_groups: List of group IDs required for access
            
        Returns:
            True if user has access, False otherwise
        """
        try:
            if not required_groups:
                # If no groups are required, allow access
                return True
            
            # Get user's groups
            user_groups = await self.get_user_groups(user_id)
            
            # Check if user belongs to any of the required groups
            user_groups_set = set(user_groups)
            required_groups_set = set(required_groups)
            
            has_access = bool(user_groups_set.intersection(required_groups_set))
            
            logger.info(
                "User access validation",
                user_id=user_id,
                has_access=has_access,
                user_groups_count=len(user_groups),
                required_groups_count=len(required_groups)
            )
            
            return has_access
            
        except Exception as e:
            logger.error("Exception validating user access", user_id=user_id, error=str(e))
            # In case of error, deny access for security
            return False
    
    async def get_user_accessible_groups(self, user_id: str) -> List[str]:
        """
        Get list of document access groups that the user belongs to.
        
        Args:
            user_id: User's object ID or UPN
            
        Returns:
            List of group IDs the user can access documents for
        """
        try:
            # Get user's groups
            user_groups = await self.get_user_groups(user_id)
            
            # Get configured document access groups
            document_groups = settings.document_access_groups_list
            
            # Find intersection of user's groups and document access groups
            user_groups_set = set(user_groups)
            document_groups_set = set(document_groups)
            
            accessible_groups = list(user_groups_set.intersection(document_groups_set))
            
            logger.info(
                "User accessible groups",
                user_id=user_id,
                accessible_groups_count=len(accessible_groups)
            )
            
            return accessible_groups
            
        except Exception as e:
            logger.error("Exception getting user accessible groups", user_id=user_id, error=str(e))
            return []
    
    async def get_group_info(self, group_id: str) -> Dict:
        """
        Get information about a specific group.
        
        Args:
            group_id: Group's object ID
            
        Returns:
            Dictionary containing group information
        """
        try:
            # Check cache first
            cache_key = f"group_info_{group_id}"
            if cache_key in self._group_cache:
                cached_data = self._group_cache[cache_key]
                if datetime.now() - cached_data["timestamp"] < self._cache_expiry:
                    logger.debug("Using cached group info", group_id=group_id)
                    return cached_data["info"]
            
            # Get fresh access token
            token = await self.get_access_token()
            
            # Call Microsoft Graph API to get group info
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            url = f"https://graph.microsoft.com/v1.0/groups/{group_id}"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                group_info = response.json()
                
                # Cache the result
                self._group_cache[cache_key] = {
                    "info": group_info,
                    "timestamp": datetime.now()
                }
                
                logger.info("Retrieved group info", group_id=group_id)
                return group_info
                
            else:
                error_msg = f"Failed to get group info: {response.status_code} - {response.text}"
                logger.error(error_msg, group_id=group_id)
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error("Exception getting group info", group_id=group_id, error=str(e))
            raise
    
    def clear_cache(self):
        """Clear the authentication cache."""
        self._group_cache.clear()
        logger.info("Cleared authentication cache")
    
    def generate_security_filter(self, user_accessible_groups: List[str]) -> str:
        """
        Generate OData filter for Azure AI Search based on user's accessible groups.
        
        Args:
            user_accessible_groups: List of group IDs the user can access
            
        Returns:
            OData filter string for Azure AI Search
        """
        if not user_accessible_groups:
            # If user has no accessible groups, return filter that matches nothing
            return "document_groups/any(g: g eq 'no-access')"
        
        # Create filter that matches documents belonging to any of the user's groups
        group_filters = []
        for group_id in user_accessible_groups:
            group_filters.append(f"document_groups/any(g: g eq '{group_id}')")
        
        # Combine with OR logic
        filter_string = " or ".join(group_filters)
        
        logger.debug("Generated security filter", filter=filter_string)
        return filter_string


# Global auth manager instance
auth_manager = EntraIDAuthManager()
