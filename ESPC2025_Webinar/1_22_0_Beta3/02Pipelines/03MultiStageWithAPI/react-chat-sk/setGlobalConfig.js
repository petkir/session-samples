/* Use The Environment Variables to set the Global Configuration */

/*
ENV: ENTRA_ResourceAppId - Azure Function App Registration Client ID
ENV: ENTRA_ResourceReplyUrl - Azure Function URL
*/

const fs = require('fs');
const path = require('path');

const setGlobalConfig = (env) => {
  const globalConfigPath = path.join(__dirname, './src/globalConfig.ts');
  console.log(`Setting Global Configuration in ${globalConfigPath}`);
  
  const appId = env.ENTRA_ResourceAppId;
  const replyUrl = env.ENTRA_ResourceReplyUrl;

  if (appId && replyUrl) {
    const configContent = `export const AZURE_FUNCTION_APP_ID = "${appId}";

export const AZURE_FUNCTION_URL = "${replyUrl}";
`;
    
    fs.writeFileSync(globalConfigPath, configContent, 'utf8');
    console.log(`Global configuration set successfully in ${globalConfigPath}`);
    console.log(`  AZURE_FUNCTION_APP_ID: ${appId}`);
    console.log(`  AZURE_FUNCTION_URL: ${replyUrl}`);
  } else {
    console.log(`Environment variables ENTRA_ResourceAppId and ENTRA_ResourceReplyUrl are required.`);
    console.log(`Skipping globalConfig.ts generation - file will use existing values.`);
  }
};

module.exports = { setGlobalConfig };

// Run if called directly
if (require.main === module) {
  setGlobalConfig(process.env);
}
