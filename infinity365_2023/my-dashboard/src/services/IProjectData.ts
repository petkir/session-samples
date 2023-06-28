
export interface IProjectData{
name:string;
customer:string;
status:string;
percentage:number;
projectmanager:IProjectUser;
}

export interface IProjectUser{
    userID: string ;
    displayName: string;
}
