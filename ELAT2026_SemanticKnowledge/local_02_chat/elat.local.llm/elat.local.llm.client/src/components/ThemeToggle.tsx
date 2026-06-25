import { ActionIcon } from '@mantine/core';
import { IconSun, IconMoon } from '@tabler/icons-react';
import { useTheme } from '../hooks/useTheme';

const ThemeToggle = () => {
  const { colorScheme, toggleColorScheme } = useTheme();

  return (
    <ActionIcon
      onClick={toggleColorScheme}
      variant="subtle"
      size="lg"
      aria-label="Toggle color scheme"
    >
      {colorScheme === 'dark' ? (
        <IconSun size={20} />
      ) : (
        <IconMoon size={20} />
      )}
    </ActionIcon>
  );
};

export default ThemeToggle;
