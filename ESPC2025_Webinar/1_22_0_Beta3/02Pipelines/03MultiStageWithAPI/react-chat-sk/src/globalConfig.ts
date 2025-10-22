export const AZURE_FUNCTION_APP_ID = 
  process.env.ENTRA_ResourceAppId || 
  "c032171c-4d2c-4b30-9572-f649390a4c8c";

export const AZURE_FUNCTION_URL = 
  process.env.ENTRA_ResourceReplyUrl || 
  "http://localhost:7071";