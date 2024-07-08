import { appInsights } from "../appInsights";
import { getLocation } from "../helper/getLocation";

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

      async cacheIssue(description: string, photo: Blob, status: string = 'new', issueId: string = '') {
        const db = await this.dbPromise;
        const transaction = db.transaction('issues', 'readwrite');
        const store = transaction.objectStore('issues');
    
        // Convert the Blob to a File object and store the filename
        const photoFile = await this.blobToFile(photo, "resizedPhoto.jpg");
        const filename = photoFile.name; // Extract the filename from the File object
    
        const issueData = { description, photo: photoFile, filename, status, issueId };
        store.add(issueData);
    
        console.log('Issue cached:', issueData);
        
    }
      
      async submitIssue(description: string, photo: File) {
        const resizedPhoto = await this.resizeImageToVGA(photo);
      
        if (navigator.onLine) {
          console.log('Device is online, submitting issue...');
          // Implement API submission logic here
          // Assuming submitToApi returns a Promise with the issue ID on success
          try {
           
            const issueId = await this.submitToApi(description, resizedPhoto);
            console.log(`Issue submitted successfully, ID: ${issueId}`);
            await this.cacheIssue(description, resizedPhoto, 'uploaded', issueId);
          } catch (error) {
            console.error('Failed to submit issue:', error);
            // Optionally, cache the issue as 'waiting' or another status on failure
          }
        } else {
          console.log('Device is offline, caching issue...');
          await this.cacheIssue(description, resizedPhoto);
        }
      }
      
      // Placeholder for the actual API submission logic
      async submitToApi(description: string, photo: Blob): Promise<string> {
        // Simulate API call
        this.submitPosition('submittingPosition');

        this.submitPosition('submitedPosition');
       
        return 'simulated-issue-id'; // Return a simulated issue ID
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