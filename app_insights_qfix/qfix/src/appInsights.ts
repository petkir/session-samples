import { ApplicationInsights } from '@microsoft/applicationinsights-web';
import { ReactPlugin } from '@microsoft/applicationinsights-react-js';
import { APPInsigthConnectionstring } from './config';

const reactPlugin = new ReactPlugin();
const appInsights = new ApplicationInsights({
  config: {
    connectionString: APPInsigthConnectionstring,
    enableAutoRouteTracking: true,

    extensions: [reactPlugin],
    /*extensionConfig: {
      [reactPlugin.identifier]: { history: {} },
    },*/
  },
});


appInsights.addTelemetryInitializer((envelope) => {
  envelope.data = envelope.data || {};
  envelope.tags = envelope.tags || {};
  envelope.tags['ai.cloud.role'] = 'SPA';
  envelope.tags["ai.cloud.roleInstance"] = "QFix";
  envelope.data.location = window.localStorage.getItem('position') || "";

}
)

appInsights.loadAppInsights();

export { appInsights, reactPlugin };



export function appInsightUserSet(signInId: string) {
  var validatedId = signInId.replace(/[,;=| ]+/g, "_");
  appInsights.setAuthenticatedUserContext(validatedId);

}

export function appInsightUserUnset() {
  appInsights.clearAuthenticatedUserContext();

}