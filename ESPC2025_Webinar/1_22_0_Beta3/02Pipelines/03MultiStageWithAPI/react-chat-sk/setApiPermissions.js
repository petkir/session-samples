/* Use The Environment Variables to set the API Permissions For Package Solution   */

/*
ENV: ENTRA_ResourceName=webApiPermissionRequests.resource   default: "react-chat-sk-api"
ENV: ENTRA_ResourceAppId=webApiPermissionRequests.appId default: "c032171c-4d2c-4b30-9572-f649390a4c8c"
ENV: ENTRA_ResourceScope=webApiPermissionRequests.scope default: "user_impersonation"
ENV: ENTRA_ResourceReplyUrl=webApiPermissionRequests.replyUrl default: "http://localhost:7071"
*/    


import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);


export const setApiPermissions = (env) => {
  const packageSolutionPath = path.join(__dirname, './config/package-solution.json');
    console.log(`Setting API Permissions in ${packageSolutionPath}`);
  
  if (fs.existsSync(packageSolutionPath)) {
    const data = fs.readFileSync(packageSolutionPath, 'utf8');
    let packageSolution = JSON.parse(data);

    if(env.ENTRA_ResourceName && env.ENTRA_ResourceAppId ){ 
    const apiPermissions =[];
    const apiPermission = {};

    apiPermission.resourceName = env.ENTRA_ResourceName ;
    apiPermission.resourceAppId = env.ENTRA_ResourceAppId ;
    apiPermission.resourceScope = env.ENTRA_ResourceScope || "user_impersonation";
    apiPermission.resourceReplyUrl = env.ENTRA_ResourceReplyUrl ;
    
    apiPermissions.push(apiPermission);
    packageSolution.webApiPermissionRequests = apiPermissions;
    fs.writeFileSync(packageSolutionPath, JSON.stringify(packageSolution, null, 2), 'utf8');
    console.log(`API Permissions set successfully in ${packageSolutionPath}`);
    }
    else {
      console.log(`Environment variables ENTRA_ResourceName and ENTRA_ResourceAppId are required to set API permissions.`);
    }
  }else {
    console.log(`Package solution file not found at ${packageSolutionPath}`);
  }
};

setApiPermissions(process.env);

