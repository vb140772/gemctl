#!/usr/bin/env python3
"""
Agentspace CLI - Manage Google Cloud Agentspace (Discovery Engine) resources.

Requirements:
    pip install google-auth google-auth-httplib2 requests click

Usage (gcloud-style CLI):
    python scripts/agentspace.py engines list --project-id PROJECT_ID --location LOCATION
    python scripts/agentspace.py engines describe ENGINE_ID --project-id PROJECT_ID --location LOCATION
    python scripts/agentspace.py data-stores list --project-id PROJECT_ID --location LOCATION
"""

import json
import os
import subprocess
import sys
from typing import Dict, List, Optional

import click
import google.auth
import google.auth.transport.requests
import requests


def get_default_project() -> Optional[str]:
    """Get default project from environment or gcloud config."""
    # Try environment variables first
    project = os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('GCLOUD_PROJECT')
    if project:
        return project
    
    # Try gcloud config
    try:
        result = subprocess.run(
            ['gcloud', 'config', 'get-value', 'project'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # Try from credentials
    try:
        credentials, project = google.auth.default()
        if project:
            return project
    except Exception:
        pass
    
    return None


def get_default_location() -> str:
    """Get default location from environment or use 'us'."""
    return os.environ.get('AGENTSPACE_LOCATION') or os.environ.get('GCLOUD_LOCATION') or 'us'


def require_project_id(f):
    """Decorator to validate project_id is provided."""
    def wrapper(*args, **kwargs):
        project_id = kwargs.get('project_id')
        if not project_id:
            click.echo("Error: --project-id is required. Set via:", err=True)
            click.echo("  1. --project-id flag", err=True)
            click.echo("  2. GOOGLE_CLOUD_PROJECT or GCLOUD_PROJECT environment variable", err=True)
            click.echo("  3. gcloud config: gcloud config set project PROJECT_ID", err=True)
            sys.exit(1)
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    wrapper.__doc__ = f.__doc__
    return wrapper


class AgentspaceClient:
    """Client for interacting with Google Cloud Agentspace (Gemini Enterprise) API."""
    
    def __init__(self, project_id: str, location: str = "global", use_service_account: bool = False):
        """
        Initialize the Agentspace client.
        
        Args:
            project_id: Google Cloud project ID
            location: Location for the resources (default: "global")
            use_service_account: Use application default credentials (service account) instead of user credentials
        """
        self.project_id = project_id
        self.location = location
        self.use_service_account = use_service_account
        
        # Set the correct regional endpoint based on location
        if location == "global":
            self.base_url = "https://discoveryengine.googleapis.com/v1"
        else:
            # For regional locations, use the regional endpoint
            # Extract region prefix (e.g., "us" from "us-central1", or use as-is)
            region_prefix = location.split("-")[0] if "-" in location else location
            self.base_url = f"https://{region_prefix}-discoveryengine.googleapis.com/v1"
        
        if use_service_account:
            # Use application default credentials (service account)
            self.credentials, self.project = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            self.session = google.auth.transport.requests.AuthorizedSession(self.credentials)
            
            # Get the service account email if available
            self.service_account = getattr(self.credentials, 'service_account_email', None)
            if not self.service_account and hasattr(self.credentials, '_service_account_email'):
                self.service_account = self.credentials._service_account_email
        else:
            # Use user credentials via gcloud auth print-access-token (default)
            self.credentials = None
            self.project = project_id
            self.session = self._create_user_auth_session(project_id)
            self.service_account = self._get_user_email()
        
        self.api_enabled = None  # Track if API is enabled
    
    def _create_user_auth_session(self, project_id: str):
        """Create a session using user credentials from gcloud auth print-access-token."""
        import requests
        
        class UserAuthSession:
            def __init__(self, project_id):
                self._token = None
                self._token_expires = None
                self._project_id = project_id
            
            def _get_access_token(self):
                """Get access token from gcloud auth print-access-token."""
                import time
                
                # Check if we have a valid cached token
                if self._token and self._token_expires and time.time() < self._token_expires:
                    return self._token
                
                try:
                    result = subprocess.run(
                        ['gcloud', 'auth', 'print-access-token'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        self._token = result.stdout.strip()
                        # Cache token for 50 minutes (tokens typically last 1 hour)
                        self._token_expires = time.time() + (50 * 60)
                        return self._token
                    else:
                        raise Exception(f"gcloud auth failed: {result.stderr}")
                except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                    raise Exception(f"Failed to get access token: {e}")
            
            def request(self, method, url, **kwargs):
                """Make authenticated request using user credentials."""
                token = self._get_access_token()
                headers = kwargs.get('headers', {})
                headers['Authorization'] = f'Bearer {token}'
                # Add quota project for user credentials
                headers['X-Goog-User-Project'] = self._project_id
                kwargs['headers'] = headers
                
                return requests.request(method, url, **kwargs)
            
            def get(self, url, **kwargs):
                return self.request('GET', url, **kwargs)
            
            def post(self, url, **kwargs):
                return self.request('POST', url, **kwargs)
            
            def delete(self, url, **kwargs):
                return self.request('DELETE', url, **kwargs)
        
        return UserAuthSession(project_id)
    
    def _get_user_email(self) -> str:
        """Get the current user email from gcloud config."""
        try:
            result = subprocess.run(
                ['gcloud', 'config', 'get-value', 'account'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            else:
                return "user-credentials"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return "user-credentials"
    
    def list_collections(self) -> List[Dict]:
        """
        List all collections in the project.
        
        Returns:
            List of collection resources
        """
        parent = f"projects/{self.project_id}/locations/{self.location}"
        url = f"{self.base_url}/{parent}/collections"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get("collections", [])
        except requests.exceptions.HTTPError as e:
            # 404 means the endpoint doesn't exist or no collections - this is OK
            if e.response is not None and e.response.status_code == 404:
                return []
            # 403 means API not enabled - report this
            if e.response is not None and e.response.status_code == 403:
                self.api_enabled = False
                return []
            print(f"Error listing collections: {e}", file=sys.stderr)
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}", file=sys.stderr)
            return []
        except requests.exceptions.RequestException as e:
            print(f"Error listing collections: {e}", file=sys.stderr)
            return []
    
    def list_engines(self, collection_id: str = "default_collection") -> List[Dict]:
        """
        List all engines (AI apps) in a collection.
        
        Args:
            collection_id: Collection ID (default: "default_collection")
            
        Returns:
            List of engine resources
        """
        parent = f"projects/{self.project_id}/locations/{self.location}/collections/{collection_id}"
        url = f"{self.base_url}/{parent}/engines"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get("engines", [])
        except requests.exceptions.HTTPError as e:
            # 404 means no engines exist - this is OK
            if e.response is not None and e.response.status_code == 404:
                return []
            # 403 means API not enabled
            if e.response is not None and e.response.status_code == 403:
                self.api_enabled = False
                return []
            print(f"Error listing engines: {e}", file=sys.stderr)
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}", file=sys.stderr)
            return []
        except requests.exceptions.RequestException as e:
            print(f"Error listing engines: {e}", file=sys.stderr)
            return []
    
    def list_data_stores(self) -> List[Dict]:
        """
        List all data stores in the project.
        
        Returns:
            List of data store resources
        """
        parent = f"projects/{self.project_id}/locations/{self.location}"
        url = f"{self.base_url}/{parent}/dataStores"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get("dataStores", [])
        except requests.exceptions.HTTPError as e:
            # 404 means no data stores exist - this is OK
            if e.response is not None and e.response.status_code == 404:
                return []
            # 403 means API not enabled
            if e.response is not None and e.response.status_code == 403:
                self.api_enabled = False
                return []
            print(f"Error listing data stores: {e}", file=sys.stderr)
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}", file=sys.stderr)
            return []
        except requests.exceptions.RequestException as e:
            print(f"Error listing data stores: {e}", file=sys.stderr)
            return []
    
    def get_engine_details(self, engine_name: str) -> Optional[Dict]:
        """
        Get detailed information about a specific engine.
        
        Args:
            engine_name: Full engine resource name
            
        Returns:
            Engine details dictionary
        """
        url = f"{self.base_url}/{engine_name}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code in [403, 404]:
                self.api_enabled = False if e.response.status_code == 403 else self.api_enabled
                return None
            print(f"Error getting engine details: {e}", file=sys.stderr)
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error getting engine details: {e}", file=sys.stderr)
            return None
    
    def get_data_store_details(self, data_store_name: str) -> Optional[Dict]:
        """
        Get detailed information about a specific data store.
        
        Args:
            data_store_name: Full data store resource name
            
        Returns:
            Data store details dictionary
        """
        url = f"{self.base_url}/{data_store_name}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code in [403, 404]:
                self.api_enabled = False if e.response.status_code == 403 else self.api_enabled
                return None
            print(f"Error getting data store details: {e}", file=sys.stderr)
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error getting data store details: {e}", file=sys.stderr)
            return None
    
    def get_data_store_schema(self, data_store_name: str) -> Optional[Dict]:
        """
        Get the schema for a data store.
        
        Args:
            data_store_name: Full data store resource name
            
        Returns:
            Schema information
        """
        url = f"{self.base_url}/{data_store_name}/schemas/default_schema"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code in [403, 404]:
                return None
            print(f"Error getting data store schema: {e}", file=sys.stderr)
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error getting data store schema: {e}", file=sys.stderr)
            return None
    
    def get_engine_full_config(self, engine_name: str) -> Dict:
        """
        Get complete configuration for an engine including all data stores.
        
        Args:
            engine_name: Full engine resource name
            
        Returns:
            Dictionary with engine and all data store configurations
        """
        print(f"\nFetching full configuration for: {engine_name}", file=sys.stderr)
        
        engine_details = self.get_engine_details(engine_name)
        if not engine_details:
            return {"error": "Could not fetch engine details"}
        
        config = {
            "engine": engine_details,
            "data_stores": []
        }
        
        # Get details for each data store
        data_store_ids = engine_details.get("dataStoreIds", [])
        print(f"Found {len(data_store_ids)} data stores", file=sys.stderr)
        
        for ds_id in data_store_ids:
            # Construct data store name from engine name
            parts = engine_name.split("/")
            project_idx = parts.index("projects")
            location_idx = parts.index("locations")
            collection_idx = parts.index("collections")
            
            ds_name = f"projects/{parts[project_idx+1]}/locations/{parts[location_idx+1]}/collections/{parts[collection_idx+1]}/dataStores/{ds_id}"
            
            print(f"  Fetching data store: {ds_id}", file=sys.stderr)
            ds_details = self.get_data_store_details(ds_name)
            if ds_details:
                # Try to get schema as well
                schema = self.get_data_store_schema(ds_name)
                if schema:
                    ds_details["schema"] = schema
                config["data_stores"].append(ds_details)
        
        return config
    
    def create_data_store_from_gcs(self, data_store_id: str, display_name: str, gcs_uri: str, 
                                 data_schema: str = "content", reconciliation_mode: str = "INCREMENTAL") -> Dict:
        """
        Create a data store and import data from GCS bucket.
        
        Args:
            data_store_id: Unique ID for the data store
            display_name: Display name for the data store
            gcs_uri: GCS URI (e.g., "gs://bucket-name/path/*")
            data_schema: Data schema type ("content", "custom", "csv", "document")
            reconciliation_mode: Import mode ("INCREMENTAL" or "FULL")
            
        Returns:
            Dictionary with operation details
        """
        try:
            # Step 1: Create the data store
            collection_name = f"projects/{self.project_id}/locations/{self.location}/collections/default_collection"
            
            data_store_config = {
                "displayName": display_name,
                "industryVertical": "GENERIC",
                "solutionTypes": ["SOLUTION_TYPE_SEARCH"],
                "contentConfig": "CONTENT_REQUIRED"
            }
            
            create_url = f"{self.base_url}/{collection_name}/dataStores?dataStoreId={data_store_id}"
            create_response = self.session.post(create_url, json=data_store_config)
            
            if create_response.status_code != 200:
                return {"error": f"Failed to create data store: {create_response.text}"}
            
            create_operation = create_response.json()
            print(f"Data store creation operation started: {create_operation.get('name', 'N/A')}", file=sys.stderr)
            
            # Step 2: Wait for data store creation to complete and get the actual data store name
            print("Waiting for data store creation to complete...", file=sys.stderr)
            actual_data_store_name = self._wait_for_data_store_creation(create_operation.get('name'), data_store_id)
            
            if not actual_data_store_name:
                # Fallback: construct the expected data store name and verify it exists
                print("Operation not found, trying to construct data store name...", file=sys.stderr)
                actual_data_store_name = f"projects/{self.project_id}/locations/{self.location}/collections/default_collection/dataStores/{data_store_id}"
                
                # Verify the data store exists
                if not self._verify_data_store_exists(actual_data_store_name):
                    return {"error": "Failed to create data store or verify its existence"}
            
            print(f"Data store created successfully: {actual_data_store_name}", file=sys.stderr)
            
            # Step 3: Import documents from GCS
            branch_name = f"{actual_data_store_name}/branches/default_branch"
            
            import_config = {
                "gcsSource": {
                    "inputUris": [gcs_uri],
                    "dataSchema": data_schema
                },
                "reconciliationMode": reconciliation_mode
            }
            
            import_url = f"{self.base_url}/{branch_name}/documents:import"
            import_response = self.session.post(import_url, json=import_config)
            
            if import_response.status_code != 200:
                return {"error": f"Failed to import documents: {import_response.text}"}
            
            import_operation = import_response.json()
            print(f"Document import operation started: {import_operation.get('name', 'N/A')}", file=sys.stderr)
            
            return {
                "data_store_name": actual_data_store_name,
                "import_operation": import_operation,
                "status": "success"
            }
            
        except Exception as e:
            return {"error": f"Error creating data store from GCS: {e}"}
    
    def _wait_for_data_store_creation(self, operation_name: str, data_store_id: str, max_wait_time: int = 300) -> Optional[str]:
        """
        Wait for data store creation operation to complete and return the actual data store name.
        
        Args:
            operation_name: Name of the create operation
            data_store_id: The data store ID we used for creation
            max_wait_time: Maximum time to wait in seconds
            
        Returns:
            Actual data store name or None if failed
        """
        import time
        
        start_time = time.time()
        check_interval = 5  # Check every 5 seconds
        
        while time.time() - start_time < max_wait_time:
            try:
                operation_url = f"{self.base_url}/{operation_name}"
                response = self.session.get(operation_url)
                
                if response.status_code == 200:
                    operation = response.json()
                    
                    if operation.get('done', False):
                        if 'error' in operation:
                            print(f"Data store creation failed: {operation['error']}", file=sys.stderr)
                            return None
                        
                        # Extract data store name from the response
                        if 'response' in operation:
                            # The response should contain the data store name
                            response_data = operation['response']
                            if 'name' in response_data:
                                return response_data['name']
                        
                        # Fallback: construct the expected data store name using the data_store_id we passed
                        # Operation name format: projects/{project}/locations/{location}/collections/{collection}/operations/create-data-store-{id}
                        # Data store name format: projects/{project}/locations/{location}/collections/{collection}/dataStores/{dataStoreId}
                        parts = operation_name.split('/')
                        if len(parts) >= 6 and parts[4] == 'collections':
                            project = parts[1]
                            location = parts[3]
                            collection = parts[5]
                            data_store_name = f"projects/{project}/locations/{location}/collections/{collection}/dataStores/{data_store_id}"
                            return data_store_name
                        
                        return None
                    else:
                        print(".", end="", flush=True, file=sys.stderr)
                        time.sleep(check_interval)
                else:
                    print(f"Error checking operation status: {response.status_code}", file=sys.stderr)
                    return None
                    
            except Exception as e:
                print(f"Error waiting for operation: {e}", file=sys.stderr)
                return None
        
        print(f"\nTimeout waiting for data store creation (>{max_wait_time}s)", file=sys.stderr)
        return None
    
    def _verify_data_store_exists(self, data_store_name: str) -> bool:
        """
        Verify that a data store exists by trying to get its details.
        
        Args:
            data_store_name: Full data store resource name
            
        Returns:
            True if data store exists, False otherwise
        """
        try:
            url = f"{self.base_url}/{data_store_name}"
            response = self.session.get(url)
            return response.status_code == 200
        except Exception:
            return False
    
    def list_documents(self, data_store_name: str, branch: str = "default_branch") -> List[Dict]:
        """
        List documents in a data store branch.
        
        Args:
            data_store_name: Full data store resource name
            branch: Branch name (default: "default_branch")
            
        Returns:
            List of document dictionaries
        """
        try:
            branch_name = f"{data_store_name}/branches/{branch}"
            url = f"{self.base_url}/{branch_name}/documents"
            
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("documents", [])
            elif response.status_code == 404:
                print(f"Branch not found: {branch_name}", file=sys.stderr)
                return []
            else:
                print(f"Error listing documents: {response.status_code} - {response.text}", file=sys.stderr)
                return []
                
        except Exception as e:
            print(f"Error listing documents: {e}", file=sys.stderr)
            return []
    
    def list_all_apps(self) -> Dict[str, List[Dict]]:
        """
        List all Agentspace apps (engines, data stores, collections).
        
        Returns:
            Dictionary with lists of different resource types
        """
        results = {
            "collections": self.list_collections(),
            "engines": [],
            "data_stores": self.list_data_stores()
        }
        
        # Try to list engines from default collection
        engines = self.list_engines("default_collection")
        if engines:
            results["engines"] = engines
        
        # If collections exist, try to list engines from each
        for collection in results["collections"]:
            collection_name = collection.get("name", "")
            collection_id = collection_name.split("/")[-1] if "/" in collection_name else collection_name
            if collection_id:
                collection_engines = self.list_engines(collection_id)
                results["engines"].extend(collection_engines)
        
        return results
    
    def create_search_engine(self, engine_id: str, display_name: str, data_store_ids: List[str], 
                           search_tier: str = "SEARCH_TIER_STANDARD") -> Dict:
        """
        Create a search engine connected to data stores.
        
        Args:
            engine_id: Unique ID for the engine
            display_name: Display name for the engine
            data_store_ids: List of data store IDs to connect
            search_tier: Search tier ("SEARCH_TIER_STANDARD" or "SEARCH_TIER_ENTERPRISE")
            
        Returns:
            Dictionary with engine creation details
        """
        try:
            collection_name = f"projects/{self.project_id}/locations/{self.location}/collections/default_collection"
            
            engine_config = {
                "displayName": display_name,
                "solutionType": "SOLUTION_TYPE_SEARCH",
                "industryVertical": "GENERIC",
                "appType": "APP_TYPE_INTRANET",
                "searchEngineConfig": {
                    "searchTier": search_tier,
                    "searchAddOns": ["SEARCH_ADD_ON_LLM"]
                },
                "commonConfig": {
                    "companyName": "BCBSMA"
                }
            }
            
            # Only add dataStoreIds if data stores are provided
            if data_store_ids:
                engine_config["dataStoreIds"] = data_store_ids
            
            create_url = f"{self.base_url}/{collection_name}/engines?engineId={engine_id}"
            create_response = self.session.post(create_url, json=engine_config)
            
            if create_response.status_code != 200:
                return {"error": f"Failed to create engine: {create_response.text}"}
            
            engine_operation = create_response.json()
            print(f"Engine creation operation started: {engine_operation.get('name', 'N/A')}", file=sys.stderr)
            
            # Wait for engine creation to complete
            print("Waiting for engine creation to complete...", file=sys.stderr)
            actual_engine_name = self._wait_for_engine_creation(engine_operation.get('name'), engine_id)
            
            if not actual_engine_name:
                # Fallback: construct the expected engine name and verify it exists
                print("Operation not found, trying to construct engine name...", file=sys.stderr)
                actual_engine_name = f"projects/{self.project_id}/locations/{self.location}/collections/default_collection/engines/{engine_id}"
                
                # Verify the engine exists
                if not self._verify_engine_exists(actual_engine_name):
                    return {"error": "Failed to create engine or verify its existence"}
            
            print(f"Engine created successfully: {actual_engine_name}", file=sys.stderr)
            
            return {
                "engine_name": actual_engine_name,
                "status": "success"
            }
            
        except Exception as e:
            return {"error": f"Error creating engine: {e}"}
    
    def _wait_for_engine_creation(self, operation_name: str, engine_id: str, max_wait_time: int = 300) -> Optional[str]:
        """
        Wait for engine creation operation to complete and return the actual engine name.
        """
        import time
        
        start_time = time.time()
        check_interval = 5  # Check every 5 seconds
        
        while time.time() - start_time < max_wait_time:
            try:
                operation_url = f"{self.base_url}/{operation_name}"
                response = self.session.get(operation_url)
                
                if response.status_code == 200:
                    operation = response.json()
                    
                    if operation.get('done', False):
                        if 'error' in operation:
                            print(f"Engine creation failed: {operation['error']}", file=sys.stderr)
                            return None
                        
                        # Extract engine name from the response
                        if 'response' in operation:
                            response_data = operation['response']
                            if 'name' in response_data:
                                return response_data['name']
                        
                        # Fallback: construct the expected engine name
                        parts = operation_name.split('/')
                        if len(parts) >= 6 and parts[4] == 'collections':
                            project = parts[1]
                            location = parts[3]
                            collection = parts[5]
                            engine_name = f"projects/{project}/locations/{location}/collections/{collection}/engines/{engine_id}"
                            return engine_name
                        
                        return None
                    else:
                        print(".", end="", flush=True, file=sys.stderr)
                        time.sleep(check_interval)
                else:
                    print(f"Error checking operation status: {response.status_code}", file=sys.stderr)
                    return None
                    
            except Exception as e:
                print(f"Error waiting for operation: {e}", file=sys.stderr)
                return None
        
        print(f"\nTimeout waiting for engine creation (>{max_wait_time}s)", file=sys.stderr)
        return None
    
    def _verify_engine_exists(self, engine_name: str) -> bool:
        """
        Verify that an engine exists by trying to get its details.
        """
        try:
            url = f"{self.base_url}/{engine_name}"
            response = self.session.get(url)
            return response.status_code == 200
        except Exception:
            return False
    
    def delete_engine(self, engine_name: str) -> Dict:
        """
        Delete a search engine.
        
        Args:
            engine_name: Full engine resource name
            
        Returns:
            Dictionary with deletion status
        """
        try:
            url = f"{self.base_url}/{engine_name}"
            response = self.session.delete(url)
            
            if response.status_code == 200:
                return {"status": "success", "message": f"Engine deleted successfully"}
            elif response.status_code == 404:
                return {"status": "error", "message": "Engine not found"}
            else:
                return {"status": "error", "message": f"Failed to delete engine: {response.text}"}
                
        except Exception as e:
            return {"status": "error", "message": f"Error deleting engine: {e}"}
    
    def delete_data_store(self, data_store_name: str) -> Dict:
        """
        Delete a data store.
        
        Args:
            data_store_name: Full data store resource name
            
        Returns:
            Dictionary with deletion status
        """
        try:
            url = f"{self.base_url}/{data_store_name}"
            response = self.session.delete(url)
            
            if response.status_code == 200:
                return {"status": "success", "message": f"Data store deleted successfully"}
            elif response.status_code == 404:
                return {"status": "error", "message": "Data store not found"}
            else:
                return {"status": "error", "message": f"Failed to delete data store: {response.text}"}
                
        except Exception as e:
            return {"status": "error", "message": f"Error deleting data store: {e}"}


def format_output(results: Dict[str, List[Dict]], output_format: str = "text") -> str:
    """
    Format the results for display.
    
    Args:
        results: Dictionary with lists of resources
        output_format: Output format ("text" or "json")
        
    Returns:
        Formatted string
    """
    if output_format == "json":
        return json.dumps(results, indent=2)
    
    # Text format
    output = []
    
    # Collections
    if results["collections"]:
        output.append("=" * 80)
        output.append("COLLECTIONS")
        output.append("=" * 80)
        for i, collection in enumerate(results["collections"], 1):
            output.append(f"\n{i}. {collection.get('name', 'N/A')}")
            if "displayName" in collection:
                output.append(f"   Display Name: {collection['displayName']}")
    else:
        output.append("No collections found.")
    
    # Engines (AI Apps)
    output.append("\n")
    if results["engines"]:
        output.append("=" * 80)
        output.append("ENGINES (AI APPS)")
        output.append("=" * 80)
        for i, engine in enumerate(results["engines"], 1):
            output.append(f"\n{i}. {engine.get('name', 'N/A')}")
            if "displayName" in engine:
                output.append(f"   Display Name: {engine['displayName']}")
            if "solutionType" in engine:
                output.append(f"   Solution Type: {engine['solutionType']}")
            if "createTime" in engine:
                output.append(f"   Created: {engine['createTime']}")
    else:
        output.append("No engines (AI apps) found.")
    
    # Data Stores
    output.append("\n")
    if results["data_stores"]:
        output.append("=" * 80)
        output.append("DATA STORES")
        output.append("=" * 80)
        for i, ds in enumerate(results["data_stores"], 1):
            output.append(f"\n{i}. {ds.get('name', 'N/A')}")
            if "displayName" in ds:
                output.append(f"   Display Name: {ds['displayName']}")
            if "contentConfig" in ds:
                output.append(f"   Content Config: {ds['contentConfig']}")
    else:
        output.append("No data stores found.")
    
    return "\n".join(output)


# Common options that can be reused
project_option = click.option(
    '--project-id',
    default=lambda: get_default_project(),
    help='Google Cloud project ID (defaults to gcloud config or $GOOGLE_CLOUD_PROJECT)'
)

location_option = click.option(
    '--location',
    default=lambda: get_default_location(),
    help='Location for resources (defaults to $AGENTSPACE_LOCATION or "us")'
)

format_option = click.option(
    '--format',
    type=click.Choice(['json', 'yaml', 'table']),
    default='table',
    show_default=True,
    help='Output format'
)

collection_option = click.option(
    '--collection',
    default='default_collection',
    show_default=True,
    help='Collection ID'
)

service_account_option = click.option(
    '--use-service-account',
    is_flag=True,
    help='Use application default credentials (service account) instead of user credentials'
)


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """Agentspace CLI - Manage Google Cloud Agentspace (Discovery Engine) resources.
    
    This tool follows gcloud-style command structure for managing Agentspace AI apps.
    """
    pass


@cli.group()
def engines():
    """Manage Agentspace engines (AI apps)."""
    pass


@cli.group()
def data_stores():
    """Manage Agentspace data stores."""
    pass


@engines.command('list')
@project_option
@location_option
@collection_option
@service_account_option
@format_option
@require_project_id
def engines_list(project_id, location, collection, use_service_account, format):
    """List all engines in a project.
    
    Example:
        python agentspace.py engines list
        python agentspace.py engines list --project-id=my-project --location=us
        python agentspace.py engines list --use-user-auth
    """
    try:
        client = AgentspaceClient(project_id, location, use_service_account)
        
        if format == 'json':
            engines_list = client.list_engines(collection)
            click.echo(json.dumps(engines_list, indent=2))
        else:
            click.echo(f"Listing engines in project: {project_id}", err=True)
            click.echo(f"Location: {location}, Collection: {collection}", err=True)
            if client.service_account:
                click.echo(f"Authenticated as: {client.service_account}", err=True)
            click.echo("", err=True)
            
            engines_list = client.list_engines(collection)
            
            if not engines_list:
                click.echo("No engines found.")
                return
            
            # Table format
            click.echo("=" * 100)
            click.echo(f"{'NAME':<60} {'DISPLAY NAME':<30} {'TYPE':<10}")
            click.echo("=" * 100)
            for engine in engines_list:
                name = engine.get('name', 'N/A').split('/')[-1]
                display_name = engine.get('displayName', 'N/A')
                solution_type = engine.get('solutionType', 'N/A').replace('SOLUTION_TYPE_', '')
                click.echo(f"{name:<60} {display_name:<30} {solution_type:<10}")
            click.echo(f"\nTotal: {len(engines_list)} engine(s)")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@engines.command('describe')
@click.argument('engine_id')
@project_option
@location_option
@collection_option
@service_account_option
@format_option
@click.option('--full', is_flag=True, help='Include all data store configurations')
@require_project_id
def engines_describe(engine_id, project_id, location, collection, use_service_account, format, full):
    """Describe a specific engine.
    
    ENGINE_ID can be just the engine ID or the full resource name.
    
    Example:
        python agentspace.py engines describe my-engine
        python agentspace.py engines describe my-engine --full
    """
    try:
        client = AgentspaceClient(project_id, location, use_service_account)
        
        # Construct full resource name if only ID provided
        if "/" not in engine_id:
            engine_name = f"projects/{project_id}/locations/{location}/collections/{collection}/engines/{engine_id}"
        else:
            engine_name = engine_id
        
        if full:
            # Get full configuration with all data stores
            if format != 'json':
                click.echo(f"Fetching full configuration for: {engine_id}", err=True)
            config = client.get_engine_full_config(engine_name)
            click.echo(json.dumps(config, indent=2))
        else:
            # Get just engine details
            engine = client.get_engine_details(engine_name)
            if not engine:
                click.echo(f"Engine not found: {engine_id}", err=True)
                sys.exit(1)
            
            if format == 'json':
                click.echo(json.dumps(engine, indent=2))
            else:
                # Human-readable format
                click.echo("=" * 80)
                click.echo(f"Engine: {engine.get('displayName', 'N/A')}")
                click.echo("=" * 80)
                click.echo(f"Name: {engine.get('name', 'N/A')}")
                click.echo(f"Solution Type: {engine.get('solutionType', 'N/A')}")
                click.echo(f"Industry Vertical: {engine.get('industryVertical', 'N/A')}")
                click.echo(f"App Type: {engine.get('appType', 'N/A')}")
                
                if 'commonConfig' in engine:
                    click.echo(f"\nCommon Config:")
                    for key, value in engine['commonConfig'].items():
                        click.echo(f"  {key}: {value}")
                
                if 'searchEngineConfig' in engine:
                    click.echo(f"\nSearch Config:")
                    sec = engine['searchEngineConfig']
                    click.echo(f"  Search Tier: {sec.get('searchTier', 'N/A')}")
                    if 'searchAddOns' in sec:
                        click.echo(f"  Search Add-ons: {', '.join(sec['searchAddOns'])}")
                
                if 'dataStoreIds' in engine:
                    click.echo(f"\nData Stores ({len(engine['dataStoreIds'])}):")
                    for ds_id in engine['dataStoreIds']:
                        click.echo(f"  - {ds_id}")
                
                if 'features' in engine:
                    features_on = [k for k, v in engine['features'].items() if 'ON' in v]
                    click.echo(f"\nFeatures ({len(features_on)}/{len(engine['features'])} enabled):")
                    for feature in features_on:
                        click.echo(f"  ✓ {feature}")
                        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@engines.command('create')
@click.argument('engine_id')
@click.argument('display_name')
@click.argument('data_store_ids', nargs=-1)
@project_option
@location_option
@collection_option
@service_account_option
@click.option('--search-tier',
              type=click.Choice(['SEARCH_TIER_STANDARD', 'SEARCH_TIER_ENTERPRISE']),
              default='SEARCH_TIER_STANDARD',
              help='Search tier (default: SEARCH_TIER_STANDARD)')
@format_option
@require_project_id
def engines_create(engine_id, display_name, data_store_ids, project_id, location, collection, use_service_account, search_tier, format):
    """Create a search engine connected to data stores.
    
    ENGINE_ID: Unique ID for the engine
    DISPLAY_NAME: Display name for the engine
    DATA_STORE_IDS: One or more data store IDs to connect
    
    Example:
        python scripts/agentspace.py engines create my-engine "My Search Engine" datastore1 datastore2
        python scripts/agentspace.py engines create my-engine "My Search Engine" datastore1 --search-tier=SEARCH_TIER_ENTERPRISE
    """
    try:
        client = AgentspaceClient(project_id, location, use_service_account)
        
        # Data stores are optional - engines can be created without them
        if not data_store_ids:
            print("Warning: No data stores specified. Engine will be created without data stores.", file=sys.stderr)
        
        result = client.create_search_engine(
            engine_id=engine_id,
            display_name=display_name,
            data_store_ids=list(data_store_ids),
            search_tier=search_tier
        )
        
        if format == 'json':
            click.echo(json.dumps(result, indent=2))
        else:
            if "error" in result:
                click.echo(f"Error: {result['error']}", err=True)
                sys.exit(1)
            else:
                click.echo(f"✅ Successfully created engine: {result['engine_name']}")
                click.echo(f"🔍 Search Tier: {search_tier}")
                if data_store_ids:
                    click.echo(f"📊 Data Stores: {', '.join(data_store_ids)}")
                else:
                    click.echo(f"📊 Data Stores: None")
                click.echo(f"🏢 Company: BCBSMA")
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@engines.command('delete')
@click.argument('engine_id')
@project_option
@location_option
@collection_option
@service_account_option
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
@format_option
@require_project_id
def engines_delete(engine_id, project_id, location, collection, use_service_account, force, format):
    """Delete a search engine.
    
    ENGINE_ID can be just the engine ID or the full resource name.
    
    Example:
        python scripts/agentspace.py engines delete my-engine
        python scripts/agentspace.py engines delete my-engine --force
    """
    try:
        client = AgentspaceClient(project_id, location, use_service_account)
        
        # Construct full resource name if only ID provided
        if "/" not in engine_id:
            engine_name = f"projects/{project_id}/locations/{location}/collections/{collection}/engines/{engine_id}"
        else:
            engine_name = engine_id
        
        # Get engine details for confirmation
        engine = client.get_engine_details(engine_name)
        if not engine:
            click.echo(f"Engine not found: {engine_id}", err=True)
            sys.exit(1)
        
        # Confirmation prompt unless --force is used
        if not force:
            click.echo(f"Engine: {engine.get('displayName', 'N/A')}")
            click.echo(f"Name: {engine.get('name', 'N/A')}")
            click.echo(f"Solution Type: {engine.get('solutionType', 'N/A')}")
            if not click.confirm(f"\nAre you sure you want to delete this engine?"):
                click.echo("Deletion cancelled.")
                return
        
        result = client.delete_engine(engine_name)
        
        if format == 'json':
            click.echo(json.dumps(result, indent=2))
        else:
            if result["status"] == "success":
                click.echo(f"✅ {result['message']}")
            else:
                click.echo(f"❌ {result['message']}", err=True)
                sys.exit(1)
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@data_stores.command('list')
@project_option
@location_option
@service_account_option
@format_option
@require_project_id
def data_stores_list(project_id, location, use_service_account, format):
    """List all data stores in a project.
    
    Example:
        python agentspace.py data-stores list
        python agentspace.py data-stores list --location=us
    """
    try:
        client = AgentspaceClient(project_id, location, use_service_account)
        
        if format == 'json':
            data_stores = client.list_data_stores()
            click.echo(json.dumps(data_stores, indent=2))
        else:
            click.echo(f"Listing data stores in project: {project_id}", err=True)
            click.echo(f"Location: {location}", err=True)
            if client.service_account:
                click.echo(f"Authenticated as: {client.service_account}", err=True)
            click.echo("", err=True)
            
            data_stores = client.list_data_stores()
            
            if not data_stores:
                click.echo("No data stores found.")
                return
            
            # Table format
            click.echo("=" * 100)
            click.echo(f"{'NAME':<50} {'DISPLAY NAME':<30} {'CONTENT CONFIG':<20}")
            click.echo("=" * 100)
            for ds in data_stores:
                name = ds.get('name', 'N/A').split('/')[-1]
                display_name = ds.get('displayName', 'N/A')
                content_config = ds.get('contentConfig', 'N/A')
                click.echo(f"{name:<50} {display_name:<30} {content_config:<20}")
            click.echo(f"\nTotal: {len(data_stores)} data store(s)")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@data_stores.command('describe')
@click.argument('data_store_id')
@project_option
@location_option
@collection_option
@service_account_option
@format_option
@require_project_id
def data_stores_describe(data_store_id, project_id, location, collection, use_service_account, format):
    """Describe a specific data store.
    
    DATA_STORE_ID can be just the ID or the full resource name.
    
    Example:
        python agentspace.py data-stores describe my-datastore
        python agentspace.py data-stores describe my-datastore --format=json
    """
    try:
        client = AgentspaceClient(project_id, location, use_service_account)
        
        # Construct full resource name if only ID provided
        if "/" not in data_store_id:
            ds_name = f"projects/{project_id}/locations/{location}/collections/{collection}/dataStores/{data_store_id}"
        else:
            ds_name = data_store_id
        
        ds = client.get_data_store_details(ds_name)
        if not ds:
            click.echo(f"Data store not found: {data_store_id}", err=True)
            sys.exit(1)
        
        # Try to get schema
        schema = client.get_data_store_schema(ds_name)
        if schema:
            ds['schema'] = schema
        
        if format == 'json':
            click.echo(json.dumps(ds, indent=2))
        else:
            # Human-readable format
            click.echo("=" * 80)
            click.echo(f"Data Store: {ds.get('displayName', 'N/A')}")
            click.echo("=" * 80)
            click.echo(f"Name: {ds.get('name', 'N/A')}")
            click.echo(f"Industry Vertical: {ds.get('industryVertical', 'N/A')}")
            click.echo(f"Content Config: {ds.get('contentConfig', 'N/A')}")
            click.echo(f"Created: {ds.get('createTime', 'N/A')}")
            
            if 'solutionTypes' in ds:
                click.echo(f"Solution Types: {', '.join(ds['solutionTypes'])}")
            
            if 'aclEnabled' in ds:
                click.echo(f"ACL Enabled: {ds['aclEnabled']}")
            
            if 'billingEstimation' in ds:
                be = ds['billingEstimation']
                size = int(be.get('unstructuredDataSize', 0))
                size_mb = size / (1024 * 1024)
                click.echo(f"\nBilling Estimation:")
                click.echo(f"  Size: {size_mb:.2f} MB")
                click.echo(f"  Updated: {be.get('unstructuredDataUpdateTime', 'N/A')}")
            
            if 'documentProcessingConfig' in ds:
                dpc = ds['documentProcessingConfig']
                click.echo(f"\nDocument Processing:")
                
                if 'chunkingConfig' in dpc:
                    cc = dpc['chunkingConfig']
                    if 'layoutBasedChunkingConfig' in cc:
                        chunk_size = cc['layoutBasedChunkingConfig'].get('chunkSize', 'N/A')
                        click.echo(f"  Chunk Size: {chunk_size}")
                
                if 'defaultParsingConfig' in dpc:
                    dpc_config = dpc['defaultParsingConfig']
                    if 'layoutParsingConfig' in dpc_config:
                        lpc = dpc_config['layoutParsingConfig']
                        if lpc.get('enableTableAnnotation'):
                            click.echo(f"  ✓ Table annotation enabled")
                        if lpc.get('enableImageAnnotation'):
                            click.echo(f"  ✓ Image annotation enabled")
            
            if 'schema' in ds:
                click.echo(f"\nSchema: {ds['schema'].get('name', 'N/A')}")
                
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@data_stores.command('create-from-gcs')
@click.argument('data_store_id')
@click.argument('display_name')
@click.argument('gcs_uri')
@project_option
@location_option
@service_account_option
@click.option('--data-schema', 
              type=click.Choice(['content', 'custom', 'csv', 'document']),
              default='content',
              help='Data schema type (default: content)')
@click.option('--reconciliation-mode',
              type=click.Choice(['INCREMENTAL', 'FULL']),
              default='INCREMENTAL',
              help='Import mode (default: INCREMENTAL)')
@format_option
@require_project_id
def data_stores_create_from_gcs(data_store_id, display_name, gcs_uri, project_id, location, 
                               use_service_account, data_schema, reconciliation_mode, format):
    """Create a data store and import data from GCS bucket.
    
    DATA_STORE_ID: Unique ID for the data store
    DISPLAY_NAME: Display name for the data store  
    GCS_URI: GCS URI (e.g., gs://bucket-name/path/*)
    
    Example:
        python scripts/agentspace.py data-stores create-from-gcs my-store "My Store" gs://my-bucket/docs/*
        python scripts/agentspace.py data-stores create-from-gcs my-store "My Store" gs://my-bucket/data.csv --data-schema=csv
    """
    try:
        client = AgentspaceClient(project_id, location, use_service_account)
        
        result = client.create_data_store_from_gcs(
            data_store_id=data_store_id,
            display_name=display_name,
            gcs_uri=gcs_uri,
            data_schema=data_schema,
            reconciliation_mode=reconciliation_mode
        )
        
        if format == 'json':
            click.echo(json.dumps(result, indent=2))
        else:
            if "error" in result:
                click.echo(f"Error: {result['error']}", err=True)
                sys.exit(1)
            else:
                click.echo(f"✅ Successfully created data store: {result['data_store_name']}")
                click.echo(f"📁 GCS URI: {gcs_uri}")
                click.echo(f"📊 Data Schema: {data_schema}")
                click.echo(f"🔄 Reconciliation Mode: {reconciliation_mode}")
                click.echo(f"⚙️  Import Operation: {result['import_operation'].get('name', 'N/A')}")
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@data_stores.command('list-documents')
@click.argument('data_store_id')
@project_option
@location_option
@collection_option
@service_account_option
@click.option('--branch', default='default_branch', help='Branch name (default: default_branch)')
@format_option
@require_project_id
def data_stores_list_documents(data_store_id, project_id, location, collection, use_service_account, branch, format):
    """List documents in a data store.
    
    DATA_STORE_ID can be just the ID or the full resource name.
    
    Example:
        python scripts/agentspace.py data-stores list-documents my-datastore
        python scripts/agentspace.py data-stores list-documents my-datastore --format=json
    """
    try:
        client = AgentspaceClient(project_id, location, use_service_account)
        
        # Construct full resource name if only ID provided
        if "/" not in data_store_id:
            ds_name = f"projects/{project_id}/locations/{location}/collections/{collection}/dataStores/{data_store_id}"
        else:
            ds_name = data_store_id
        
        documents = client.list_documents(ds_name, branch)
        
        if format == 'json':
            click.echo(json.dumps(documents, indent=2))
        else:
            if not documents:
                click.echo("No documents found in this data store.")
                return
            
            click.echo("=" * 100)
            click.echo(f"Documents in Data Store: {data_store_id}")
            click.echo(f"Branch: {branch}")
            click.echo("=" * 100)
            click.echo(f"{'ID':<40} {'URI':<50} {'Index Time':<25}")
            click.echo("-" * 100)
            
            for doc in documents:
                doc_id = doc.get('id', 'N/A')[:40]
                uri = doc.get('content', {}).get('uri', 'N/A')
                if len(uri) > 50:
                    uri = uri[:47] + "..."
                index_time = doc.get('indexTime', 'N/A')
                if index_time != 'N/A':
                    # Format the timestamp for better readability
                    from datetime import datetime
                    try:
                        dt = datetime.fromisoformat(index_time.replace('Z', '+00:00'))
                        index_time = dt.strftime('%m/%d/%Y, %I:%M:%S %p')
                    except:
                        pass
                
                click.echo(f"{doc_id:<40} {uri:<50} {index_time:<25}")
            
            click.echo(f"\nTotal: {len(documents)} document(s)")
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@data_stores.command('delete')
@click.argument('data_store_id')
@project_option
@location_option
@collection_option
@service_account_option
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
@format_option
@require_project_id
def data_stores_delete(data_store_id, project_id, location, collection, use_service_account, force, format):
    """Delete a data store.
    
    DATA_STORE_ID can be just the ID or the full resource name.
    
    Example:
        python scripts/agentspace.py data-stores delete my-datastore
        python scripts/agentspace.py data-stores delete my-datastore --force
    """
    try:
        client = AgentspaceClient(project_id, location, use_service_account)
        
        # Construct full resource name if only ID provided
        if "/" not in data_store_id:
            ds_name = f"projects/{project_id}/locations/{location}/collections/{collection}/dataStores/{data_store_id}"
        else:
            ds_name = data_store_id
        
        # Get data store details for confirmation
        ds = client.get_data_store_details(ds_name)
        if not ds:
            click.echo(f"Data store not found: {data_store_id}", err=True)
            sys.exit(1)
        
        # Confirmation prompt unless --force is used
        if not force:
            click.echo(f"Data Store: {ds.get('displayName', 'N/A')}")
            click.echo(f"Name: {ds.get('name', 'N/A')}")
            click.echo(f"Content Config: {ds.get('contentConfig', 'N/A')}")
            click.echo(f"Created: {ds.get('createTime', 'N/A')}")
            if not click.confirm(f"\nAre you sure you want to delete this data store?"):
                click.echo("Deletion cancelled.")
                return
        
        result = client.delete_data_store(ds_name)
        
        if format == 'json':
            click.echo(json.dumps(result, indent=2))
        else:
            if result["status"] == "success":
                click.echo(f"✅ {result['message']}")
            else:
                click.echo(f"❌ {result['message']}", err=True)
                sys.exit(1)
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()

