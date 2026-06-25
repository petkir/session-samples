import { Container, Title, Text, Button, Stack, Paper, Group, Box, ThemeIcon } from '@mantine/core';
import { IconMessageCircle, IconRobot, IconBrain, IconSparkles } from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';

const DescriptionPage = () => {
  const navigate = useNavigate();

  const handleStartNewChat = () => {
    navigate('/chat/new');
  };

  return (
    <Container size="md" py="xl">
      <Stack gap="xl" align="center">
        <Box ta="center">
          <ThemeIcon size={80} radius="xl" variant="gradient" gradient={{ from: 'blue', to: 'cyan' }}>
            <IconRobot size={40} />
          </ThemeIcon>
          <Title order={1} mt="md" size="3rem" fw={700} c="blue.6">
            Welcome to ESPC Chat
          </Title>
          <Text size="xl" c="dimmed" mt="sm">
            Your intelligent conversation partner powered by AI
          </Text>
        </Box>

        <Paper p="xl" radius="lg" shadow="sm" w="100%" maw={600}>
          <Stack gap="lg">
            <Group>
              <ThemeIcon size={40} radius="lg" variant="light" color="blue">
                <IconMessageCircle size={20} />
              </ThemeIcon>
              <Box flex={1}>
                <Text fw={500} size="lg">Start a Conversation</Text>
                <Text size="sm" c="dimmed">
                  Ask questions, get insights, and explore ideas with our AI assistant
                </Text>
              </Box>
            </Group>

            <Group>
              <ThemeIcon size={40} radius="lg" variant="light" color="green">
                <IconBrain size={20} />
              </ThemeIcon>
              <Box flex={1}>
                <Text fw={500} size="lg">Knowledge Base</Text>
                <Text size="sm" c="dimmed">
                  Access and search through your uploaded documents and knowledge
                </Text>
              </Box>
            </Group>

            <Group>
              <ThemeIcon size={40} radius="lg" variant="light" color="purple">
                <IconSparkles size={20} />
              </ThemeIcon>
              <Box flex={1}>
                <Text fw={500} size="lg">Smart Responses</Text>
                <Text size="sm" c="dimmed">
                  Get contextual answers based on your files and conversation history
                </Text>
              </Box>
            </Group>
          </Stack>
        </Paper>

        <Group gap="lg">
          <Button 
            size="lg" 
            onClick={handleStartNewChat}
            leftSection={<IconMessageCircle size={20} />}
          >
            Start New Chat
          </Button>
          <Button 
            size="lg" 
            variant="outline"
            onClick={() => navigate('/knowledge')}
          >
            Browse Knowledge
          </Button>
        </Group>

        <Paper p="md" radius="md" bg="blue.0" w="100%" maw={600}>
          <Text size="sm" c="blue.7" ta="center">
            💡 <strong>Tip:</strong> You can upload files during your conversation to get more contextual responses
          </Text>
        </Paper>
      </Stack>
    </Container>
  );
};

export default DescriptionPage;
