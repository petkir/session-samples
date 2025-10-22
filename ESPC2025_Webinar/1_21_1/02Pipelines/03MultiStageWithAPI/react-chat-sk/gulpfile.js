'use strict';

const build = require('@microsoft/sp-build-web');
const gulp = require('gulp');
const fs = require('fs');
const path = require('path');



build.addSuppression(`Warning - [sass] The local CSS class 'ms-Grid' is not camelCase and will not be type-safe.`);

var getTasks = build.rig.getTasks;
build.rig.getTasks = function () {
  var result = getTasks.call(build.rig);

  result.set('serve', result.get('serve-deprecated'));

  return result;
};



let setApiPermissions = build.subTask('set-api-permissions', function(gulp, buildOptions, done) {
  if (build.getConfig().args.production || build.getConfig().args.ship) {
  this.log('Setting API Permissions for production/ship build...'+__dirname);
   const env = process.env;
  const packageSolutionPath = path.join(__dirname, 'config/package-solution.json');
  
  this.log(' ENTRA_ResourceName: ' + env.ENTRA_ResourceName);
  this.log(' ENTRA_ResourceAppId: ' + env.ENTRA_ResourceAppId);
  this.log(' ENTRA_ResourceScope: ' + env.ENTRA_ResourceScope);
  this.log(' ENTRA_ResourceReplyUrl: ' + env.ENTRA_ResourceReplyUrl);
  if(env.ENTRA_ResourceName && env.ENTRA_ResourceAppId ){
      const data = fs.readFileSync(packageSolutionPath, 'utf8');
      let packageSolution = JSON.parse(data);
      const apiPermissions =[];
      const apiPermission = {};
  
      apiPermission.resourceName = env.ENTRA_ResourceName ;
      apiPermission.resourceAppId = env.ENTRA_ResourceAppId ;
      apiPermission.resourceScope = env.ENTRA_ResourceScope || "user_impersonation";
      apiPermission.resourceReplyUrl = env. ENTRA_ResourceReplyUrl ;
      
      apiPermissions.push(apiPermission);
      packageSolution.webApiPermissionRequests = apiPermissions;
      fs.writeFileSync(packageSolutionPath, JSON.stringify(packageSolution, null, 2), 'utf8');
    }else{
      this.logWarning('Environment variables for API Permissions not set. Skipping...');
    }

}else{
  this.log('Skipping setting API Permissions for non-production build...');
 
}

  done();
});
build.rig.addPostTypescriptTask(setApiPermissions);

//build.rig.addPreBuildTask(setApiPermissions);

build.initialize(gulp);
