# MDVM Function App - Microsoft Defender Vulnerability Management API

A Python-based Azure Function App that retrieves software vulnerability data from Microsoft Defender for Endpoint (MDVM) API and provides it through a REST endpoint with optional data reorganization capabilities.

## Overview

This Azure Function App serves as a secure middleware layer between client applications and the Microsoft Defender Vulnerability Management API. It provides:

- **Secure API Access**: Uses Azure AD (Entra ID) authentication with client credentials flow
- **Data Optimization**: Fetches vulnerability data with configurable pagination and caching
- **Flexible Output**: Option to reorganize data into hierarchical structures for easier consumption
- **Performance Monitoring**: Built-in logging and performance metrics
- **Error Handling**: Comprehensive error handling with detailed error messages

## Features

### 🔐 Authentication & Security
- Azure AD (Entra ID) client credentials authentication
- Token caching with automatic refresh
- Secure environment variable configuration
- HTTP connection pooling with retry strategies

### 📊 Data Processing
- Fetches software vulnerabilities from Microsoft Defender for Endpoint
- Configurable page size and maximum pages limits
- Optional hierarchical data reorganization (OS Platform → Device Name → CVE ID)
- Performance metrics and detailed logging

### 🚀 Performance Optimizations
- HTTP session reuse with connection pooling
- Token caching to reduce authentication overhead
- Configurable retry strategies for API calls
- Async-friendly design patterns

## API Endpoints

### GET `/api/getMDVMData`

Retrieves software vulnerability data from Microsoft Defender Vulnerability Management.

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pageSize` | integer | 10 | Number of records per page (1-200000) |
| `maxPages` | integer | 5 | Maximum pages to fetch (0 = unlimited) |
| `reorganize` | boolean | true | Reorganize data into hierarchical structure |

#### Example Requests

```bash
# Basic request with default parameters
GET /api/getMDVMData

# Custom page size and max pages
GET /api/getMDVMData?pageSize=50&maxPages=10

# Disable data reorganization
GET /api/getMDVMData?pageSize=100&reorganize=false
```

#### Response Format

**With Reorganization (default):**
```json
{
  "data": {
    "Windows 10": {
      "DESKTOP-ABC123": {
        "CVE-2023-1234": {
          "cveId": "CVE-2023-1234",
          "deviceName": "DESKTOP-ABC123",
          "osPlatform": "Windows 10",
          "softwareName": "Microsoft Office",
          "softwareVersion": "16.0.14326.20508",
          "severity": "High"
        }
      }
    }
  },
  "metadata": {
    "total_vulnerabilities": 1500,
    "pages_fetched": 5,
    "has_more_data": true,
    "fetch_duration_seconds": 12.45,
    "reorganized": true,
    "structure": "osPlatform -> deviceName -> cveId"
  }
}
```

**Without Reorganization:**
```json
{
  "vulnerabilities": [
    {
      "cveId": "CVE-2023-1234",
      "deviceName": "DESKTOP-ABC123",
      "osPlatform": "Windows 10",
      "softwareName": "Microsoft Office",
      "softwareVersion": "16.0.14326.20508",
      "severity": "High"
    }
  ],
  "total_count": 1500,
  "pages_fetched": 5,
  "has_more_data": true,
  "fetch_duration_seconds": 12.45
}
```

## Configuration

### Environment Variables

Configure these environment variables in your Azure Function App settings or `local.settings.json`:

| Variable | Required | Description |
|----------|----------|-------------|
| `AAD_TENANT_ID` | Yes | Azure AD tenant ID |
| `AAD_CLIENT_ID` | Yes | Azure AD application (client) ID |
| `AAD_CLIENT_SECRET` | Yes | Azure AD client secret |
| `AAD_RESOURCE_APP_ID_URI` | No | Resource URI (default: `https://api.securitycenter.microsoft.com`) |
| `AzureWebJobsStorage` | Yes | Azure Storage connection string |
| `FUNCTIONS_WORKER_RUNTIME` | Yes | Set to `python` |

### Application Configuration

The following constants can be modified in `function_app.py`:

```python
DEFAULT_PAGE_SIZE = 10        # Default records per page
DEFAULT_MAX_PAGES = 5         # Default maximum pages to fetch
MAX_PAGE_SIZE = 200000        # Maximum allowed page size
MAX_PAGES_LIMIT = 0           # Maximum pages limit (0 = unlimited)
```

## Prerequisites

### Azure AD App Registration

1. **Register Application**: Create an Azure AD app registration
2. **Configure API Permissions**: Add the following permissions:
   - `WindowsDefenderATP` → `Vulnerability.Read.All` (Application permission)
3. **Create Client Secret**: Generate a client secret for authentication
4. **Grant Admin Consent**: Admin consent required for application permissions

### Microsoft Defender for Endpoint

- Active Microsoft Defender for Endpoint subscription
- Appropriate licensing for vulnerability management features
- Devices onboarded to Microsoft Defender

## Deployment

### Deploy to Azure

1. **Create Function App**:
   ```bash
   az functionapp create \
     --resource-group myResourceGroup \
     --consumption-plan-location westus2 \
     --runtime python \
     --runtime-version 3.9 \
     --functions-version 4 \
     --name mdvm-funcapp \
     --storage-account mystorageaccount
   ```

2. **Configure Application Settings**:
   ```bash
   az functionapp config appsettings set \
     --name mdvm-funcapp \
     --resource-group myResourceGroup \
     --settings \
     AAD_TENANT_ID="your-tenant-id" \
     AAD_CLIENT_ID="your-client-id" \
     AAD_CLIENT_SECRET="your-client-secret"
   ```

3. **Deploy Code**:
   ```bash
   func azure functionapp publish mdvm-funcapp
   ```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues related to:
- **Azure Functions**: [Azure Functions Documentation](https://docs.microsoft.com/azure/azure-functions/)
- **Microsoft Defender API**: [Microsoft Defender for Endpoint API Documentation](https://docs.microsoft.com/microsoft-365/security/defender-endpoint/apis-intro)
- **This Implementation**: Create an issue in this repository