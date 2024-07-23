import { useEffect,ReactNode } from "react";
import { msalInstance } from "../entraID";
import { useQFix } from "../contexts/QFixProvider";
import { issueReportingService } from "../services/IssueReportingService";


export  const LoginCheck: React.FC<{ children: ReactNode }> = ({ children }) => {
    const { user, setUser,loggedInState, setLoggedInState,setIssueCount } = useQFix();
  useEffect(() => {

    issueReportingService.getUnsyncedIssues().then((issues) => {
        if (issues.length > 0) {
         setIssueCount(issues.length);
        }
    });
    if((msalInstance as any).getAllAccounts()>0 && loggedInState ===0){
    
   }  setLoggedInState(1);
    setUser((msalInstance as any).getAllAccounts()[0]);
  
   
 },[loggedInState,setLoggedInState,setUser])
      
        return (
          <>
              {children}
            </>
        );
      };

    
