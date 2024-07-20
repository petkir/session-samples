import React from 'react';
import { CommandBar, ICommandBarItemProps } from '@fluentui/react/lib/CommandBar';
import { mergeStyleSets } from '@fluentui/react/lib/Styling';



import { Toggle, DefaultButton, FontIcon } from '@fluentui/react';

import { useTheme } from '../contexts/ThemeProvider';
import { useQFix} from '../contexts/QFixProvider';
import {  useNavigate } from 'react-router-dom';




const classNames = mergeStyleSets({
  container: {
    
    padding: '10px 30px',
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
  badge :{
    backgroundColor: 'red',
    color: 'white',
    width: '20px',
    height: '20px',
    borderRadius: '50%',
    marginLeft: '-10px',
    mrginTop: '0px',
    fontSize: '12px',
    display: 'inline-block',
    position: 'absolute',
    top: '0',
  
  },
  badgecontainer: { 
    display: 'inline-block',
    position: 'relative',
    marginLeft: '20px',
  }
});

const Header: React.FC = () => {
  console.log('Header');

  const { isDarkTheme, toggleTheme } = useTheme(); 
  const { user,issueCount } = useQFix();
  
  const navigate = useNavigate();
  const items: ICommandBarItemProps[] = [
    {
      key: 'home',
      text: 'Home',
      iconProps: { iconName: 'Home' },
      onClick: (ev) => {ev?.stopPropagation(); 
        navigate('/')},
    },
    {
      key: 'report-issue',
      text: 'report-issue',
      iconProps: { iconName: 'IconsFilled' },
      
      onClick: (ev) => {ev?.stopPropagation(); 
        navigate('/report-issue')},
    },
    {
      key: 'unsubmitted-issue',
      text: 'unsubmitted-issue',
      iconProps: { iconName: 'IconsFilled' },
      onClick: (ev) => {ev?.stopPropagation(); 
        navigate('/unsubmitted-issue')},
    
    },
  ];
  
  
  return (
    <div className={classNames.container}>
      <div>QFix</div>
      <CommandBar items={items} />
      <div className={classNames.switchContainer}>
        <Toggle onChange={toggleTheme} checked={isDarkTheme} onText='Dark Mode' offText='Light Mode' />
      </div>
      <div>
      
        <DefaultButton text={user?.name}/>
        <div className={classNames.badgecontainer} >
        <FontIcon iconName='Dictionary' />
        <span className={classNames.badge}>{issueCount}</span>
        </div>
        
      </div>
    </div>
  );
};

export default Header;
