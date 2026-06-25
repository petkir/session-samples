import { 
  Group, 
  Title, 
  Avatar, 
  Menu, 
  Text, 
  Divider,
  Box,
  Stack,
  UnstyledButton
} from '@mantine/core';
import { 
  IconUser, 
  IconLogout, 
  IconUserPlus, 
  IconChevronDown
} from '@tabler/icons-react';
import { User } from '../hooks/useAuth';
import ThemeToggle from './ThemeToggle';
import './AppHeader.scss';

interface AppHeaderProps {
  user?: User | null;
  onLogout?: () => void;
  onSwitchUser?: () => void;
}

const AppHeader = ({ user, onLogout, onSwitchUser }: AppHeaderProps) => {
  // Generate a mock avatar URL based on user email or use provided avatar
  const getAvatarUrl = (user: User) => {
    return user.avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.name)}&background=339af0&color=fff&size=40`;
  };

  return (
    <div className="app-header">
      <Group h="100%" px="md" justify="space-between">
        {/* Left side - App title */}
        <Group>
          <Title order={3} c="blue.6">
            💬 Chat App
          </Title>
        </Group>

        {/* Right side - Theme toggle first, then user profile */}
        <Group gap="md">
          <ThemeToggle />
          
          {user && (
            <Menu 
              shadow="md" 
              width={320} 
              position="bottom-end"
              withArrow
              arrowPosition="center"
            >
              <Menu.Target>
                <UnstyledButton className="user-button">
                  <Group gap="sm">
                    <Avatar
                      src={getAvatarUrl(user)}
                      size={32}
                      radius="xl"
                      alt={user.name}
                    />
                    <Box style={{ flex: 1 }}>
                      <Text size="sm" fw={500}>
                        {user.name}
                      </Text>
                     </Box>
                    <IconChevronDown size={14} />
                  </Group>
                </UnstyledButton>
              </Menu.Target>

              <Menu.Dropdown>
                <Menu.Label>Account</Menu.Label>
                <Box p="md">
                  <Group gap="md">
                    <Avatar
                      src={getAvatarUrl(user)}
                      size={48}
                      radius="xl"
                      alt={user.name}
                    />
                    <Stack gap={4} style={{ flex: 1 }}>
                      <Text size="sm" fw={500}>
                        {user.name}
                      </Text>
                      <Text size="xs" c="dimmed">
                        {user.email}
                      </Text>
                    </Stack>
                  </Group>
                </Box>
                
                <Divider />
                
                <Menu.Item
                  leftSection={<IconUser size={14} />}
                  onClick={() => {
                    // Handle profile click - could open a profile modal
                    console.log('Profile clicked');
                  }}
                >
                  Profile Settings
                </Menu.Item>
                
                <Menu.Item
                  leftSection={<IconUserPlus size={14} />}
                  onClick={onSwitchUser}
                >
                  Sign in as another user
                </Menu.Item>
                
                <Divider />
                
                <Menu.Item
                  leftSection={<IconLogout size={14} />}
                  color="red"
                  onClick={onLogout}
                >
                  Sign out
                </Menu.Item>
              </Menu.Dropdown>
            </Menu>
          )}
        </Group>
      </Group>
    </div>
  );
};

export default AppHeader;
