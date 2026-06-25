import { Container, Paper, Title, Text, Button, Center, Stack } from '@mantine/core';
import { IconLogin } from '@tabler/icons-react';
import './Login.scss';

interface LoginProps {
  onLogin: () => void;
}

const Login = ({ onLogin }: LoginProps) => {
  return (
    <Container size="xs" className="login-container">
      <Center style={{ minHeight: '100vh' }}>
        <Paper shadow="md" p="xl" radius="md" withBorder className="login-card">
          <Stack gap="md" align="center">
            <div className="login-header">
              <Title order={1} ta="center" mb="sm">
                Welcome to Chat App
              </Title>
              <Text c="dimmed" ta="center">
                Please sign in to continue
              </Text>
            </div>
            
            <Button 
              leftSection={<IconLogin size={20} />}
              size="lg"
              fullWidth
              onClick={onLogin}
              variant="filled"
              className="login-button"
            >
              Sign in with Microsoft
            </Button>
            
            <div className="login-footer">
              <Text size="sm" c="dimmed" ta="center">
                This app uses Entra ID for authentication
              </Text>
            </div>
          </Stack>
        </Paper>
      </Center>
    </Container>
  );
};

export default Login;
