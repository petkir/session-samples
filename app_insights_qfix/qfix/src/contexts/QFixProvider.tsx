import { createContext, ReactNode, useContext, useState } from "react";


type QFixContextType = {
    loggedInState: number;
    setLoggedInState: (value:number) => void;
    user?: any;
    setUser: (user: any) => void;
    issueCount: number;
    setIssueCount: (issueCount: number) => void;
    incrementIssueCount: () => void;
  };


const QFixContext = createContext<QFixContextType | undefined>(undefined);

export const QFixProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [loggedInState, setLoggedInState] = useState(0);
    const [user, setUser] = useState<any>(undefined);
    const [issueCount, setIssueCount] = useState<number>(0);
  
    const incrementIssueCount = () => {
        setIssueCount(issueCount + 1);
        }
  
    return (
      <QFixContext.Provider value={{ loggedInState, setLoggedInState , user,setUser,issueCount,setIssueCount,incrementIssueCount}}>
        
          {children}
        
      </QFixContext.Provider>
    );
  };
  
  

  export const useQFix = ():QFixContextType => {
    const context = useContext(QFixContext);
    if (!context) {
      throw new Error('useQFix must be used within a QFixProvider');
    }
    return context;
  }