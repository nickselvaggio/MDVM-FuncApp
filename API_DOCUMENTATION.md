# API Documentation

## Endpoint Reference

### GET /api/getMDVMData

Retrieves software vulnerability data from Microsoft Defender Vulnerability Management API.

#### Request

**URL**: `/api/getMDVMData`  
**Method**: `GET`  
**Authentication**: None (function handles internal authentication to Microsoft Defender API)

#### Query Parameters

| Parameter | Type | Required | Default | Min | Max | Description |
|-----------|------|----------|---------|-----|-----|-------------|
| `pageSize` | integer | No | 10 | 1 | 200,000 | Number of vulnerability records to retrieve per API page |
| `maxPages` | integer | No | 5 | 0 | unlimited | Maximum number of pages to fetch (0 = no limit) |
| `reorganize` | boolean | No | true | - | - | Whether to reorganize data into hierarchical structure |

#### Response

##### Success Response (200 OK)

**With Reorganization (reorganize=true)**

```json
{
  "data": {
    "osPlatform1": {
      "deviceName1": {
        "cveId1": {
          "cveId": "CVE-2023-12345",
          "deviceName": "DESKTOP-ABC123",
          "osPlatform": "Windows 10",
          "softwareName": "Microsoft Office",
          "softwareVersion": "16.0.14326.20508",
          "severity": "High",
          "publishedDate": "2023-01-15T00:00:00Z",
          "lastSeenDate": "2023-12-01T10:30:00Z"
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

**Without Reorganization (reorganize=false)**

```json
{
  "vulnerabilities": [
    {
      "cveId": "CVE-2023-12345",
      "deviceName": "DESKTOP-ABC123",
      "osPlatform": "Windows 10",
      "softwareName": "Microsoft Office",
      "softwareVersion": "16.0.14326.20508",
      "severity": "High",
      "publishedDate": "2023-01-15T00:00:00Z",
      "lastSeenDate": "2023-12-01T10:30:00Z"
    }
  ],
  "total_count": 1500,
  "pages_fetched": 5,
  "has_more_data": true,
  "fetch_duration_seconds": 12.45
}
```

##### Error Responses

**400 Bad Request** - Invalid Parameters
```json
{
  "error": "pageSize and maxPages must be valid integers"
}
```

**500 Internal Server Error** - Configuration Error
```json
{
  "error": "Server misconfiguration: AAD_TENANT_ID is missing"
}
```

**502 Bad Gateway** - External API Error
```json
{
  "error": "Authentication failed. Token may be invalid or expired.",
  "timestamp": 1698765432.123
}
```

#### Response Fields

##### Vulnerability Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `cveId` | string | Common Vulnerabilities and Exposures identifier |
| `deviceName` | string | Name of the affected device |
| `osPlatform` | string | Operating system platform |
| `softwareName` | string | Name of the vulnerable software |
| `softwareVersion` | string | Version of the vulnerable software |
| `severity` | string | Vulnerability severity (Critical, High, Medium, Low) |
| `publishedDate` | string (ISO 8601) | Date when vulnerability was published |
| `lastSeenDate` | string (ISO 8601) | Date when vulnerability was last detected |

##### Metadata Fields

| Field | Type | Description |
|-------|------|-------------|
| `total_vulnerabilities` | integer | Total number of vulnerability records returned |
| `pages_fetched` | integer | Number of API pages processed |
| `has_more_data` | boolean | Indicates if more data is available beyond the fetched pages |
| `fetch_duration_seconds` | float | Total time taken to fetch data from Microsoft API |
| `reorganized` | boolean | Indicates if data has been reorganized into hierarchical structure |
| `structure` | string | Description of the hierarchical structure (when reorganized=true) |

## Usage Examples

### Basic Request
```bash
curl "https://your-function-app.azurewebsites.net/api/getMDVMData"
```

### Custom Page Size
```bash
curl "https://your-function-app.azurewebsites.net/api/getMDVMData?pageSize=100"
```

### Fetch Multiple Pages
```bash
curl "https://your-function-app.azurewebsites.net/api/getMDVMData?maxPages=10&pageSize=50"
```

### Raw Data (No Reorganization)
```bash
curl "https://your-function-app.azurewebsites.net/api/getMDVMData?reorganize=false"
```

### Complete Data Dump (No Page Limit)
```bash
curl "https://your-function-app.azurewebsites.net/api/getMDVMData?maxPages=0&pageSize=1000"
```

## Rate Limits and Performance

### Microsoft Defender API Limits
- **Rate Limit**: Varies by subscription and tenant
- **Typical Limits**: 100-1000 requests per minute
- **Page Size Limit**: Up to 200,000 records per page

### Function App Considerations
- **Timeout**: Maximum 10 minutes for consumption plan
- **Memory**: Scales based on demand
- **Cold Start**: ~2-5 seconds for Python runtime

### Performance Recommendations

1. **Optimize Page Size**: Balance between fewer API calls (larger pages) and faster response times (smaller pages)
2. **Use Caching**: Token caching reduces authentication overhead
3. **Monitor Usage**: Track `fetch_duration_seconds` to identify performance issues
4. **Implement Client Caching**: Cache responses on client side when appropriate

## Error Handling Details

### HTTP Status Codes

| Code | Scenario | Retry Recommended |
|------|----------|-------------------|
| 400 | Invalid parameters | No - Fix parameters |
| 401 | Authentication failed | No - Check credentials |
| 403 | Insufficient permissions | No - Check API permissions |
| 429 | Rate limit exceeded | Yes - Use Retry-After header |
| 500 | Function configuration error | No - Check environment variables |
| 502 | Microsoft API error | Yes - Temporary issue |
| 503 | Service unavailable | Yes - Exponential backoff |

### Client-Side Error Handling

```javascript
async function fetchVulnerabilities(pageSize = 10, maxPages = 5) {
  try {
    const response = await fetch(
      `/api/getMDVMData?pageSize=${pageSize}&maxPages=${maxPages}`
    );
    
    if (!response.ok) {
      const errorData = await response.json();
      
      if (response.status === 429) {
        // Rate limit - implement retry logic
        const retryAfter = response.headers.get('Retry-After') || 60;
        console.log(`Rate limited. Retry after ${retryAfter} seconds`);
        return null;
      }
      
      throw new Error(`API Error: ${errorData.error}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch vulnerabilities:', error);
    throw error;
  }
}
```

## Data Structure Examples

### Hierarchical Structure (reorganize=true)

The reorganized structure groups vulnerabilities by:
1. **OS Platform** (Windows 10, Windows 11, Linux, etc.)
2. **Device Name** (Individual machine names)
3. **CVE ID** (Specific vulnerability identifiers)

This structure is optimal for:
- Dashboard visualizations
- Platform-specific analysis
- Device-centric reporting
- Hierarchical filtering

### Flat Structure (reorganize=false)

The flat structure maintains the original API response format, which is optimal for:
- Data processing pipelines
- CSV exports
- Database insertions
- Stream processing