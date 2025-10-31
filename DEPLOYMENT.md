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
- **maximumInstanceCount**: Defaults to 40
- **instanceMemoryMB**: Defaults to 2048 MB

## Post-Deployment: Deploy Your Code

After the infrastructure is created, deploy your function code using one of these methods:

### Option 1: Azure CLI

```bash
# Download the latest release zip from GitHub
# Replace <version> with the desired release tag (e.g., v1.0.0)
curl -L -o deploy.zip https://github.com/nickselvaggio/MDVM-FuncApp/releases/latest/download/mdvm-funcapp-v1.0.0.zip

# Deploy the zip to Azure Function App
az functionapp deployment source config-zip \
  --resource-group <your-resource-group> \
  --name <your-function-app-name> \
  --src deploy.zip
```

### Option 2: VS Code

1. Install the [Azure Functions extension](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azurefunctions)
2. Clone this repository and open in VS Code
3. Click the Azure icon in the sidebar
4. Right-click on your Function App
5. Select "Deploy to Function App..."

## Troubleshooting

### Deployment fails with "storage account name not available"
The storage account name must be globally unique. Either:
- Let the template auto-generate a name (default behavior)
- Specify a unique name in parameters

## Additional Resources

- [Azure Functions Documentation](https://docs.microsoft.com/azure/azure-functions/)
- [Flex Consumption Plan](https://docs.microsoft.com/azure/azure-functions/flex-consumption-plan)
- [Python Developer Guide](https://docs.microsoft.com/azure/azure-functions/functions-reference-python)
