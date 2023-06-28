import { WebPartContext } from "@microsoft/sp-webpart-base";
import { AadHttpClient } from '@microsoft/sp-http';
import { IAzdoAccount, IAzdoProfile, IAzdoWorkItemReference, IWorkItemValue } from "./IAzureDevOps";


const devOpsEndPointID: string = "499b84ac-1321-427f-aa17-267ca6975798";

export class DevOpsService {
  private ctx: WebPartContext;
  private apiclient: AadHttpClient;
  constructor(ctx: | WebPartContext) {
    this.ctx = ctx;
  }

  private async InitAADClient(): Promise<void> {
    if (!this.apiclient) {
      this.apiclient = await this.ctx.aadHttpClientFactory.getClient(devOpsEndPointID);
    }
  }

  async getDevOpsTasks(): Promise<IWorkItemValue[]> {
    await this.InitAADClient();

    const tasks = [];
    try {
      const profile = await this.getProfile();
      const accounts = await this.getAccounts(profile.id);
      for (const account of accounts) {
        const queryResult = await this.getAssignedTasks(account.accountName);
        tasks.push(...(await this.getTasks(account.accountName, queryResult.map(x => x.id))));
      }
    } catch (ex) {
      console.log(ex);
      alert(ex);
    }
    return tasks;
  }


  public async getProfile(): Promise<IAzdoProfile> {
    await this.InitAADClient();
    const response = await this.apiclient.get(
      'https://app.vssps.visualstudio.com/_apis/profile/profiles/me?api-version=7.1-preview.3',
      AadHttpClient.configurations.v1);
    const json = await response.json();
    return json as IAzdoProfile;
  }

  public async getAccounts(memberId: string): Promise<IAzdoAccount[]> {
    await this.InitAADClient();
    const response = await this.apiclient.get(
      `https://app.vssps.visualstudio.com/_apis/accounts?memberId=${memberId}&api-version=7.1-preview.1`,
      AadHttpClient.configurations.v1);
    const json = await response.json();
    return json.value as IAzdoAccount[];
  }

  public async getAssignedTasks(organizationName: string): Promise<IAzdoWorkItemReference[]> {
    await this.InitAADClient();
    const response = await this.apiclient.post(
      `https://dev.azure.com/${organizationName}/_apis/wit/wiql?api-version=7.0`,
      AadHttpClient.configurations.v1,
      {
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          query: "SELECT"
            + "[System.Id]"
            + " FROM WorkItems"
            + " WHERE [System.WorkItemType] = 'Task'"
            + " AND [State] <> 'Closed'"
            + " AND [State] <> 'Removed'"
            + " AND [System.AssignedTo] = @Me"
        })
      });
    const json = await response.json();
    return json.workItems as IAzdoWorkItemReference[];
  }

  public async getTasks(organizationName: string, ids: number[]): Promise<IWorkItemValue[]> {
    await this.InitAADClient();
    const response = await this.apiclient.get(
      `https://dev.azure.com/${organizationName}/_apis/wit/workitems?ids=${ids.join(',')}&$expand=all&api-version=7.0`,
      AadHttpClient.configurations.v1,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      });
    const json = await response.json();
    return json.value as IWorkItemValue[];
  }

}

