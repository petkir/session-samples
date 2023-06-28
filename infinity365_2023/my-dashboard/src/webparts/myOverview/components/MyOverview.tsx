/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-floating-promises */
/* eslint-disable @typescript-eslint/no-explicit-any */
import * as React from 'react';
import styles from './MyOverview.module.scss';
import { IMyOverviewProps } from './IMyOverviewProps';
import { escape } from '@microsoft/sp-lodash-subset';
import { Agenda } from '@microsoft/mgt-react/dist/es6/generated/react';
import { DataService } from '../../../services/DataService';
import { IWorkItemValue } from '../../../services/IAzureDevOps';
import { ITicket } from '../../../services/ITicket';
import { DevOpsService } from '../../../services/DevOpsService';

interface IMyOverviewState {
  tickets?: ITicket[];
  tasks?: IWorkItemValue[];
}

export default class MyOverview extends React.Component<IMyOverviewProps, IMyOverviewState> {
  svc: DataService = undefined;
  dsvc: DevOpsService = undefined;
  constructor(props: IMyOverviewProps) {
    super(props)
    this.svc = new DataService(props.context);
    this.dsvc = new DevOpsService(props.context);
    this.state = {};
  }

  public componentDidMount(): void {
    this.getData();
  }

  private async getData(): Promise<void> {
    
    const tickets = await this.svc.getMyTickets().catch((ex)=>{console.log(ex); return [];});
    let tasks = await this.dsvc.getDevOpsTasks().catch((ex)=>{console.log(ex); return [];});
    if(tasks.length>5)
     tasks=tasks.slice(0,5);
    this.setState({
      tasks: tasks ,
      tickets: tickets
    })
  }

  public render(): React.ReactElement<IMyOverviewProps> {
    const {

      hasTeamsContext,
      userDisplayName
    } = this.props;
    const {
      tasks,
      tickets
    } = this.state;
    return (
      <section className={`${styles.myOverview} ${hasTeamsContext ? styles.teams : ''}`}>
        <div>
          <h3>Hi {escape(userDisplayName)}!</h3>
          <div>
            <h4>Kalender</h4>
            <Agenda />
          </div>
          <div>
            <h4>Tickets</h4>
            {tickets && tickets.length > 0 ?
              <ul>
                {tickets.map((x, i) => <li key={"t" + i}><i>{x.area}</i>:  {x.subject}</li>)}
              </ul>
              : <p>No Data Found</p>}
          </div>
          <div>
            <h4>DevOps</h4>
            {tasks && tasks.length > 0 ?
              <ul>
                {tasks.map((x, i) => <li key={"t" + i}>{x.fields["System.Title"]}</li>)}
              </ul>
              : <p>No Data Found</p>}

            </div> 
        </div>
      </section>
    );
  }
}
