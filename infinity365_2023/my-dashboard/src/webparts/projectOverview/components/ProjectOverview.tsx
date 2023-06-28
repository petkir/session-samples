/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/explicit-function-return-type */
/* eslint-disable @typescript-eslint/no-floating-promises */
import * as React from 'react';
import styles from './ProjectOverview.module.scss';
import { IProjectOverviewProps } from './IProjectOverviewProps';


import { DataService } from '../../../services/DataService';
import { IProjectData } from '../../../services/IProjectData';
import { ListView, IViewField, SelectionMode } from "@pnp/spfx-controls-react/lib/ListView";
interface IProjectOverviewState {
  projects?: IProjectData[];

}

export default class ProjectOverview extends React.Component<IProjectOverviewProps, IProjectOverviewState> {

  svc: DataService = undefined;

  constructor(props: IProjectOverviewProps) {
    super(props)
    this.svc = new DataService(props.context);

    this.state = {};
  }
  public componentDidMount(): void {
    this.getData();
  }
  private async getData(): Promise<void> {

    const projects = await this.svc.getMyProjects().catch((ex) => { console.log(ex); return []; });

    this.setState({
      projects: projects
    })
  }
  private _getSelection(items: any[]) {
    console.log('Selected items:', items);
  }

  public render(): React.ReactElement<IProjectOverviewProps> {

    const items = this.state.projects;
    const viewFields: IViewField[] = [
      { name: "name", displayName: "Titel", sorting: true },
      { name: "customer", displayName: "Kunde", sorting: true },
      { name: "status", displayName: "Status" },
      {
        name: "percentage", displayName: "Fertigstellung", sorting: true,
        render: (item?: any, index?: number) => {
          return (<div style={{ width: '100%',height:'100%' }}>
            <div style={{ width: item.percentage + '%', backgroundColor: 'lightgray',height:'100%' }} />
          </div>);
        }
      },
      { name: "projectmanager.displayName", displayName: "ProjectManager", sorting: true }

    ]
    const {
      hasTeamsContext,
    } = this.props;

    return (
      <section className={`${styles.projectOverview} ${hasTeamsContext ? styles.teams : ''}`}>
        <div>
          <h3>Overview</h3>
          {items && items.length > 0 ? <ListView
            items={items}
            viewFields={viewFields}
            compact={true}
            selectionMode={SelectionMode.none}
            selection={this._getSelection}
            showFilter={true}
            filterPlaceHolder="Search..."
            stickyHeader={true}
          /> : <div>No Data</div>}
        </div>
      </section>
    );
  }
}
