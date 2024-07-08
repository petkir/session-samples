import React from 'react';
import { Stack, Text } from '@fluentui/react';

const Home: React.FC = () => {
  return (
    <Stack horizontalAlign="center" verticalAlign="center" styles={{ root: { height: '100vh' } }}>
      <Text variant="xxLarge">Welcome to QFix</Text>
      <Text variant="large">Use this app to report any issues within the facility.</Text>
    </Stack>
  );
};

export default Home;
