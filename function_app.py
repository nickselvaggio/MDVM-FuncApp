import azure.functions as func
import json
import logging
import os
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from functools import lru_cache
from threading import Lock
from typing import Dict, Optional, Tuple

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Centralized configuration constants
DEFAULT_PAGE_SIZE = 10
DEFAULT_MAX_PAGES = 5
MAX_PAGE_SIZE = 200000  # Maximum page size allowed
MAX_PAGES_LIMIT = 0     # Maximum number of pages allowed (0 = unlimited)

# Global session with connection pooling and retry strategy
def _get_http_session() -> requests.Session:
    """Create a requests session with connection pooling and retry strategy."""
    session = requests.Session()
    
    # Configure retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=10,
        pool_maxsize=20
    )
    
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

# Global session instance
_http_session = _get_http_session()

# Token caching
_token_cache = {}
_token_lock = Lock()


def _fetch_aad_token(tenant_id: str, client_id: str, client_secret: str, resource_app_id_uri: str) -> str:
    """Acquire an Entra ID token using client credentials"""
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/token"
    
    data = {
        "resource": resource_app_id_uri,
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "MDVM-FuncApp/1.0"
    }

    try:
        response = _http_session.post(
            token_url, 
            data=data, 
            headers=headers, 
            timeout=10
        )
        response.raise_for_status()
        payload = response.json()
        
        return payload["access_token"]
        
    except requests.exceptions.HTTPError as exc:
        logging.error("Token request failed with status %s: %s", exc.response.status_code, exc.response.text)
        raise RuntimeError("Failed to retrieve Entra ID token due to HTTP error.") from exc
    except requests.exceptions.RequestException as exc:
        logging.error("Token request failed due to connection error: %s", exc)
        raise RuntimeError("Failed to retrieve Entra ID token due to connection error.") from exc
    except (KeyError, json.JSONDecodeError) as exc:
        logging.error("Token response parsing failed: %s", exc)
        raise RuntimeError("Failed to parse Entra ID token response.") from exc


def _get_cached_token(tenant_id: str, client_id: str, client_secret: str, resource_app_id_uri: str) -> str:
    """Get cached token or fetch new one if expired."""
    cache_key = f"{tenant_id}:{client_id}:{resource_app_id_uri}"
    
    with _token_lock:
        cached_entry = _token_cache.get(cache_key)
        if cached_entry and cached_entry['expires_at'] > time.time() + 300:  # 5 min buffer
            logging.info("Using cached token")
            return cached_entry['token']
    
    # Fetch new token
    token = _fetch_aad_token(tenant_id, client_id, client_secret, resource_app_id_uri)
    
    with _token_lock:
        _token_cache[cache_key] = {
            'token': token,
            'expires_at': time.time() + 3600  # Assume 1 hour expiry
        }
    
    return token


def _reorganize_vulnerabilities_by_hierarchy(vulnerabilities: list) -> dict:
    """
    Reorganize vulnerabilities data into hierarchical structure:
    osPlatform -> deviceName -> cveId (with all vulnerability data)
    """
    reorganized = {}
    
    for vuln in vulnerabilities:
        # Use correct field names from the actual API response
        os_platform = vuln.get("osPlatform", "Unknown")
        device_name = vuln.get("deviceName", "Unknown")
        cve_id = vuln.get("cveId")
        
        # Handle cases where cveId might be null or empty
        if not cve_id:
            # Use a combination of software info to create a unique identifier
            software_name = vuln.get("softwareName", "Unknown")
            software_version = vuln.get("softwareVersion", "Unknown")
            cve_id = f"{software_name}_{software_version}"
        
        # Use setdefault for cleaner nested dictionary creation
        reorganized.setdefault(os_platform, {}).setdefault(device_name, {})[cve_id] = vuln
    
    return reorganized


def _fetch_mdvm_vulnerabilities(access_token: str, page_size: int = DEFAULT_PAGE_SIZE, max_pages: int = DEFAULT_MAX_PAGES) -> dict:
    """Fetch software vulnerabilities"""
    base_url = "https://api.securitycenter.microsoft.com/api/machines/SoftwareVulnerabilitiesByMachine"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "MDVM-FuncApp/1.0"
    }
    
    all_vulnerabilities = []
    current_url = f"{base_url}?pageSize={page_size}"
    pages_fetched = 0
    
    # Track performance metrics
    start_time = time.time()
    
    while current_url and (max_pages == 0 or pages_fetched < max_pages):
        page_start = time.time()
        
        try:
            logging.info(f"Fetching page {pages_fetched + 1} from MDVM API")
            
            response = _http_session.get(
                current_url, 
                headers=headers, 
                timeout=30
            )
            response.raise_for_status()
            
            response_data = response.json()
            page_duration = time.time() - page_start
            
            # Extract vulnerabilities from the current page
            vulnerabilities = response_data.get("value", [])
            all_vulnerabilities.extend(vulnerabilities)
            
            logging.info(f"Page {pages_fetched + 1}: {len(vulnerabilities)} vulnerabilities fetched in {page_duration:.2f}s")
            
            # Check for next page
            current_url = response_data.get("@odata.nextLink")
            pages_fetched += 1
            
        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code
            error_msg = f"API request failed with status {status_code}"
            
            # Enhanced error handling based on status codes
            if status_code == 401:
                logging.error("Authentication failed - token may be expired")
                raise RuntimeError("Authentication failed. Token may be invalid or expired.") from exc
            elif status_code == 403:
                logging.error("Access denied - check API permissions")
                raise RuntimeError("Access denied. Check API permissions.") from exc
            elif status_code == 429:
                retry_after = exc.response.headers.get('Retry-After', '60')
                logging.error(f"Rate limit exceeded - retry after {retry_after} seconds")
                raise RuntimeError(f"Rate limit exceeded. Please retry after {retry_after} seconds.") from exc
            elif 500 <= status_code < 600:
                logging.error(f"Server error {status_code} - temporary issue")
                raise RuntimeError(f"MDVM API server error: {error_msg}") from exc
            else:
                logging.error(f"Unexpected HTTP error: {error_msg}")
                raise RuntimeError(f"API request failed: {error_msg}") from exc
                
        except requests.exceptions.RequestException as exc:
            logging.error("API request failed due to connection error: %s", exc)
            raise RuntimeError("Failed to connect to MDVM API.") from exc
    
    total_duration = time.time() - start_time
    logging.info(f"Total API fetch completed: {len(all_vulnerabilities)} vulnerabilities in {total_duration:.2f}s")
    
    if max_pages > 0 and pages_fetched >= max_pages and current_url:
        logging.warning(f"Reached maximum page limit ({max_pages}). More data may be available.")
    
    return {
        "vulnerabilities": all_vulnerabilities,
        "total_count": len(all_vulnerabilities),
        "pages_fetched": pages_fetched,
        "has_more_data": bool(current_url),
        "fetch_duration_seconds": total_duration
    }


@app.route(route="getMDVMData")
def getMDVMData(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing MDVM vulnerabilities request')
    
    # Input validation with defaults and bounds checking
    try:
        page_size = min(max(int(req.params.get('pageSize', str(DEFAULT_PAGE_SIZE))), 1), MAX_PAGE_SIZE)
        max_pages_input = max(int(req.params.get('maxPages', str(DEFAULT_MAX_PAGES))), 0)
        max_pages = min(max_pages_input, MAX_PAGES_LIMIT) if MAX_PAGES_LIMIT > 0 else max_pages_input
        reorganize = req.params.get('reorganize', 'true').lower() in ['true', '1', 'yes', 'on']
    except ValueError as exc:
        logging.warning(f"Invalid parameter values in request: {exc}")
        return func.HttpResponse(
            json.dumps({"error": "pageSize and maxPages must be valid integers"}),
            status_code=400,
            mimetype="application/json"
        )

    # Environment configuration with validation
    required_env_vars = ["AAD_TENANT_ID", "AAD_CLIENT_ID", "AAD_CLIENT_SECRET"]
    env_config = {}
    
    for var in required_env_vars:
        value = os.environ.get(var)
        if not value:
            logging.error(f"Missing required environment variable: {var}")
            return func.HttpResponse(
                json.dumps({"error": f"Server misconfiguration: {var} is missing"}),
                status_code=500,
                mimetype="application/json"
            )
        env_config[var] = value
    
    resource_app_id_uri = os.environ.get("AAD_RESOURCE_APP_ID_URI", "https://api.securitycenter.microsoft.com")

    try:
        # Use cached token
        access_token = _get_cached_token(
            env_config["AAD_TENANT_ID"],
            env_config["AAD_CLIENT_ID"], 
            env_config["AAD_CLIENT_SECRET"],
            resource_app_id_uri
        )
        
        # Fetch vulnerabilities
        vulnerabilities_data = _fetch_mdvm_vulnerabilities(access_token, page_size, max_pages)
        
        logging.info(f"Successfully fetched {vulnerabilities_data['total_count']} vulnerabilities across {vulnerabilities_data['pages_fetched']} pages")
        
        # Process response
        if reorganize and vulnerabilities_data['vulnerabilities']:
            logging.info("Reorganizing vulnerability data by OSPlatform -> DeviceName -> CveId hierarchy")
            reorganized_data = _reorganize_vulnerabilities_by_hierarchy(vulnerabilities_data['vulnerabilities'])
            
            # Create response with reorganized data and metadata
            response_data = {
                "data": reorganized_data,
                "metadata": {
                    "total_vulnerabilities": vulnerabilities_data['total_count'],
                    "pages_fetched": vulnerabilities_data['pages_fetched'],
                    "has_more_data": vulnerabilities_data['has_more_data'],
                    "fetch_duration_seconds": vulnerabilities_data['fetch_duration_seconds'],
                    "reorganized": True,
                    "structure": "osPlatform -> deviceName -> cveId"
                }
            }
            
            # Display reorganized data structure summary
            platform_count = len(reorganized_data)
            device_count = sum(len(devices) for devices in reorganized_data.values())
            cve_count = sum(len(cves) for devices in reorganized_data.values() for cves in devices.values())
            
            logging.info(f"Reorganized data structure: {platform_count} OS Platforms, {device_count} unique devices, {cve_count} CVE entries")
            
        else:
            response_data = vulnerabilities_data
        
        return func.HttpResponse(
            json.dumps(response_data, indent=2, default=str),
            status_code=200,
            mimetype="application/json"
        )
        
    except RuntimeError as exc:
        logging.error("MDVM data fetch failed: %s", exc)
        return func.HttpResponse(
            json.dumps({
                "error": str(exc),
                "timestamp": time.time()
            }),
            status_code=502,
            mimetype="application/json"
        )
    except Exception as exc:
        logging.exception("Unexpected error in getMDVMData")
        return func.HttpResponse(
            json.dumps({
                "error": "Internal server error",
                "timestamp": time.time()
            }),
            status_code=500,
            mimetype="application/json"
        )