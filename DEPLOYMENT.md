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

The deployment is now fully automated. The managed identity is automatically granted **Storage Blob Data Contributor** access to the storage account during deployment.

No manual configuration steps are required after deployment completes.

## Troubleshooting

### Deployment fails with "storage account name not available"
The storage account name must be globally unique. Either:
- Let the template auto-generate a name (default behavior)
- Specify a unique name in parameters

## Additional Resources

- [Azure Functions Documentation](https://docs.microsoft.com/azure/azure-functions/)
- [Flex Consumption Plan](https://docs.microsoft.com/azure/azure-functions/flex-consumption-plan)
- [Python Developer Guide](https://docs.microsoft.com/azure/azure-functions/functions-reference-python)
