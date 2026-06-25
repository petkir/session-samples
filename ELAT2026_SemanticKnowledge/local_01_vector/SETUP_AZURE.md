# Azure App Registration Setup

This guide walks you through settin2. **Set Application ID URI**
   - Click **"+ Set"** next to Application ID URI
   - Accept the default (`api://{client-id}`) or customize it:

     ```text
     api://elat-local-llm-chat
     ```

   - Click **"Save"** Azure App Registration for the elat Local LLM Chat Application with proper authentication and API scopes.

## Prerequisites

- Azure subscription with admin rights
- Access to Azure Active Directory (Entra ID)
- Owner permissions on your Azure AD tenant (recommended)

## Step 1: Create App Registration

1. **Navigate to Azure Portal**
   - Go to [Azure Portal](https://portal.azure.com)
   - Search for "App registrations" or navigate to **Azure Active Directory > App registrations**

2. **Create New Registration**
   - Click **"+ New registration"**
   - Fill in the following details:
     - **Name**: `elat-Local-LLM-Chat`
     - **Supported account types**:
       - Select **"Accounts in this organizational directory only"** (Single tenant)
     - **Redirect URI**: Leave blank for now (we'll configure this later)
   - Click **"Register"**

3. **Note Important Values**
   After registration, copy these values for your configuration:
   - **Application (client) ID**
   - **Directory (tenant) ID**
   - **Object ID**

## Step 2: Configure Single Page Application (SPA)

1. **Navigate to Authentication**
   - In your app registration, go to **"Authentication"** in the left menu

2. **Add Platform**
   - Click **"+ Add a platform"**
   - Select **"Single-page application"**

3. **Configure Redirect URIs**
   Add the following redirect URIs for development and production:

   ```text
  
   http://localhost:5173/
   https://localhost:54375/
   http://localhost:3000/
   ```

   > **Note**: Add your production URL when deploying (e.g., `https://your-app.azurewebsites.net`)

4. **Configure Advanced Settings**
   - **Logout URL**: `http://localhost:5173` (add production URL when deploying)
   - **Implicit grant and hybrid flows**:
     - ✅ **Access tokens** (checked)
     - ✅ **ID tokens** (checked)

5. **Click "Configure"** to save

## Step 3: Expose API and Define Scopes

1. **Navigate to Expose an API**
   - In your app registration, go to **"Expose an API"** in the left menu

2. **Set Application ID URI**
   - Click **"+ Set"** next to Application ID URI
   - Accept the default (`api://{client-id}`) or customize it:
     ```
     api://elat-local-llm-chat
     ```
   - Click **"Save"**

3. **Add Custom Scopes**
   Click **"+ Add a scope"** and create the following scopes:

   **Scope 1: Chat Access**
   - **Scope name**: `Chat.ReadWrite`
   - **Admin consent display name**: `Access chat sessions and messages`
   - **Admin consent description**: `Allows the application to read and write chat sessions and messages on behalf of the user`
   - **User consent display name**: `Access your chat data`
   - **User consent description**: `Allows the app to access your chat sessions and messages`
   - **State**: `Enabled`

   **Scope 2: File Upload**
   - **Scope name**: `Files.Upload`
   - **Admin consent display name**: `Upload files to chat`
   - **Admin consent description**: `Allows the application to upload and manage files in chat sessions`
   - **User consent display name**: `Upload files`
   - **User consent description**: `Allows the app to upload files to your chat sessions`
   - **State**: `Enabled`

4. **Add Authorized Client Applications** (Optional)
   If you want to pre-authorize your own app:
   - Click **"+ Add a client application"**
   - **Client ID**: Use the same Application (client) ID from Step 1
   - **Authorized scopes**: Select both scopes you created
   - Click **"Add application"**

## Step 4: API Permissions

1. **Navigate to API Permissions**
   - In your app registration, go to **"API permissions"** in the left menu

2. **Add Microsoft Graph Permissions**
   - Click **"+ Add a permission"**
   - Select **"Microsoft Graph"**
   - Choose **"Delegated permissions"**
   - Add the following permissions:
     - `User.Read` (usually already present)
     - `openid`
     - `profile`
     - `email`

3. **Add Your Custom API Permissions**
   - Click **"+ Add a permission"**
   - Select **"My APIs"**
   - Choose your app registration (`elat-Local-LLM-Chat`)
   - Select **"Delegated permissions"**
   - Check both scopes:
     - `access_as_user`
   - Click **"Add permissions"**

4. **Grant Admin Consent**
   - Click **"✓ Grant admin consent for [Your Organization]"**
   - Confirm by clicking **"Yes"**

## Step 5: Add Yourself as Owner

1. **Navigate to Owners**
   - In your app registration, go to **"Owners"** in the left menu

2. **Add Owner**
   - Click **"+ Add owners"**
   - Search for and select your user account
   - Click **"Add"**

## Step 6: Configure Token Settings (Optional)

1. **Navigate to Token Configuration**
   - In your app registration, go to **"Token configuration"** in the left menu

2. **Add Optional Claims**
   - Click **"+ Add optional claim"**
   - **Token type**: `ID`
   - Select useful claims like:
     - `email`
     - `given_name`
     - `family_name`
     - `preferred_username`
   - Click **"Add"**

## Step 7: Configure Your Application

### Backend Configuration (`appsettings.Development.json`)

```json
{
  "AzureAd": {
    "Instance": "https://login.microsoftonline.com/",
    "Domain": "YOUR_DOMAIN.onmicrosoft.com",
    "TenantId": "YOUR_TENANT_ID",
    "ClientId": "YOUR_CLIENT_ID"
  }
}
```

### Frontend Configuration (`src/.env`)

```typescript
VITE_AZURE_CLIENT_ID=your-client-id-here
VITE_AZURE_TENANT_ID=your-tenant-id-here
VITE_AZURE_DOMAIN=your-domain.onmicrosoft.com

```

## Step 8: Testing the Configuration

1. **Start your application**
   ```bash
   ./setup.sh
   ```

2. **Test Authentication**
   - Navigate to `http://localhost:5173`
   - Click the login button
   - You should be redirected to Microsoft login
   - After successful login, you should be redirected back to your app

3. **Verify Token Claims**
   - Check that your tokens contain the expected scopes
   - Use browser developer tools to inspect the access token

## Troubleshooting

### Common Issues

#### CORS Errors

- Ensure all redirect URIs are properly configured
- Check that you're using the exact URLs (including trailing slashes)

#### Scope Not Found

- Verify the Application ID URI is correct
- Ensure scopes are properly exposed in "Expose an API"

#### Authentication Fails

- Check that tenant ID and client ID are correct
- Verify the authority URL format

#### Permission Denied

- Ensure admin consent has been granted
- Check that required permissions are added

### Useful Azure CLI Commands

```bash
# List app registrations
az ad app list --display-name "elat-Local-LLM-Chat"

# Get app registration details
az ad app show --id YOUR_CLIENT_ID

# Update redirect URIs
az ad app update --id YOUR_CLIENT_ID --web-redirect-uris "http://localhost:5173" "https://localhost:5173"
```

## Security Best Practices

1. **Use least privilege**: Only request necessary scopes
2. **Secure storage**: Never commit client secrets to source control
3. **Regular rotation**: Rotate client secrets regularly (if using any)
4. **Monitor usage**: Regularly check sign-in logs and audit trails
5. **Production setup**: Use separate app registrations for dev/staging/prod

## Next Steps

After completing this setup:

1. ✅ Update your `appsettings.Development.json` with the Azure AD values
2. ✅ Configure your frontend authentication in `authConfig.ts`
3. ✅ Test the authentication flow
4. ✅ Deploy to production and update redirect URIs accordingly

For more information, see the [Microsoft Identity Platform documentation](https://docs.microsoft.com/en-us/azure/active-directory/develop/).
