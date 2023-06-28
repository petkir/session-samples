/* eslint-disable @typescript-eslint/no-explicit-any */
export interface IAzdoProfile {
    displayName?: string;
    publicAlias?: string;
    emailAddress?: string;
    coreRevision?: number;
    timeStamp?: string;
    id?: string;
    revisionrevision?: number;
  }
  
  export interface IAzdoAccount {
    accountId?: string;
    accountUri?: string;
    accountName?: string;
    properties?: unknown;
  }
  
  export interface IAzdoWorkItemReference {
    id: number;
    url: string;
  }


  export interface IWorkItemValue {
    id:         number;
    rev:        number;
    fields:     IValueFields;
    relations?: any[];
    _links:     IValueLinks;
    url:        string;
}
export interface IValueLinks {
    self:              IHTMLClass;
    workItemUpdates:   IHTMLClass;
    workItemRevisions: IHTMLClass;
    workItemComments:  IHTMLClass;
    html:              IHTMLClass;
    workItemType:      IHTMLClass;
    fields:            IHTMLClass;
}

export interface IValueFields {
    "System.Id":                                number;
    "System.AreaId":                            number;
    "System.AreaPath":                          string;
    "System.TeamProject":                       string;
    "System.NodeName":                          string;
    "System.AreaLevel1":                        string;
    "System.Rev":                               number;
    "System.AuthorizedDate":                    Date;
    "System.RevisedDate":                       Date;
    "System.IterationId":                       number;
    "System.IterationPath":                     string;
    "System.IterationLevel1":                   string;
    "System.IterationLevel2":                   string;
    "System.WorkItemType":                      string;
    "System.State":                             string;
    "System.Reason":                            string;
    "System.AssignedTo":                        IMicrosoftVstsCommonActivatedBy;
    "System.CreatedDate":                       Date;
    "System.CreatedBy":                         IMicrosoftVstsCommonActivatedBy;
    "System.ChangedDate":                       Date;
    "System.ChangedBy":                         IMicrosoftVstsCommonActivatedBy;
    "System.AuthorizedAs":                      IMicrosoftVstsCommonActivatedBy;
    "System.PersonId":                          number;
    "System.Watermark":                         number;
    "System.CommentCount":                      number;
    "System.Title":                             string;
    "Microsoft.VSTS.Common.StateChangeDate":    Date;
    "Microsoft.VSTS.Common.Priority":           number;
    "Microsoft.VSTS.Common.StackRank"?:         number;
    "System.Parent"?:                           number;
    "Microsoft.VSTS.Scheduling.RemainingWork"?: number;
    "Microsoft.VSTS.Scheduling.Effort"?:        number;
    "System.Description"?:                      string;
    "Microsoft.VSTS.Common.Triage"?:            string;
    "Microsoft.VSTS.CMMI.Blocked"?:             string;
    "Microsoft.VSTS.CMMI.TaskType"?:            string;
    "Microsoft.VSTS.CMMI.RequiresReview"?:      string;
    "Microsoft.VSTS.CMMI.RequiresTest"?:        string;
    "Microsoft.VSTS.Common.ActivatedDate"?:     Date;
    "Microsoft.VSTS.Common.ActivatedBy"?:       IMicrosoftVstsCommonActivatedBy;
    "Microsoft.VSTS.Common.ResolvedDate"?:      Date;
    "Microsoft.VSTS.Common.ResolvedBy"?:        IMicrosoftVstsCommonActivatedBy;
    "Microsoft.VSTS.Common.ResolvedReason"?:    string;
}

export interface IMicrosoftVstsCommonActivatedBy {
    displayName: string;
    url:         string;
    _links:      IMicrosoftVSTSCommonActivatedByLinks;
    id:          string;
    uniqueName:  string;
    imageUrl:    string;
    descriptor:  string;
}

export interface IMicrosoftVSTSCommonActivatedByLinks {
    avatar: IHTMLClass;
}

export interface IHTMLClass {
    href: string;
}

