import { Container, Stack, Loader, Text, Center } from '@mantine/core';
import './Loading.scss';

const Loading = () => {
  return (
    <Container className="loading-container">
      <Center style={{ minHeight: '100vh' }}>
        <Stack align="center" gap="lg">
          <Loader size="lg" type="dots" color="blue" />
          <Text size="lg" fw={500} c="dimmed">
            Loading...
          </Text>
        </Stack>
      </Center>
    </Container>
  );
};

export default Loading;
