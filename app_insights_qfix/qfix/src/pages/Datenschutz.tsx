import React from 'react';
import { Stack, Text, } from '@fluentui/react';


const Datenschutz: React.FC = () => {

  return (
    <Stack horizontalAlign="center" verticalAlign="center" styles={{ root: { height: 'calc( 100vh - 64px)', overflow: 'hidden' } }}>
      <Text variant="large">Datenrichtlinie</Text><br />
      <Text>Da kommt noch ein Text</Text>
    </Stack>
  );
};

export default Datenschutz;
