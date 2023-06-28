import { WebPartContext } from "@microsoft/sp-webpart-base";
import { AadHttpClient } from '@microsoft/sp-http';
import { ITicket } from "./ITicket";
import { IProjectData } from "./IProjectData";

const AADClientID: string = "api://316be047-7c44-48d0-ab33-0f21043eec7a";
//const AADBaseAPIURL: string = "https://myappspiservice.azurewebsites.net/api/"




export class DataService {
    private ctx: WebPartContext;
    private apiclient: AadHttpClient;

    constructor(ctx: | WebPartContext) {
        this.ctx = ctx;
    }

    private async InitAADClient(): Promise<void> {
        if (!this.apiclient) {
            this.apiclient = await this.ctx.aadHttpClientFactory.getClient(AADClientID);
        }
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    async getMyTickets(): Promise<ITicket[]> {
        await this.InitAADClient();
        /*
                const resp = await this.apiclient.get(
                    `${AADBaseAPIURL}GetTickets?$filter=...`,
                    AadHttpClient.configurations.v1);
                const data = await resp.json();
                */
        const data = [
            { id: "1", subject: "Nichts geht!!!", url: "asd", area: "Kunde1" },
            { id: "2", subject: "Geht wieder :-)", url: "asd", area: "Kunde1" }
        ]
        return data;
    }

    async getMyProjects(): Promise<IProjectData[]> {
        await this.InitAADClient();
        /*
                const resp = await this.apiclient.get(
                    `${AADBaseAPIURL}GetTickets?$filter=...`,
                    AadHttpClient.configurations.v1);
                const data = await resp.json();
                */
        const data:IProjectData[] = [
            { name: "Cooles BI Projekt", customer: "PPEDV", status: "in time", percentage: 10, projectmanager: { userID: "p.kirschner@cubido.at", displayName: "Peter Kirschner" } },
            { name: "SPFx Session", customer: "Infinity", status: "in time", percentage: 80, projectmanager: { userID: "p.kirschner@cubido.at", displayName: "Peter Kirschner" } }
        ]
        return data;
    }


}

