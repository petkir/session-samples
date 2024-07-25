import React from 'react';
import { mergeStyleSets } from '@fluentui/react/lib/Styling';



import { Toggle, DefaultButton, FontIcon, OverflowSet, IOverflowSetItemProps, IconButton, IButtonStyles } from '@fluentui/react';

import { useTheme } from '../contexts/ThemeProvider';
import { useQFix} from '../contexts/QFixProvider';
import { Link, useNavigate } from 'react-router-dom';




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
  const items: IOverflowSetItemProps[] = [
    {
      key: 'home',
      text: 'Home',
      iconProps: { iconName: 'Home' },
      onClick: () => {
        navigate('/')},
    },
    {
      key: 'report-issue',
      text: 'New Report',
      iconProps: { iconName: 'IconsFilled' },
      
      onClick: () => {
        navigate('/report-issue')},
    },
    {
      key: 'unsubmitted-issue',
      text: 'Requests',
      iconProps: { iconName: 'IconsFilled' },
      onClick: () => { 
        navigate('/unsubmitted-issue')},
    
    },
  ];
  const onRenderItem = (item: IOverflowSetItemProps): JSX.Element => {
    return (
     
      <Link style={{paddingRight:'20px'}} to={'/'+item.key} onClick={item.onClick}>
        {item.text}
      </Link>
    );
  };
  
  return (
    <>
    <div className={classNames.container}>
      <div>QFix</div>
      
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
    <div className={classNames.container}>
      <OverflowSet
      
      items={items}
      role='menu'
      onRenderOverflowButton={onRenderOverflowButton}
    onRenderItem={onRenderItem}
      />
      </div>
    </>
  );
};



const onRenderOverflowButton = (overflowItems: any[] | undefined): JSX.Element => {
  const buttonStyles: Partial<IButtonStyles> = {
    root: {
      minWidth: 0,
      padding: '0 4px',
      alignSelf: 'stretch',
      height: 'auto',
    },
  };
  return (
    <IconButton
      title="More options"
      styles={buttonStyles}
      menuIconProps={{ iconName: 'More' }}
      menuProps={{ items: overflowItems! }}
    />
  );
};
export default Header;
