import React, {  useState } from 'react';
import {  Stack, Text, Toggle } from '@fluentui/react';
import { APPInsigthConnectionstring, EntraIDAuthority, EntraIDClientID } from '../config';

import { msalInstance } from '../entraID';
import { useQFix } from '../contexts/QFixProvider';
import { appInsightUserSet } from '../appInsights';
import { syntaxHighlight } from '../helper/syntaxHighlight';

const Home: React.FC = () => {
  const [debug,setDebug] = useState(false);
  const { user, setUser,loggedInState, setLoggedInState } = useQFix();
  
  

  return (
    <Stack horizontalAlign="center" verticalAlign="center" styles={{ root: { height: 'calc( 100vh - 116px)',overflow:'hidden' } }}>
      <Text variant="xxLarge">Welcome to QFix</Text>
      <Text variant="large">Use this app to report any issues within the facility.</Text>
      <Toggle onChange={()=>setDebug(!debug)} checked={debug} inlineLabel={true} label={debug ? 'Show Configuration enabled' : 'Show Configuration disabled'} />
      {debug && <p>
      <Text variant="large">EntraIDClientID:</Text><Text>{EntraIDClientID}</Text><br />
      <Text variant="large">EntraIDAuthority</Text><Text>{EntraIDAuthority}</Text>
      <Text variant="large">APPInsigthConnectionString:</Text><Text>{APPInsigthConnectionstring}</Text>
      <Text variant="large">User</Text><Text><pre dangerouslySetInnerHTML={{__html:syntaxHighlight(user)}} /></Text>
      </p>}
       <div>
       {(loggedInState ===0 || msalInstance.getAllAccounts().length ===0 )&& <button onClick={async ():Promise<void> => {
          try {
            const loginResponse = await msalInstance.loginPopup();
            
            setLoggedInState(loginResponse.account ? 1 : 0);
            setUser(loginResponse.account);
            appInsightUserSet(loginResponse.account.homeAccountId);
            
        } catch (err) {
            console.error(err);
            
        }

        }}>Login</button>
      }
        </div>
        
    </Stack>
  );
};

export default Home;
