import { appInsights } from "../appInsights";
import { getLocation } from "../helper/getLocation";

export type IssueType = {
    description: string;
    photo: File;
    filename: string;
    issueId: string;
    photoPosition: string;
    submitPosition: string;
  };


class IssueReportingService {
    dbPromise: Promise<IDBDatabase>;
    
  
    constructor() {
      this.dbPromise = new Promise((resolve, reject) => {
        const openRequest = indexedDB.open('IssueReportingDB', 1);
  
        openRequest.onupgradeneeded = () => {
          const db = openRequest.result;
          if (!db.objectStoreNames.contains('issues')) {
            db.createObjectStore('issues', { autoIncrement: true });
          }
        };
  
        openRequest.onsuccess = () => {
          resolve(openRequest.result);
        };
  
        openRequest.onerror = () => {
          reject(openRequest.error);
        };
      });
    }
  
 
  
    async fileToBlob(file: File): Promise<Blob> {
      return new Blob([file], { type: file.type });
    }

     blobToFile(blob: Blob, filename: string): File {
        // Create a new File object from the blob
        const file = new File([blob], filename, {
          type: blob.type,
          lastModified: new Date().getTime(), // Optionally, you can use blob's last modified time if available
        });
      
        return file;
      }

      async cacheIssue(description: string, photo: Blob, status: string = 'new', issueId: string = '',photoPosition: string, submitPosition: string) {
        const db = await this.dbPromise;
        const transaction = db.transaction('issues', 'readwrite');
        const store = transaction.objectStore('issues');
    
        // Convert the Blob to a File object and store the filename
        const photoFile = await this.blobToFile(photo, "resizedPhoto.jpg");
        const filename = photoFile.name; // Extract the filename from the File object
    
        const issueData = { description, photo: photoFile, filename, status, issueId , 
          photoPosition: JSON.stringify(photoPosition), 
          submitPosition: JSON.stringify(submitPosition)};
        store.add(issueData);
    
        console.log('Issue cached:', issueData);
        
    }

    async getIssues(): Promise<IssueType[]>{
        const db = await this.dbPromise;
        const transaction = db.transaction('issues', 'readonly');
        const store = transaction.objectStore('issues');
        const issues: IssueType[] = [];
    
        return new Promise((resolve, reject) => {
          store.openCursor().onsuccess = (event) => {
            const cursor = (event.target as IDBRequest).result;
            if (cursor) {
              issues.push(cursor.value);
              cursor.continue();
            } else {
              resolve(issues);
            }
          };
        });
      }
    
      async getUnsyncedIssues(): Promise<IssueType[]>{
        const db = await this.dbPromise;
        const transaction = db.transaction('issues', 'readonly');
        const store = transaction.objectStore('issues');
        const issues: IssueType[] = [];
        return new Promise((resolve, reject) => {
          store.openCursor().onsuccess = (event) => {
            const cursor = (event.target as IDBRequest).result;
            if (cursor) {
              if(cursor.value.issueId === ''){
              issues.push(cursor.value);
              }
              cursor.continue();
            } else {
              resolve(issues);
            }
          };
        });
      }
      
      async submitIssue(description: string, photo: File, photoPosition: string, submitPosition: string) {
        const resizedPhoto = await this.resizeImageToVGA(photo);
      
        await this.cacheIssue(description, resizedPhoto, 'uploaded', '',photoPosition,submitPosition);
      
      }

      async submitCachedIssues() {
        const issues = await this.getUnsyncedIssues();
        let haserror=false;
        for (const issue of issues) {
          try {
            await this.submitToApi(issue.description, issue.photo,issue.photoPosition,issue.submitPosition);
            
          } catch (error) {
            haserror=true;
            console.error('Error submitting issue:', error);
          }
        }
        if(!haserror){
          this.cleanCache();
        }
      }

      async cleanCache() {
        const db = await this.dbPromise;
        const transaction = db.transaction('issues', 'readwrite');
        const store = transaction.objectStore('issues');
        store.clear();
      }
      
      // Placeholder for the actual API submission logic
      async submitToApi(description: string, photo: Blob,photoPosition:string,submitPosition:string): Promise<string> {
       
       return new Promise((resolve,reject) => {
        this.submitPosition('submitedPosition');
        reject('storedata');
        //resolve( 'simulated-issue-id');
        });

      }

      async submitPosition(areaName:string) {
        const pos2= await getLocation();
        appInsights.trackEvent({   
          name: areaName,
          properties: {
            latitude :pos2.latitude,
            longitude :pos2.longitude,
            timestamp: new Date().toISOString(),
          },
        });
      }
    async resizeImageToVGA(file: File): Promise<Blob> {
        return new Promise((resolve, reject) => {
          const img = new Image();
          img.src = URL.createObjectURL(file);
          img.onload = () => {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            // Calculate the new dimensions while maintaining the aspect ratio
            const maxW = 640;
            const maxH = 480;
            let width = img.width;
            let height = img.height;
      
            if (width > height) {
              if (width > maxW) {
                height *= maxW / width;
                width = maxW;
              }
            } else {
              if (height > maxH) {
                width *= maxH / height;
                height = maxH;
              }
            }
      
            canvas.width = width;
            canvas.height = height;
            
            // Draw the resized image
            ctx?.drawImage(img, 0, 0, width, height);
            
            // Convert canvas to Blob
            canvas.toBlob((blob)=> {
                if(blob === null) {
                    reject('Error converting canvas to blob');
                    return;
                }
                resolve(blob)

            }, file.type);
          };
          img.onerror = reject;
        });
      }
  }
  
  export const issueReportingService = new IssueReportingService();