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

appInsights.loadAppInsights();

export { appInsights, reactPlugin };
