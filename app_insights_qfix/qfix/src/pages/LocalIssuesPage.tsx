import { useEffect, useState } from "react";
import { issueReportingService, IssueType } from "../services/IssueReportingService";
import { DefaultButton, Stack } from "@fluentui/react";
import { syntaxHighlight } from "../helper/syntaxHighlight";

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
    <Stack styles={{ root: { height: '-webkit-fill-available' } }}>
<div>      <h1>Local Issues</h1> 
             </div>
      {loading &&<p>Local issues page content loading...</p>}
      {!loading && items.length === 0 && <p>No local issues found</p>}
      {!loading && items.length > 0 && (
       items.map((item,index) => {
        const pos1 = item.photoPosition?JSON.parse(item.photoPosition):undefined;
        const pos2 = item.submitPosition?JSON.parse(item.submitPosition):undefined;
        return (
          <div key={index} style={{ padding:'10px 50px'}}>
            <span>{index}</span>
            <h2>{item.description}</h2>
            <img height={'60px'} src={URL.createObjectURL(item.photo)} alt={item.filename} />
            {pos1 && <div><a target="_blank"  rel="noreferrer"  href={`https://www.google.com/maps/search/?api=1&query=${pos1?.coords?.latitude},${pos1?.coords?.longitude}`} ><span>photoPosition Maps</span></a></div>}
            <pre dangerouslySetInnerHTML={{__html:syntaxHighlight(pos1)}} />
            {pos2 && <div><a target="_blank"  rel="noreferrer"  href={`https://www.google.com/maps/search/?api=1&query=${pos2?.coords?.latitude},${pos2?.coords?.longitude}`} ><span>submitPosition Maps</span></a></div>}
            <pre dangerouslySetInnerHTML={{__html:syntaxHighlight(pos2)}} />
          </div>
        );
       } )
      )}
<div style={{height:'50px'}}></div>
<div>    
      <DefaultButton text="clear LocalDB" onClick={async ()=>{
        setLoading(true);
        issueReportingService.cleanCache()
        const data=await issueReportingService.getIssues();
        setItems(data);
        setLoading(false);
      }
             } />
             </div>
    </Stack>
  );
}

export default LocalIssuesPage;


