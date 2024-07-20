import React, { useEffect, useState } from 'react';
import {  Stack, Text, Toggle } from '@fluentui/react';
import { APPInsigthConnectionstring, EntraIDClientID } from '../config';

import { msalInstance } from '../entraID';
import { useQFix } from '../contexts/QFixProvider';

const Home: React.FC = () => {
  const [debug,setDebug] = useState(false);
  const { user, setUser,loggedInState, setLoggedInState } = useQFix();
  
  useEffect(() => {
     if((msalInstance as any).getAllAccounts()>0 && loggedInState ===0){
     
    }  setLoggedInState(1);
     setUser((msalInstance as any).getAllAccounts()[0]);
   
    
  },[loggedInState,setLoggedInState,setUser])

  return (
    <Stack horizontalAlign="center" verticalAlign="center" styles={{ root: { height: 'calc( 100vh - 64px)' } }}>
      <Text variant="xxLarge">Welcome to QFix</Text>
      <Text variant="large">Use this app to report any issues within the facility.</Text>
      <Toggle onChange={()=>setDebug(!debug)} checked={debug} inlineLabel={true} label={debug ? 'Show Configuration enabled' : 'Show Configuration disabled'} />
      {debug && <p>
      <Text variant="large">{EntraIDClientID}</Text><br />
      <Text variant="large">{APPInsigthConnectionstring}</Text>
      <Text variant="large">{JSON.stringify(user)}</Text>
      </p>}
       <div>
       {loggedInState ===0 && <button onClick={async ():Promise<void> => {
          try {
            
            debugger;
            const loginResponse = await msalInstance.loginPopup();
            
            setLoggedInState(loginResponse.account ? 1 : 0);
            setUser(loginResponse.account);
            
        } catch (err) {
            // handle error

            console.error(err);
            debugger;
        }

        }}>Login</button>
      }
        </div>
        
    </Stack>
  );
};

export default Home;
