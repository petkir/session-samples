/* Use The Environment Variables to set the API Permissions For Package Solution   */

/*
ENV: ENTRA_ResourceName=webApiPermissionRequests.resource   default: "react-chat-sk-api"
ENV: ENTRA_ResourceAppId=webApiPermissionRequests.appId default: "c032171c-4d2c-4b30-9572-f649390a4c8c"
ENV: ENTRA_ResourceScope=webApiPermissionRequests.scope default: "user_impersonation"
ENV: ENTRA_ResourceReplyUrl=webApiPermissionRequests.replyUrl default: "http://localhost:7071"
*/    


const fs = require('fs');
const path = require('path');

const setApiPermissions = (env) => {
  const packageSolutionPath = path.join(__dirname, './config/package-solution.json');
  console.log(`Setting API Permissions in ${packageSolutionPath}`);
  
  if (fs.existsSync(packageSolutionPath)) {
    const data = fs.readFileSync(packageSolutionPath, 'utf8');
    let packageSolution = JSON.parse(data);

    if(env.ENTRA_ResourceName && env.ENTRA_ResourceAppId ){ 
      const apiPermissions =[];
      const apiPermission = {};

      apiPermission.resource = env.ENTRA_ResourceName ;
      apiPermission.appId = env.ENTRA_ResourceAppId ;
      apiPermission.scope = env.ENTRA_ResourceScope || "user_impersonation";
      apiPermission.replyUrl = env.ENTRA_ResourceReplyUrl ;
      
      apiPermissions.push(apiPermission);
      packageSolution.solution.webApiPermissionRequests = apiPermissions;
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

module.exports = { setApiPermissions };

// Run if called directly
if (require.main === module) {
  setApiPermissions(process.env);
}

