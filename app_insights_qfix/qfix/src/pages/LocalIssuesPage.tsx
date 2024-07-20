import { useEffect, useState } from "react";
import { issueReportingService, IssueType } from "../services/IssueReportingService";

const LocalIssuesPage = () => {
    const [items,setItems] = useState<IssueType[]>([]);
    const [loading,setLoading] = useState(false);
    useEffect(() => {
        document.title = "Local Issues";
        async function fetchData() {
            try{
        const data=await issueReportingService.getIssues();
        setItems(data);
        setLoading(false);
            }catch(err){
                setLoading(false);
                console.error(err);
            }
        }
        setLoading(true);
        fetchData();
    } ,[] );
    
  return (
    <div>
      <h1>Local Issues</h1>
      {loading &&<p>Local issues page content loading...</p>}
      {!loading && items.length === 0 && <p>No local issues found</p>}
      {!loading && items.length > 0 && (
       items.map((item,index) => {
        return (
          <div key={index}>
            <h2>{item.description}</h2>
            <img  src={URL.createObjectURL(item.photo)} alt={item.filename} />
          </div>
        );
       } )
      )}
    </div>
  );
}

export default LocalIssuesPage;