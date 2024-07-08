import React from 'react';
import { CommandBar, ICommandBarItemProps } from '@fluentui/react/lib/CommandBar';
import { mergeStyleSets } from '@fluentui/react/lib/Styling';

import { useTheme } from '../contexts/ThemeProvider';

import { Toggle } from '@fluentui/react';
import { Login } from '@microsoft/mgt-react';

const classNames = mergeStyleSets({
  container: {
    width: '100%',
    padding: '10px 0',
    backgroundColor: '#0078d4',
    color: 'white',
    textAlign: 'center',
    fontSize: '24px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  switchContainer: {
    display: 'flex',
    alignItems: 'center',
  },
  switchLabel: {
    marginLeft: '10px',
  },
});

const Header: React.FC = () => {
  const { isDarkTheme, toggleTheme } = useTheme();

  const items: ICommandBarItemProps[] = [
    {
      key: 'home',
      text: 'Home',
      iconProps: { iconName: 'Home' },
      href: '/',
    },
  ];

  return (
    <div className={classNames.container}>
      <div>QFix</div>
      <CommandBar items={items} />
      <div className={classNames.switchContainer}>
        <Toggle onChange={toggleTheme} checked={isDarkTheme} />
        <span className={classNames.switchLabel}>{isDarkTheme ? 'Dark Mode' : 'Light Mode'}</span>
      </div>
      <div>
        <Login />
      </div>
    </div>
  );
};

export default Header;
