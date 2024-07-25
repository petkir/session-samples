import { mergeStyleSets } from "@fluentui/react";
import { Link } from "react-router-dom";

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
  }
});

const Header: React.FC = () => {


  return (
    <div className={classNames.container}>
      <Link to="datenrichtlinie">Datenverwenungs-Richtlinie </Link>

    </div>
  );
};

export default Header;