# MDVM Function App Deployment Guide

## Deploy to Azure

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fnickselvaggio%2FMDVM-FuncApp%2Fmain%2Fazuredeploy.json)

## Prerequisites

- Azure Subscription
- Resource Group (will be created or selected during deployment)

## Required Parameters

- **functionAppName**: Name for your Azure Function App (must be globally unique)

## Optional Parameters

All other parameters have sensible defaults:
- **location**: Defaults to resource group location
- **storageAccountName**: Auto-generated with unique suffix
- **pythonVersion**: Defaults to 3.11
- **maximumInstanceCount**: Defaults to 100
- **instanceMemoryMB**: Defaults to 2048 MB

## Post-Deployment Configuration

### Required: Storage Account Role Assignment

After deployment, the managed identity needs access to the storage account. Run these Azure CLI commands:

```bash
# Set variables
RESOURCE_GROUP="<your-resource-group>"
FUNCTION_APP_NAME="<your-function-app-name>"
STORAGE_ACCOUNT_NAME="<your-storage-account-name>"

# Get the managed identity principal ID
IDENTITY_PRINCIPAL_ID=$(az functionapp identity show \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query principalId -o tsv)

# Get the user-assigned managed identity principal ID
USER_IDENTITY_NAME=$(az identity list \
  --resource-group $RESOURCE_GROUP \
  --query "[?contains(name, '$FUNCTION_APP_NAME')].name" -o tsv)

USER_IDENTITY_PRINCIPAL_ID=$(az identity show \
  --name $USER_IDENTITY_NAME \
  --resource-group $RESOURCE_GROUP \
  --query principalId -o tsv)

# Assign Storage Blob Data Contributor role to user-assigned identity
az role assignment create \
  --assignee $USER_IDENTITY_PRINCIPAL_ID \
  --role "Storage Blob Data Contributor" \
  --scope "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Storage/storageAccounts/$STORAGE_ACCOUNT_NAME"

# Assign Storage Blob Data Contributor role to system-assigned identity
az role assignment create \
  --assignee $IDENTITY_PRINCIPAL_ID \
  --role "Storage Blob Data Contributor" \
  --scope "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Storage/storageAccounts/$STORAGE_ACCOUNT_NAME"
```

### Alternative: Using Azure Portal

1. Navigate to the Storage Account
2. Select **Access Control (IAM)**
3. Click **+ Add** → **Add role assignment**
4. Select role: **Storage Blob Data Contributor**
5. Assign access to: **Managed Identity**
6. Select members: Choose both the system-assigned and user-assigned identities for your Function App
7. Click **Review + assign**

## Troubleshooting

### Deployment fails with "storage account name not available"
The storage account name must be globally unique. Either:
- Let the template auto-generate a name (default behavior)
- Specify a unique name in parameters

## Additional Resources

- [Azure Functions Documentation](https://docs.microsoft.com/azure/azure-functions/)
- [Flex Consumption Plan](https://docs.microsoft.com/azure/azure-functions/flex-consumption-plan)
- [Python Developer Guide](https://docs.microsoft.com/azure/azure-functions/functions-reference-python)
